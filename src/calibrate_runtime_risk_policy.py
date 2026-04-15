from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

from phishing_url_ml.settings import BASE_DIR, RUNTIME_RISK_POLICY_PATH


DEFAULT_THRESHOLDS = {
    "domain": {
        "high": 0.95,
        "medium": 0.90,
        "low": 0.55,
    },
    "url": {
        "high": 0.98,
        "medium": 0.75,
        "low": 0.45,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Write the runtime risk policy used by IDS inference and summarize how the chosen "
            "thresholds behave on the latest real-world expanded validation results."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        help=(
            "Optional detailed expanded validation CSV. Defaults to the latest official file in "
            "data/validation/results/ matching vn_real_world_validation_seed_expanded_detailed_*.csv."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=RUNTIME_RISK_POLICY_PATH,
        help="JSON output path for the runtime risk policy.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("docs/Runtime Risk Policy.md"),
        help="Markdown report path.",
    )
    return parser.parse_args()


def resolve_repo_path(path_value: Path) -> Path:
    return path_value if path_value.is_absolute() else BASE_DIR / path_value


def latest_official_detailed_csv() -> Path:
    results_dir = BASE_DIR / "data" / "validation" / "results"
    candidates = sorted(
        results_dir.glob("vn_real_world_validation_seed_expanded_detailed_*.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(
            "No official expanded detailed validation CSV found in data/validation/results/."
        )
    return candidates[0]


def risk_level_for_score(score: float, thresholds: dict[str, float]) -> str:
    if score >= thresholds["high"]:
        return "high"
    if score >= thresholds["medium"]:
        return "medium"
    if score >= thresholds["low"]:
        return "low"
    return "minimal"


def score_summary(frame: pd.DataFrame) -> dict[str, float] | None:
    if frame.empty:
        return None
    scores = frame["score"].astype(float)
    return {
        "min": round(float(scores.min()), 6),
        "p25": round(float(scores.quantile(0.25)), 6),
        "median": round(float(scores.median()), 6),
        "p75": round(float(scores.quantile(0.75)), 6),
        "max": round(float(scores.max()), 6),
    }


def summarize_dataset_kind(df: pd.DataFrame, dataset_kind: str, thresholds: dict[str, float]) -> dict[str, object]:
    subset = df.loc[df["dataset_kind"].astype(str) == dataset_kind].copy()
    subset["calibrated_risk_level"] = subset["score"].astype(float).apply(
        lambda value: risk_level_for_score(value, thresholds)
    )

    risk_order = ["minimal", "low", "medium", "high"]
    risk_counts = Counter(subset["calibrated_risk_level"].astype(str))
    risk_counts_expected_benign = Counter(
        subset.loc[subset["expected_label_int"].astype(int) == 0, "calibrated_risk_level"].astype(str)
    )
    risk_counts_expected_phishing = Counter(
        subset.loc[subset["expected_label_int"].astype(int) == 1, "calibrated_risk_level"].astype(str)
    )

    return {
        "rows": int(len(subset)),
        "thresholds": thresholds,
        "score_summary_all": score_summary(subset),
        "score_summary_expected_benign": score_summary(
            subset.loc[subset["expected_label_int"].astype(int) == 0]
        ),
        "score_summary_expected_phishing": score_summary(
            subset.loc[subset["expected_label_int"].astype(int) == 1]
        ),
        "score_summary_false_positive": score_summary(subset.loc[subset["is_false_positive"] == True]),
        "score_summary_true_positive": score_summary(
            subset.loc[
                (subset["expected_label_int"].astype(int) == 1)
                & (subset["predicted_label"].astype(int) == 1)
            ]
        ),
        "risk_counts": {level: int(risk_counts.get(level, 0)) for level in risk_order},
        "risk_counts_expected_benign": {
            level: int(risk_counts_expected_benign.get(level, 0)) for level in risk_order
        },
        "risk_counts_expected_phishing": {
            level: int(risk_counts_expected_phishing.get(level, 0)) for level in risk_order
        },
    }


def write_markdown(path: Path, source_csv: Path, policy: dict[str, object], summaries: dict[str, object]) -> None:
    lines = [
        "# Runtime Risk Policy",
        "",
        f"- Source detailed CSV: `{source_csv.relative_to(BASE_DIR)}`",
        f"- Generated at: `{policy['generated_at']}`",
        f"- Policy version: `{policy['version']}`",
        "",
        "## 1. Thresholds",
        "",
        f"- `Domain`: low >= `{policy['dataset_kind_overrides']['domain']['low']:.2f}`, "
        f"medium >= `{policy['dataset_kind_overrides']['domain']['medium']:.2f}`, "
        f"high >= `{policy['dataset_kind_overrides']['domain']['high']:.2f}`",
        f"- `URL`: low >= `{policy['dataset_kind_overrides']['url']['low']:.2f}`, "
        f"medium >= `{policy['dataset_kind_overrides']['url']['medium']:.2f}`, "
        f"high >= `{policy['dataset_kind_overrides']['url']['high']:.2f}`",
        "",
        "## 2. Summary",
        "",
    ]

    for dataset_kind in ["domain", "url"]:
        summary = summaries[dataset_kind]
        lines.extend(
            [
                f"### 2.{1 if dataset_kind == 'domain' else 2}. `{dataset_kind}`",
                "",
                f"- Rows: `{summary['rows']}`",
                f"- Risk counts: `{summary['risk_counts']}`",
                f"- Expected benign by risk: `{summary['risk_counts_expected_benign']}`",
                f"- Expected phishing by risk: `{summary['risk_counts_expected_phishing']}`",
                f"- Score summary all: `{summary['score_summary_all']}`",
                f"- Score summary false positive: `{summary['score_summary_false_positive']}`",
                f"- Score summary true positive: `{summary['score_summary_true_positive']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## 3. Notes",
            "",
            "- Muc tieu cua policy nay la bien `risk_level` thanh tin hieu van hanh hop ly hon cho IDS, khong thay doi nhan `phishing/benign` cua model.",
            "- `URL high` duoc day len cao hon de giu nhom true phishing manh trong `expanded` o muc canh bao cao, trong khi mot so benign score sat nguong se ha xuong `medium` hoac `low`.",
            "- `Domain high` duoc dat cao hon de tranh nang canh bao qua som cho cac hostname benign bi model score cao truoc khi co them runtime triage.",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    source_csv = resolve_repo_path(args.input) if args.input else latest_official_detailed_csv()
    output_path = resolve_repo_path(args.output)
    report_path = resolve_repo_path(args.report)

    df = pd.read_csv(source_csv)
    required = {"dataset_kind", "expected_label_int", "predicted_label", "score", "is_false_positive"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Detailed CSV is missing required columns: {', '.join(missing)}")

    policy = {
        "version": "2026-04-15_phase36_calibrated",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_detailed_csv": str(source_csv.relative_to(BASE_DIR)),
        "default": {
            "high": 0.90,
            "medium": 0.65,
            "low": 0.35,
        },
        "dataset_kind_overrides": DEFAULT_THRESHOLDS,
        "notes": [
            "Risk policy changes IDS alert severity only; it does not change the model's phishing/benign prediction.",
            "Phase 36 calibrates dataset-specific thresholds from the latest official expanded validation behavior.",
        ],
    }

    summaries = {
        dataset_kind: summarize_dataset_kind(df, dataset_kind, policy["dataset_kind_overrides"][dataset_kind])
        for dataset_kind in ["domain", "url"]
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(policy, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(report_path, source_csv, policy, summaries)

    print(output_path)
    print(report_path)


if __name__ == "__main__":
    main()
