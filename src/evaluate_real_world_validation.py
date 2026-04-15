from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd

from phishing_url_ml.feature_engineering import align_feature_frame, build_feature_frame
from phishing_url_ml.inference import (
    build_inference_row,
    expected_feature_columns,
    load_official_model_bundle,
    normalized_score_for_model,
    predict_value,
    recommendation_for_prediction,
    risk_level_for_score,
    summarize_signals,
)
from phishing_url_ml.settings import BASE_DIR
from phishing_url_ml.utils import require_columns


REQUIRED_COLUMNS = [
    "sample_id",
    "category",
    "dataset_kind",
    "input_value",
    "expected_label",
    "priority",
]

TOKEN_PATTERN_SPECS = (
    ("dang_nhap", ("dang-nhap", "dang nhap")),
    ("returnurl", ("returnurl", "return url")),
    ("login", ("login", "logon", "sign in", "signin", "signon", "sso")),
    ("portal", ("portal",)),
    ("mail", ("mail",)),
    ("account", ("account",)),
    ("auth", ("auth",)),
    ("verify", ("verify", "verification")),
    ("request", ("request",)),
    ("pdf", (".pdf",)),
    ("otp", ("otp",)),
    ("digibank", ("digibank",)),
    ("wallet", ("wallet",)),
    ("crypto", ("crypto",)),
    ("bank", ("bank",)),
    ("pay", ("pay", "payment", "checkout")),
    ("secure", ("secure",)),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run official phishing models on a real-world validation seed file and "
            "export detailed predictions plus false-positive summaries."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/validation/vn_real_world_benign_seed.csv"),
        help="CSV file containing real-world validation samples.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/validation/results"),
        help="Directory used to store evaluation outputs.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("docs/VN Real-World Benign Validation Results.md"),
        help="Markdown summary report path.",
    )
    parser.add_argument(
        "--domain-run-summary",
        type=Path,
        help="Optional run_summary.json path for the domain model. Defaults to the official model.",
    )
    parser.add_argument(
        "--url-run-summary",
        type=Path,
        help="Optional run_summary.json path for the URL model. Defaults to the official model.",
    )
    return parser.parse_args()


def resolve_repo_path(path_value: Path) -> Path:
    return path_value if path_value.is_absolute() else BASE_DIR / path_value


def expected_label_to_int(value: str) -> int:
    normalized = value.strip().lower()
    if normalized == "benign":
        return 0
    if normalized == "phishing":
        return 1
    raise ValueError(f"Unsupported expected_label: {value}")


def load_bundle_from_run_summary(run_summary_path: Path) -> dict[str, object]:
    payload = json.loads(run_summary_path.read_text(encoding="utf-8"))
    selected_model_path = resolve_repo_path(Path(payload["artifacts"]["selected_model_path"]))
    model = joblib.load(selected_model_path)
    return {
        "dataset_kind": payload["dataset_kind"],
        "variant_name": str(Path(run_summary_path).parent.name),
        "model_name": payload["best_model"],
        "feature_columns": payload.get("feature_columns", []),
        "model": model,
        "prediction_mode": "direct_model",
    }


def load_bundles(args: argparse.Namespace) -> dict[str, dict[str, object]]:
    bundles: dict[str, dict[str, object]] = {}
    if args.domain_run_summary:
        bundles["domain"] = load_bundle_from_run_summary(resolve_repo_path(args.domain_run_summary))
    else:
        official = load_official_model_bundle("domain")
        bundles["domain"] = {
            "dataset_kind": "domain",
            "variant_name": official.variant_name,
            "model_name": official.model_name,
            "feature_columns": official.run_summary.get("feature_columns", []),
            "model": official.model,
            "prediction_mode": "official_runtime",
        }

    if args.url_run_summary:
        bundles["url"] = load_bundle_from_run_summary(resolve_repo_path(args.url_run_summary))
    else:
        official = load_official_model_bundle("url")
        bundles["url"] = {
            "dataset_kind": "url",
            "variant_name": official.variant_name,
            "model_name": official.model_name,
            "feature_columns": official.run_summary.get("feature_columns", []),
            "model": official.model,
            "prediction_mode": "official_runtime",
        }
    return bundles


