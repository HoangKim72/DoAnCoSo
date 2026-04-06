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

DOMAIN_BENIGN_ADDON_DIR = RAW_DIR / "vn_benign_domain_addon"


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


def resolve_addon_date(row: dict[str, object], fallback_date: str = "2025-04-07") -> str:
    value = str(row.get("collected_at", "")).strip()
    if value:
        return value
    return fallback_date


def load_domain_benign_addons() -> pd.DataFrame:
    if not DOMAIN_BENIGN_ADDON_DIR.exists():
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    rows: list[dict[str, object]] = []
    csv_paths = sorted(DOMAIN_BENIGN_ADDON_DIR.glob("*.csv"))
    for csv_path in csv_paths:
        addon_df = pd.read_csv(csv_path)
        if "input_value" not in addon_df.columns:
            log(f"Skipping benign domain addon file without input_value column: {csv_path}")
            continue

        for row in addon_df.to_dict(orient="records"):
            parsed = build_parsed_record(row.get("input_value", ""), "domain")
            if not parsed["parse_ok"]:
                continue
            rows.append(
                {
                    "sample_text": parsed["canonical_hostname"] or parsed["hostname"],
                    "label": 0,
                    "source": str(row.get("source", "")).strip() or "vn_benign_domain_addon",
                    "collected_at": resolve_addon_date(row),
                    "record_type": "domain",
                    "hostname": parsed["hostname"],
                    "registered_domain": parsed["registered_domain"],
                    "subdomain": parsed["subdomain"],
                    "suffix": parsed["suffix"],
                    "is_ip_host": parsed["is_ip_host"],
                    "canonical_hostname": parsed["canonical_hostname"],
                    "canonical_registered_domain": parsed["canonical_registered_domain"],
                    "source_rank": pd.NA,
                }
            )

    if not rows:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    addon_frame = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    log(
        "Loaded curated benign domain addon rows: "
        f"{len(addon_frame):,} from {len(csv_paths)} file(s) in {DOMAIN_BENIGN_ADDON_DIR}"
    )
    return addon_frame


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
    working = working[OUTPUT_COLUMNS].copy()
    addon_df = load_domain_benign_addons()
    if not addon_df.empty:
        working = pd.concat([working, addon_df], ignore_index=True)

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
