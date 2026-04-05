from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from phishing_url_ml.settings import PROCESSED_DIR
from phishing_url_ml.utils import log, require_columns, write_json


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