def predict_with_bundle(value: str, dataset_kind: str, bundle: dict[str, object]) -> dict[str, object]:
    if str(bundle.get("prediction_mode", "")) == "official_runtime":
        return predict_value(
            value=value,
            dataset_kind=dataset_kind,
            source="real_world_validation",
            persist=False,
        )

    inference_df, parsed_row = build_inference_row(value, dataset_kind)
    feature_frame = build_feature_frame(inference_df, dataset_kind)
    feature_frame = align_feature_frame(
        feature_frame,
        expected_feature_columns(bundle["model"], {"feature_columns": bundle.get("feature_columns", [])}),
    )
    model = bundle["model"]
    predicted_label = int(model.predict(feature_frame)[0])
    score, _ = normalized_score_for_model(model, feature_frame)
    risk_level = risk_level_for_score(score, dataset_kind)
    feature_values = feature_frame.iloc[0].to_dict()
    return {
        "predicted_label": predicted_label,
        "predicted_class": "phishing" if predicted_label == 1 else "benign",
        "score": round(float(score), 6),
        "score_source": "direct_model",
        "risk_level": risk_level,
        "model_name": bundle["model_name"],
        "variant_name": bundle["variant_name"],
        "normalized_value": parsed_row["sample_text"],
        "signals": summarize_signals(dataset_kind, parsed_row, feature_values),
        "recommendation": recommendation_for_prediction(predicted_label, risk_level),
        "decision_mode": "model",
        "override_reason": "",
        "override_match_value": "",
        "model_predicted_class_before_override": "",
        "model_score_before_override": None,
        "model_risk_level_before_override": "",
    }


def normalize_text_for_pattern_matching(value: object) -> str:
    lowered = str(value or "").strip().lower()
    return re.sub(r"[^a-z0-9.]+", " ", lowered)


def detect_token_patterns(value: object) -> list[str]:
    lowered = str(value or "").strip().lower()
    normalized = normalize_text_for_pattern_matching(value)
    matched: list[str] = []
    for pattern_name, keywords in TOKEN_PATTERN_SPECS:
        if any(keyword in lowered or keyword in normalized for keyword in keywords):
            matched.append(pattern_name)
    return matched


