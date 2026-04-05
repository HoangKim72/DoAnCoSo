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
    "record_type",
    "hostname",
    "registered_domain",
    "subdomain",
    "suffix",
    "is_ip_host",
    "canonical_hostname",
    "canonical_registered_domain",
    "source_rank",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the dataset for the domain model.")
    parser.add_argument(
        "--input",
        type=Path,
        default=PROCESSED_DIR / "clean_master_dataset.parquet",
        help="Path to the cleaned master dataset.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DIR / "domain_model_dataset.parquet",
        help="Path to the output parquet dataset.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_parquet(args.input)
    require_columns(
        df,
        ["label", "source", "collected_at", "hostname", "registered_domain", "canonical_hostname"],
        dataset_name="clean master dataset",
    )

    working = df.loc[df["canonical_hostname"].ne("")].copy()
    working["sample_text"] = working["canonical_hostname"]
    working = working.sort_values(["collected_at", "label"], ascending=[True, False]).reset_index(drop=True)
    working = working.drop_duplicates(subset=["sample_text"], keep="first")

    positive_hosts = set(working.loc[working["label"] == 1, "sample_text"])
    overlap_mask = (working["label"] == 0) & working["sample_text"].isin(positive_hosts)
    if overlap_mask.any():
        working = working.loc[~overlap_mask].copy()

    domain_dataset = working[OUTPUT_COLUMNS].copy()
    domain_dataset.to_parquet(args.output, index=False)
    log(f"Saved domain model dataset with {len(domain_dataset):,} rows to {args.output}")

    stats_path = args.output.with_suffix(".stats.json")
    write_json(
        stats_path,
        {
            "rows": int(len(domain_dataset)),
            "class_distribution": domain_dataset["label"].value_counts().sort_index().to_dict(),
            "source_distribution": domain_dataset["source"].value_counts().to_dict(),
        },
    )
    log(f"Wrote domain dataset stats to {stats_path}")


if __name__ == "__main__":
    main()
