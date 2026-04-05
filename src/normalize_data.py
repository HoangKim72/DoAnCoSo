from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from phishing_url_ml.settings import PROCESSED_DIR, SOURCE_CONFIGS
from phishing_url_ml.utils import iter_raw_files, log, parse_date_from_filename


STANDARD_COLUMNS = [
    "original_value",
    "label",
    "source",
    "collected_at",
    "record_type",
    "source_record_id",
    "source_rank",
    "source_target",
]


def normalize_phishtank(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    collected_at = parse_date_from_filename(path)
    rows = []
    for entry in payload:
        rows.append(
            {
                "original_value": entry.get("url", ""),
                "label": 1,
                "source": "phishtank",
                "collected_at": collected_at,
                "record_type": "url",
                "source_record_id": entry.get("phish_id", ""),
                "source_rank": pd.NA,
                "source_target": entry.get("target", ""),
            }
        )
    frame = pd.DataFrame(rows)
    log(f"Normalized {len(frame):,} records from {path.name}")
    return frame


def normalize_openphish(path: Path) -> pd.DataFrame:
    collected_at = parse_date_from_filename(path)
    values = path.read_text(encoding="utf-8").splitlines()
    frame = pd.DataFrame(
        {
            "original_value": values,
            "label": 1,
            "source": "openphish",
            "collected_at": collected_at,
            "record_type": "url",
            "source_record_id": "",
            "source_rank": pd.NA,
            "source_target": "",
        }
    )
    log(f"Normalized {len(frame):,} records from {path.name}")
    return frame


def normalize_news_sitemaps(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    fallback_date = parse_date_from_filename(path)
    rows = []
    for entry in payload:
        collected_at = str(entry.get("collected_at", "")).strip() or fallback_date
        rows.append(
            {
                "original_value": entry.get("url", ""),
                "label": 0,
                "source": "news_sitemaps",
                "collected_at": collected_at,
                "record_type": "url",
                "source_record_id": entry.get("sitemap_url", ""),
                "source_rank": pd.NA,
                "source_target": entry.get("publisher", ""),
            }
        )

    frame = pd.DataFrame(rows)
    log(f"Normalized {len(frame):,} records from {path.name}")
    return frame


def normalize_tranco(path: Path, top_n: int | None) -> pd.DataFrame:
    collected_at = parse_date_from_filename(path)
    frame = pd.read_csv(
        path,
        names=["source_rank", "original_value"],
        nrows=top_n,
        compression="zip",
        dtype={"source_rank": "Int64", "original_value": "string"},
    )
    frame["label"] = 0
    frame["source"] = "tranco"
    frame["collected_at"] = collected_at
    frame["record_type"] = "domain"
    frame["source_record_id"] = ""
    frame["source_target"] = ""
    frame = frame[STANDARD_COLUMNS]
    log(f"Normalized {len(frame):,} records from {path.name}")
    return frame


def normalize_mendeley_phishing_url(path: Path) -> pd.DataFrame:
    collected_at = SOURCE_CONFIGS["mendeley_phishing_url"].published_date or parse_date_from_filename(path)
    with ZipFile(path) as archive:
        with archive.open("Phishing URL dataset/URL dataset.csv") as handle:
            frame = pd.read_csv(handle, usecols=["url", "type"])

    type_values = frame["type"].astype("string").str.strip().str.lower()
    mapped_label = type_values.map({"phishing": 1, "legitimate": 0})
    normalized = pd.DataFrame(
        {
            "original_value": frame["url"],
            "label": mapped_label,
            "source": "mendeley_phishing_url",
            "collected_at": collected_at,
            "record_type": "url",
            "source_record_id": "",
            "source_rank": pd.NA,
            "source_target": "10.17632/vfszbj9b36.1",
        }
    ).dropna(subset=["original_value", "label"])
    normalized["label"] = normalized["label"].astype(int)
    log(f"Normalized {len(normalized):,} records from {path.name}")
    return normalized


def normalize_mendeley_legitphish(path: Path) -> pd.DataFrame:
    collected_at = SOURCE_CONFIGS["mendeley_legitphish"].published_date or parse_date_from_filename(path)
    with ZipFile(path) as archive:
        with archive.open("LegitPhish Dataset/url_features_extracted1.csv") as handle:
            frame = pd.read_csv(handle, usecols=["URL", "ClassLabel"])

    class_values = pd.to_numeric(frame["ClassLabel"], errors="coerce")
    normalized = pd.DataFrame(
        {
            "original_value": frame["URL"],
            "label": class_values.map({0.0: 1, 1.0: 0}),
            "source": "mendeley_legitphish",
            "collected_at": collected_at,
            "record_type": "url",
            "source_record_id": "",
            "source_rank": pd.NA,
            "source_target": "10.17632/hx4m73v2sf.1",
        }
    ).dropna(subset=["original_value", "label"])
    normalized["label"] = normalized["label"].astype(int)
    log(f"Normalized {len(normalized):,} records from {path.name}")
    return normalized


NORMALIZERS = {
    "phishtank": normalize_phishtank,
    "openphish": normalize_openphish,
    "news_sitemaps": normalize_news_sitemaps,
    "mendeley_phishing_url": normalize_mendeley_phishing_url,
    "mendeley_legitphish": normalize_mendeley_legitphish,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize raw data feeds into a shared schema.")
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=sorted(SOURCE_CONFIGS),
        default=["tranco", "mendeley_phishing_url", "mendeley_legitphish"],
        help="Sources to include during normalization.",
    )
    parser.add_argument(
        "--include-openphish",
        action="store_true",
        help="Required if you want to process OpenPhish raw files.",
    )
    parser.add_argument("--start-date", help="Optional YYYY-MM-DD lower bound for raw file dates.")
    parser.add_argument("--end-date", help="Optional YYYY-MM-DD upper bound for raw file dates.")
    parser.add_argument(
        "--tranco-top-n",
        type=int,
        default=100000,
        help="Limit benign Tranco domains for manageable experiments. Use 1000000 for full list.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DIR / "normalized_dataset.parquet",
        help="Output parquet path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sources = list(dict.fromkeys(args.sources))

    if "openphish" in sources and not args.include_openphish:
        raise SystemExit(
            "OpenPhish processing is disabled by default. Re-run with --include-openphish "
            "after you confirm the feed terms fit your use case."
        )

    frames: list[pd.DataFrame] = []
    for source in sources:
        raw_files = list(iter_raw_files(source, start_date=args.start_date, end_date=args.end_date))
        if not raw_files:
            log(f"No raw files found for source={source}")
            continue

        if source == "tranco":
            for raw_path in raw_files:
                frames.append(normalize_tranco(raw_path, top_n=args.tranco_top_n))
            continue

        normalizer = NORMALIZERS[source]
        for raw_path in raw_files:
            frames.append(normalizer(raw_path))

    if not frames:
        raise SystemExit("No raw files were normalized. Run download_data.py first or adjust the date range.")

    normalized = pd.concat(frames, ignore_index=True)
    for column in STANDARD_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = pd.NA
    normalized = normalized[STANDARD_COLUMNS].copy()
    normalized["label"] = normalized["label"].astype(int)
    normalized["collected_at"] = pd.to_datetime(normalized["collected_at"]).dt.strftime("%Y-%m-%d")
    normalized = normalized.sort_values(["collected_at", "source", "label"], ascending=[True, True, False])
    normalized = normalized.reset_index(drop=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_parquet(args.output, index=False)
    log(f"Saved normalized dataset with {len(normalized):,} rows to {args.output}")


if __name__ == "__main__":
    main()