def evaluate_rows(seed_df: pd.DataFrame, bundles: dict[str, dict[str, object]]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in seed_df.to_dict(orient="records"):
        expected_label_int = expected_label_to_int(str(row["expected_label"]))
        try:
            dataset_kind = str(row["dataset_kind"])
            result = predict_with_bundle(
                value=str(row["input_value"]),
                dataset_kind=dataset_kind,
                bundle=bundles[dataset_kind],
            )
            predicted_label = int(result["predicted_label"])
            predicted_class = str(result["predicted_class"])
            error_text = ""
        except Exception as exc:  # pragma: no cover - runtime safeguard
            result = {}
            predicted_label = -1
            predicted_class = "error"
            error_text = str(exc)
        normalized_value = str(result.get("normalized_value", "") or "")
        matched_token_patterns = detect_token_patterns(
            " ".join(
                part for part in [str(row.get("input_value", "")).strip(), normalized_value] if part
            )
        )
        primary_token_pattern = matched_token_patterns[0] if matched_token_patterns else "_none"
        is_false_positive = expected_label_int == 0 and predicted_label == 1
        is_false_negative = expected_label_int == 1 and predicted_label == 0
        if error_text:
            error_kind = "runtime_error"
        elif is_false_positive:
            error_kind = "false_positive"
        elif is_false_negative:
            error_kind = "false_negative"
        else:
            error_kind = "matched"

        rows.append(
            {
                **row,
                "expected_label_int": expected_label_int,
                "predicted_label": predicted_label,
                "predicted_class": predicted_class,
                "score": result.get("score"),
                "score_source": result.get("score_source"),
                "risk_level": result.get("risk_level"),
                "model_name": result.get("model_name"),
                "variant_name": result.get("variant_name"),
                "normalized_value": normalized_value,
                "signals": " | ".join(result.get("signals", [])),
                "recommendation": result.get("recommendation"),
                "match_expected": predicted_label == expected_label_int,
                "is_false_positive": is_false_positive,
                "is_false_negative": is_false_negative,
                "error_kind": error_kind,
                "error": error_text,
                "matched_token_patterns": " | ".join(matched_token_patterns),
                "primary_token_pattern": primary_token_pattern,
                "decision_mode": result.get("decision_mode", "model"),
                "override_reason": result.get("override_reason", ""),
                "override_match_value": result.get("override_match_value", ""),
                "model_predicted_class_before_override": result.get(
                    "model_predicted_class_before_override", ""
                ),
                "model_score_before_override": result.get("model_score_before_override"),
                "model_risk_level_before_override": result.get("model_risk_level_before_override", ""),
            }
        )
    return pd.DataFrame(rows)


def group_summary(df: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    summary = (
        df.groupby(group_columns, dropna=False)
        .agg(
            total_cases=("sample_id", "count"),
            matched_cases=("match_expected", "sum"),
            predicted_benign=("predicted_label", lambda values: int((pd.Series(values) == 0).sum())),
            predicted_phishing=("predicted_label", lambda values: int((pd.Series(values) == 1).sum())),
            false_positives=("is_false_positive", "sum"),
            false_negatives=("is_false_negative", "sum"),
            errors=("error", lambda values: int(pd.Series(values).astype(str).ne("").sum())),
            average_score=("score", "mean"),
        )
        .reset_index()
    )
    summary["false_positive_rate"] = summary["false_positives"] / summary["total_cases"]
    summary["false_negative_rate"] = summary["false_negatives"] / summary["total_cases"]
    summary["match_rate"] = summary["matched_cases"] / summary["total_cases"]
    return summary


def group_error_summary(df: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    error_df = df.loc[~df["match_expected"]].copy()
    if error_df.empty:
        return pd.DataFrame(
            columns=group_columns
            + [
                "total_errors",
                "false_positives",
                "false_negatives",
                "runtime_errors",
                "override_after_model",
                "average_score",
                "error_share",
            ]
        )

    summary = (
        error_df.groupby(group_columns, dropna=False)
        .agg(
            total_errors=("sample_id", "count"),
            false_positives=("is_false_positive", "sum"),
            false_negatives=("is_false_negative", "sum"),
            runtime_errors=("error", lambda values: int(pd.Series(values).astype(str).ne("").sum())),
            override_after_model=(
                "decision_mode",
                lambda values: int(
                    pd.Series(values).astype(str).eq("model_plus_curated_benign_override").sum()
                ),
            ),
            average_score=("score", "mean"),
        )
        .reset_index()
    )
    summary["error_share"] = summary["total_errors"] / len(error_df)
    return summary.sort_values("total_errors", ascending=False).reset_index(drop=True)


def detect_evaluation_mode(df: pd.DataFrame) -> str:
    expected_values = set(df["expected_label"].astype(str).str.strip().str.lower().unique())
    if expected_values == {"benign"}:
        return "benign_only"
    if expected_values == {"phishing"}:
        return "phishing_only"
    return "mixed"


def write_markdown_report(
    report_path: Path,
    seed_path: Path,
    details_path: Path,
    overall_summary: dict[str, object],
    by_dataset_path: Path,
    by_priority_path: Path,
    by_category_path: Path,
    error_by_category_path: Path,
    error_by_token_pattern_path: Path,
    error_by_category_pattern_path: Path,
    top_issues: pd.DataFrame,
    top_error_patterns: pd.DataFrame,
) -> None:
    def formatted_score(value: object) -> str:
        if value is None or pd.isna(value):
            return "n/a"
        return f"{float(value):.6f}"

    evaluation_mode = str(overall_summary["evaluation_mode"])
    if evaluation_mode == "benign_only":
        title = "VN Real-World Benign Validation Results"
        metric_lines = [
            f"- So false positive: `{overall_summary['false_positives']}`",
            f"- Ty le false positive: `{overall_summary['false_positive_rate']:.2%}`",
        ]
        issue_section_title = "## 3. False Positive noi bat"
        empty_issue_line = "- Khong co false positive nao trong lan chay nay."
        issue_formatter = (
            lambda row: f"- `{row['sample_id']}` | `{row['dataset_kind']}` | `{row['input_value']}` | "
            f"score=`{formatted_score(row['score'])}` | risk=`{row['risk_level']}` | priority=`{row['priority']}`"
        )
        quick_notes = [
            "- Bo nay chi gom case `benign`, nen chi so can nhin truoc mat la `false positive`.",
            "- Neu false positive tap trung vao `university_portal` hoac `banking`, can uu tien xem lai `Domain Model` va cac URL login/portal hop le.",
            "- Day la bo kiem tra thuc chien bo sung, khong thay the cho test set hoc may chinh.",
        ]
    elif evaluation_mode == "phishing_only":
        title = "VN Real-World Phishing Validation Results"
        metric_lines = [
            f"- So phishing duoc nhan dien dung: `{overall_summary['matched_cases']}`",
            f"- Ty le nhan dien dung: `{overall_summary['match_rate']:.2%}`",
            f"- So false negative: `{overall_summary['false_negatives']}`",
            f"- Ty le false negative: `{overall_summary['false_negative_rate']:.2%}`",
        ]
        issue_section_title = "## 3. False Negative noi bat"
        empty_issue_line = "- Khong co false negative nao trong lan chay nay."
        issue_formatter = (
            lambda row: f"- `{row['sample_id']}` | `{row['dataset_kind']}` | `{row['input_value']}` | "
            f"score=`{formatted_score(row['score'])}` | risk=`{row['risk_level']}` | priority=`{row['priority']}`"
        )
        quick_notes = [
            "- Bo nay chi gom case `phishing`, nen chi so can nhin truoc mat la `false negative` va `ty le nhan dien dung`.",
            "- Neu false negative tap trung vao mot nhom nhu `cloud_email_docs` hay `banking_payment`, can bo sung them mau phishing cung kieu vao bo danh gia va bo train.",
            "- Day la bo kiem tra thuc chien bo sung, khong thay the cho test set hoc may chinh.",
        ]
    else:
        title = "VN Real-World Validation Results"
        metric_lines = [
            f"- So false positive: `{overall_summary['false_positives']}`",
            f"- So false negative: `{overall_summary['false_negatives']}`",
            f"- Match rate: `{overall_summary['match_rate']:.2%}`",
        ]
        issue_section_title = "## 3. Case sai noi bat"
        empty_issue_line = "- Khong co case sai nao trong lan chay nay."
        issue_formatter = (
            lambda row: f"- `{row['sample_id']}` | `{row['dataset_kind']}` | `{row['input_value']}` | "
            f"pred=`{row['predicted_class']}` | score=`{formatted_score(row['score'])}` | risk=`{row['risk_level']}`"
        )
        quick_notes = [
            "- Bo nay gom ca `benign` va `phishing`, nen can doc dong thoi false positive, false negative va match rate.",
            "- Day la bo kiem tra thuc chien bo sung, khong thay the cho test set hoc may chinh.",
        ]

    lines = [
        f"# {title}",
        "",
        f"- Input seed: `{seed_path.relative_to(BASE_DIR)}`",
        f"- Detailed results: `{details_path.relative_to(BASE_DIR)}`",
        f"- Evaluated at: `{overall_summary['evaluated_at']}`",
        f"- Prediction modes: `{', '.join(overall_summary.get('prediction_modes', ['unknown']))}`",
        f"- Curated runtime overrides applied: `{int(overall_summary.get('override_after_model', 0))}`",
        "",
        "## 1. Tong quan",
        "",
        f"- Tong so case: `{overall_summary['total_cases']}`",
        f"- So case dung ky vong: `{overall_summary['matched_cases']}`",
        *metric_lines,
        f"- So case loi khi predict: `{overall_summary['errors']}`",
        "",
        "## 2. File tong hop",
        "",
        f"- Theo `dataset_kind`: `{by_dataset_path.relative_to(BASE_DIR)}`",
        f"- Theo `priority`: `{by_priority_path.relative_to(BASE_DIR)}`",
        f"- Theo `category`: `{by_category_path.relative_to(BASE_DIR)}`",
        f"- Loi theo `category`: `{error_by_category_path.relative_to(BASE_DIR)}`",
        f"- Loi theo `token pattern`: `{error_by_token_pattern_path.relative_to(BASE_DIR)}`",
        f"- Loi theo `category + token pattern`: `{error_by_category_pattern_path.relative_to(BASE_DIR)}`",
        "",
        issue_section_title,
        "",
    ]

    if top_issues.empty:
        lines.append(empty_issue_line)
    else:
        for row in top_issues.to_dict(orient="records"):
            lines.append(issue_formatter(row))

    lines.extend(
        [
            "",
            "## 4. Token pattern noi bat",
            "",
        ]
    )

    if top_error_patterns.empty:
        lines.append("- Khong co token pattern loi nao trong lan chay nay.")
    else:
        for row in top_error_patterns.to_dict(orient="records"):
            token_pattern = str(row.get("primary_token_pattern", "_none"))
            token_pattern = "none" if token_pattern == "_none" else token_pattern
            lines.append(
                f"- `{token_pattern}` | total_errors=`{int(row['total_errors'])}` | "
                f"fp=`{int(row['false_positives'])}` | fn=`{int(row['false_negatives'])}` | "
                f"share=`{float(row['error_share']):.2%}`"
            )

    lines.extend(
        [
            "",
            "## 5. Nhan xet nhanh",
            "",
            *quick_notes,
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_path = resolve_repo_path(args.input)
    output_dir = resolve_repo_path(args.output_dir)
    report_path = resolve_repo_path(args.report)
    output_dir.mkdir(parents=True, exist_ok=True)

    seed_df = pd.read_csv(input_path)
    require_columns(seed_df, REQUIRED_COLUMNS, dataset_name="real-world validation seed")
    bundles = load_bundles(args)
    details_df = evaluate_rows(seed_df, bundles)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = input_path.stem
    details_path = output_dir / f"{stem}_detailed_{timestamp}.csv"
    by_dataset_path = output_dir / f"{stem}_by_dataset_kind_{timestamp}.csv"
    by_priority_path = output_dir / f"{stem}_by_priority_{timestamp}.csv"
    by_category_path = output_dir / f"{stem}_by_category_{timestamp}.csv"
    error_by_category_path = output_dir / f"{stem}_errors_by_category_{timestamp}.csv"
    error_by_token_pattern_path = output_dir / f"{stem}_errors_by_token_pattern_{timestamp}.csv"
    error_by_category_pattern_path = output_dir / f"{stem}_errors_by_category_token_pattern_{timestamp}.csv"
    summary_json_path = output_dir / f"{stem}_summary_{timestamp}.json"

    details_df.to_csv(details_path, index=False, encoding="utf-8")
    by_dataset_df = group_summary(details_df, ["dataset_kind"])
    by_priority_df = group_summary(details_df, ["priority"])
    by_category_df = group_summary(details_df, ["category"])
    error_by_category_df = group_error_summary(details_df, ["category"])
    error_by_token_pattern_df = group_error_summary(details_df, ["primary_token_pattern"])
    error_by_category_pattern_df = group_error_summary(details_df, ["category", "primary_token_pattern"])
    by_dataset_df.to_csv(by_dataset_path, index=False, encoding="utf-8")
    by_priority_df.to_csv(by_priority_path, index=False, encoding="utf-8")
    by_category_df.to_csv(by_category_path, index=False, encoding="utf-8")
    error_by_category_df.to_csv(error_by_category_path, index=False, encoding="utf-8")
    error_by_token_pattern_df.to_csv(error_by_token_pattern_path, index=False, encoding="utf-8")
    error_by_category_pattern_df.to_csv(error_by_category_pattern_path, index=False, encoding="utf-8")

    false_positive_count = int(details_df["is_false_positive"].sum())
    false_negative_count = int(details_df["is_false_negative"].sum())
    matched_cases = int(details_df["match_expected"].sum())
    error_count = int(details_df["error"].astype(str).ne("").sum())
    evaluation_mode = detect_evaluation_mode(details_df)
    overall_summary = {
        "evaluated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "input_path": str(input_path),
        "details_path": str(details_path),
        "evaluation_mode": evaluation_mode,
        "prediction_modes": sorted({str(bundle.get("prediction_mode", "direct_model")) for bundle in bundles.values()}),
        "total_cases": int(len(details_df)),
        "matched_cases": matched_cases,
        "match_rate": float(matched_cases / len(details_df)) if len(details_df) else 0.0,
        "false_positives": false_positive_count,
        "false_positive_rate": float(false_positive_count / len(details_df)) if len(details_df) else 0.0,
        "false_negatives": false_negative_count,
        "false_negative_rate": float(false_negative_count / len(details_df)) if len(details_df) else 0.0,
        "errors": error_count,
        "override_after_model": int(
            details_df["decision_mode"].astype(str).eq("model_plus_curated_benign_override").sum()
        ),
        "artifacts": {
            "by_dataset_kind": str(by_dataset_path),
            "by_priority": str(by_priority_path),
            "by_category": str(by_category_path),
            "errors_by_category": str(error_by_category_path),
            "errors_by_token_pattern": str(error_by_token_pattern_path),
            "errors_by_category_token_pattern": str(error_by_category_pattern_path),
        },
    }
    summary_json_path.write_text(json.dumps(overall_summary, indent=2), encoding="utf-8")

    if evaluation_mode == "benign_only":
        top_issues = (
            details_df.loc[details_df["is_false_positive"]]
            .sort_values(["priority", "score"], ascending=[True, False], na_position="last")
            .head(10)
        )
    elif evaluation_mode == "phishing_only":
        top_issues = (
            details_df.loc[details_df["is_false_negative"]]
            .sort_values(["priority", "score"], ascending=[True, True], na_position="last")
            .head(10)
        )
    else:
        top_issues = (
            details_df.loc[~details_df["match_expected"]]
            .sort_values(["priority", "score"], ascending=[True, False], na_position="last")
            .head(10)
        )
    top_error_patterns = error_by_token_pattern_df.head(10)
    write_markdown_report(
        report_path=report_path,
        seed_path=input_path,
        details_path=details_path,
        overall_summary=overall_summary,
        by_dataset_path=by_dataset_path,
        by_priority_path=by_priority_path,
        by_category_path=by_category_path,
        error_by_category_path=error_by_category_path,
        error_by_token_pattern_path=error_by_token_pattern_path,
        error_by_category_pattern_path=error_by_category_pattern_path,
        top_issues=top_issues,
        top_error_patterns=top_error_patterns,
    )

    print(f"Wrote detailed results to {details_path}")
    print(f"Wrote dataset summary to {by_dataset_path}")
    print(f"Wrote priority summary to {by_priority_path}")
    print(f"Wrote category summary to {by_category_path}")
    print(f"Wrote error-by-category summary to {error_by_category_path}")
    print(f"Wrote error-by-token-pattern summary to {error_by_token_pattern_path}")
    print(f"Wrote error-by-category-token summary to {error_by_category_pattern_path}")
    print(f"Wrote JSON summary to {summary_json_path}")
    print(f"Wrote markdown report to {report_path}")
    if evaluation_mode == "benign_only":
        print(
            f"Overall false positives: {false_positive_count}/{len(details_df)} "
            f"({overall_summary['false_positive_rate']:.2%})"
        )
    elif evaluation_mode == "phishing_only":
        print(
            f"Overall false negatives: {false_negative_count}/{len(details_df)} "
            f"({overall_summary['false_negative_rate']:.2%})"
        )
    else:
        print(f"Overall match rate: {overall_summary['match_rate']:.2%}")


if __name__ == "__main__":
    main()
