from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from phishing_url_ml.settings import PROCESSED_DIR
from phishing_url_ml.utils import build_parsed_record, log, require_columns, write_json


OUTPUT_COLUMNS = [
    "original_value",
    "label",
    "source",
    "collected_at",
    "record_type",
    "source_record_id",
    "source_rank",
    "source_target",
    "scheme",
    "hostname",
    "subdomain",
    "domain",
    "suffix",
    "registered_domain",
    "path",
    "query",
    "fragment",
    "is_ip_host",
    "canonical_domain",
    "canonical_hostname",
    "canonical_registered_domain",
    "canonical_url",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean the normalized dataset.")
    parser.add_argument(
        "--input",
        type=Path,
        default=PROCESSED_DIR / "normalized_dataset.parquet",
        help="Path to the normalized parquet dataset.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DIR / "clean_master_dataset.parquet",
        help="Path to the cleaned parquet dataset.",
    )
    return parser.parse_args()


def deduplicate_records(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    domain_rows = df[df["record_type"] == "domain"].copy()
    url_rows = df[df["record_type"] == "url"].copy()

    before_count = len(df)
    domain_rows = domain_rows.drop_duplicates(subset=["canonical_hostname"], keep="first")
    url_rows = url_rows.drop_duplicates(subset=["canonical_url"], keep="first")
    combined = pd.concat([domain_rows, url_rows], ignore_index=True)
    combined = combined.sort_values(["collected_at", "label"], ascending=[True, False]).reset_index(drop=True)
    removed_count = before_count - len(combined)
    return combined, removed_count


def main() -> None:
    args = parse_args()
    df = pd.read_parquet(args.input)
    require_columns(
        df,
        ["original_value", "label", "source", "collected_at", "record_type"],
        dataset_name="normalized dataset",
    )

    log(f"Loaded {len(df):,} normalized rows from {args.input}")
    parsed = pd.DataFrame(
        [build_parsed_record(value, record_type) for value, record_type in zip(df["original_value"], df["record_type"])]
    )
    working = pd.concat([df.reset_index(drop=True), parsed], axis=1)
    working["collected_at"] = pd.to_datetime(working["collected_at"]).dt.strftime("%Y-%m-%d")
    working = working.sort_values(["collected_at", "label"], ascending=[True, False]).reset_index(drop=True)

    invalid_counts = working.loc[~working["parse_ok"], "invalid_reason"].value_counts().to_dict()
    invalid_removed = int((~working["parse_ok"]).sum())
    valid = working.loc[working["parse_ok"]].drop(columns=["parse_ok", "invalid_reason"]).copy()
    log(f"Removed {invalid_removed:,} invalid rows")

    positive_hosts = set(valid.loc[valid["label"] == 1, "canonical_hostname"])
    positive_urls = set(valid.loc[(valid["label"] == 1) & valid["canonical_url"].ne(""), "canonical_url"])
    overlap_mask = (
        (valid["label"] == 0)
        & (
            valid["canonical_hostname"].isin(positive_hosts)
            | valid["canonical_url"].isin(positive_urls)
        )
    )
    overlap_removed = int(overlap_mask.sum())
    valid = valid.loc[~overlap_mask].copy()
    log(f"Removed {overlap_removed:,} negative rows due to positive/negative overlap")

    deduplicated, dedup_removed = deduplicate_records(valid)
    deduplicated = deduplicated[OUTPUT_COLUMNS].copy()
    deduplicated.to_parquet(args.output, index=False)
    log(f"Saved clean master dataset with {len(deduplicated):,} rows to {args.output}")

    stats_path = args.output.with_suffix(".stats.json")
    write_json(
        stats_path,
        {
            "input_rows": int(len(df)),
            "invalid_rows_removed": invalid_removed,
            "invalid_reason_counts": invalid_counts,
            "overlap_rows_removed": overlap_removed,
            "deduplicated_rows_removed": dedup_removed,
            "output_rows": int(len(deduplicated)),
            "class_distribution": deduplicated["label"].value_counts().sort_index().to_dict(),
            "record_type_distribution": deduplicated["record_type"].value_counts().to_dict(),
        },
    )
    log(f"Wrote cleaning stats to {stats_path}")


if __name__ == "__main__":
    main()
