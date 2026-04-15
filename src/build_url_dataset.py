from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from phishing_url_ml.settings import PROCESSED_DIR, RAW_DIR
from phishing_url_ml.utils import build_parsed_record, log, require_columns, write_json


OUTPUT_COLUMNS = [
    "sample_text",
    "label",
    "source",
    "collected_at",
    "hostname",
    "registered_domain",
    "path",
    "query",
    "fragment",
    "scheme",
    "is_ip_host",
    "canonical_hostname",
    "canonical_url",
]

URL_BENIGN_ADDON_DIR = RAW_DIR / "vn_benign_url_addon"
URL_PHISHING_ADDON_DIR = RAW_DIR / "vn_phishing_url_addon"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the dataset for the URL model.")
    parser.add_argument(
        "--input",
        type=Path,
        default=PROCESSED_DIR / "clean_master_dataset.parquet",
        help="Path to the cleaned master dataset.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DIR / "url_model_dataset.parquet",
        help="Path to the output parquet dataset.",
    )
    return parser.parse_args()


def resolve_addon_date(row: dict[str, object], fallback_date: str = "2026-04-15") -> str:
    value = str(row.get("collected_at", "")).strip()
    if value:
        return value
    return fallback_date


def load_url_addons(
    addon_dir: Path,
    label: int,
    default_source: str,
) -> pd.DataFrame:
    if not addon_dir.exists():
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    rows: list[dict[str, object]] = []
    csv_paths = sorted(addon_dir.glob("*.csv"))
    for csv_path in csv_paths:
        addon_df = pd.read_csv(csv_path)
        if "input_value" not in addon_df.columns:
            log(f"Skipping URL addon file without input_value column: {csv_path}")
            continue

        for row in addon_df.to_dict(orient="records"):
            parsed = build_parsed_record(row.get("input_value", ""), "url")
            if not parsed["parse_ok"]:
                continue
            rows.append(
                {
                    "sample_text": parsed["canonical_url"] or parsed["canonical_hostname"],
                    "label": label,
                    "source": str(row.get("source", "")).strip() or default_source,
                    "collected_at": resolve_addon_date(row),
                    "hostname": parsed["hostname"],
                    "registered_domain": parsed["registered_domain"],
                    "path": parsed["path"],
                    "query": parsed["query"],
                    "fragment": parsed["fragment"],
                    "scheme": parsed["scheme"],
                    "is_ip_host": parsed["is_ip_host"],
                    "canonical_hostname": parsed["canonical_hostname"],
                    "canonical_url": parsed["canonical_url"],
                }
            )

    if not rows:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    addon_frame = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    log(
        "Loaded curated URL addon rows: "
        f"{len(addon_frame):,} from {len(csv_paths)} file(s) in {addon_dir}"
    )
    return addon_frame


def load_url_benign_addons() -> pd.DataFrame:
    return load_url_addons(
        addon_dir=URL_BENIGN_ADDON_DIR,
        label=0,
        default_source="vn_benign_url_addon",
    )


def load_url_phishing_addons() -> pd.DataFrame:
    return load_url_addons(
        addon_dir=URL_PHISHING_ADDON_DIR,
        label=1,
        default_source="vn_phishing_url_addon",
    )


def main() -> None:
    args = parse_args()
    df = pd.read_parquet(args.input)
    require_columns(
        df,
        ["label", "source", "collected_at", "canonical_url", "hostname", "path", "query"],
        dataset_name="clean master dataset",
    )

    working = df.loc[(df["record_type"] == "url") & df["canonical_url"].ne("")].copy()
    working["sample_text"] = working["canonical_url"]
    addon_frames = [working[OUTPUT_COLUMNS].copy()]
    benign_addon_df = load_url_benign_addons()
    if not benign_addon_df.empty:
        addon_frames.append(benign_addon_df)
    phishing_addon_df = load_url_phishing_addons()
    if not phishing_addon_df.empty:
        addon_frames.append(phishing_addon_df)
    if len(addon_frames) > 1:
        working = pd.concat(addon_frames, ignore_index=True)
    else:
        working = addon_frames[0]
    working = working.sort_values(["collected_at", "label"], ascending=[True, False]).reset_index(drop=True)
    working = working.drop_duplicates(subset=["sample_text"], keep="first")

    positive_urls = set(working.loc[working["label"] == 1, "sample_text"])
    overlap_mask = (working["label"] == 0) & working["sample_text"].isin(positive_urls)
    if overlap_mask.any():
        working = working.loc[~overlap_mask].copy()

    url_dataset = working[OUTPUT_COLUMNS].copy()
    url_dataset.to_parquet(args.output, index=False)
    log(f"Saved URL model dataset with {len(url_dataset):,} rows to {args.output}")

    if url_dataset["label"].nunique() < 2:
        log(
            "Warning: URL dataset currently has fewer than 2 classes. "
            "You need a benign URL source before training a proper URL model."
        )

    stats_path = args.output.with_suffix(".stats.json")
    write_json(
        stats_path,
        {
            "rows": int(len(url_dataset)),
            "class_distribution": url_dataset["label"].value_counts().sort_index().to_dict(),
            "source_distribution": url_dataset["source"].value_counts().to_dict(),
        },
    )
    log(f"Wrote URL dataset stats to {stats_path}")


if __name__ == "__main__":
    main()
