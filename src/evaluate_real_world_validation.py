from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd

from phishing_url_ml.feature_engineering import build_feature_frame
from phishing_url_ml.inference import (
    build_inference_row,
    load_official_model_bundle,
    normalized_score_for_model,
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
        "model": model,
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
            "model": official.model,
        }

    if args.url_run_summary:
        bundles["url"] = load_bundle_from_run_summary(resolve_repo_path(args.url_run_summary))
    else:
        official = load_official_model_bundle("url")
        bundles["url"] = {
            "dataset_kind": "url",
            "variant_name": official.variant_name,
            "model_name": official.model_name,
            "model": official.model,
        }
    return bundles


def predict_with_bundle(value: str, dataset_kind: str, bundle: dict[str, object]) -> dict[str, object]:
    inference_df, parsed_row = build_inference_row(value, dataset_kind)
    feature_frame = build_feature_frame(inference_df, dataset_kind)
    model = bundle["model"]
    predicted_label = int(model.predict(feature_frame)[0])
    score, _ = normalized_score_for_model(model, feature_frame)
    risk_level = risk_level_for_score(score)
    feature_values = feature_frame.iloc[0].to_dict()
    return {
        "predicted_label": predicted_label,
        "predicted_class": "phishing" if predicted_label == 1 else "benign",
        "score": round(float(score), 6),
        "risk_level": risk_level,
        "model_name": bundle["model_name"],
        "variant_name": bundle["variant_name"],
        "normalized_value": parsed_row["sample_text"],
        "signals": summarize_signals(dataset_kind, parsed_row, feature_values),
        "recommendation": recommendation_for_prediction(predicted_label, risk_level),
    }


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

        rows.append(
            {
                **row,
                "expected_label_int": expected_label_int,
                "predicted_label": predicted_label,
                "predicted_class": predicted_class,
                "score": result.get("score"),
                "risk_level": result.get("risk_level"),
                "model_name": result.get("model_name"),
                "variant_name": result.get("variant_name"),
                "normalized_value": result.get("normalized_value"),
                "signals": " | ".join(result.get("signals", [])),
                "recommendation": result.get("recommendation"),
                "match_expected": predicted_label == expected_label_int,
                "is_false_positive": expected_label_int == 0 and predicted_label == 1,
                "is_false_negative": expected_label_int == 1 and predicted_label == 0,
                "error": error_text,
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
    top_issues: pd.DataFrame,
) -> None:
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
            f"score=`{row['score']:.6f}` | risk=`{row['risk_level']}` | priority=`{row['priority']}`"
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
            f"score=`{row['score']:.6f}` | risk=`{row['risk_level']}` | priority=`{row['priority']}`"
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
            f"pred=`{row['predicted_class']}` | score=`{row['score']:.6f}` | risk=`{row['risk_level']}`"
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
            "## 4. Nhan xet nhanh",
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
    summary_json_path = output_dir / f"{stem}_summary_{timestamp}.json"

    details_df.to_csv(details_path, index=False, encoding="utf-8")
    by_dataset_df = group_summary(details_df, ["dataset_kind"])
    by_priority_df = group_summary(details_df, ["priority"])
    by_category_df = group_summary(details_df, ["category"])
    by_dataset_df.to_csv(by_dataset_path, index=False, encoding="utf-8")
    by_priority_df.to_csv(by_priority_path, index=False, encoding="utf-8")
    by_category_df.to_csv(by_category_path, index=False, encoding="utf-8")

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
        "total_cases": int(len(details_df)),
        "matched_cases": matched_cases,
        "match_rate": float(matched_cases / len(details_df)) if len(details_df) else 0.0,
        "false_positives": false_positive_count,
        "false_positive_rate": float(false_positive_count / len(details_df)) if len(details_df) else 0.0,
        "false_negatives": false_negative_count,
        "false_negative_rate": float(false_negative_count / len(details_df)) if len(details_df) else 0.0,
        "errors": error_count,
        "artifacts": {
            "by_dataset_kind": str(by_dataset_path),
            "by_priority": str(by_priority_path),
            "by_category": str(by_category_path),
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
    write_markdown_report(
        report_path=report_path,
        seed_path=input_path,
        details_path=details_path,
        overall_summary=overall_summary,
        by_dataset_path=by_dataset_path,
        by_priority_path=by_priority_path,
        by_category_path=by_category_path,
        top_issues=top_issues,
    )

    print(f"Wrote detailed results to {details_path}")
    print(f"Wrote dataset summary to {by_dataset_path}")
    print(f"Wrote priority summary to {by_priority_path}")
    print(f"Wrote category summary to {by_category_path}")
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
