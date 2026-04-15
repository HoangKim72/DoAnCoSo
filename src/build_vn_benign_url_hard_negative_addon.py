from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlparse

import pandas as pd

from collect_vn_benign_train_addon import (
    collect_from_seed,
    load_seed_sites,
    resolve_repo_path,
    session_with_headers,
)
from phishing_url_ml.settings import BASE_DIR


DEFAULT_OFFICIAL_URL_DATASET = Path("data/processed/official/url_model_official.parquet")
DEFAULT_VALIDATION_BENIGN_SEED = Path("data/validation/vn_real_world_benign_seed_expanded.csv")
DEFAULT_SEED_FILE = Path("data/curated/vn_url_hard_negative_seed_sites.csv")
DEFAULT_OUTPUT_DIR = Path("data/raw/vn_benign_url_addon")

HOST_PATTERNS = {
    "mail": 3,
    "online": 3,
    "portal": 2,
    "account": 2,
    "auth": 2,
    "cas": 3,
    "daotao": 2,
    "hocphi": 2,
    "hocvu": 2,
    "hocvudientu": 3,
    "student": 2,
    "sinhvien": 2,
}

PATH_PATTERNS = {
    "/account": 2,
    "/auth": 2,
    "/cas/login": 4,
    "/dang-nhap": 3,
    "/daotao": 2,
    "/hocphi": 2,
    "/hoc-vu": 2,
    "/hocvu": 2,
    "/login": 3,
    "/mail": 2,
    "/portal": 2,
    "/request": 2,
    "/tra-cuu": 3,
    ".aspx": 3,
    ".pdf": 1,
}

QUERY_KEY_PATTERNS = {
    "returnurl": 3,
    "service": 2,
    "page": 1,
    "flag": 1,
    "redirect": 2,
    "redirect_uri": 2,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Collect a benign URL hard-negative addon for the URL model while excluding rows "
            "already present in official training or validation seeds."
        )
    )
    parser.add_argument(
        "--seed-file",
        type=Path,
        default=DEFAULT_SEED_FILE,
        help="CSV file listing official seed sites used to collect hard-negative benign URLs.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="CSV output path. Defaults to data/raw/vn_benign_url_addon/vn_benign_url_addon_<date>_phase33.csv.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        help="Optional JSON summary output path. Defaults next to --output.",
    )
    parser.add_argument(
        "--exclude-url-dataset",
        type=Path,
        default=DEFAULT_OFFICIAL_URL_DATASET,
        help="Parquet dataset used to exclude URL rows already present in official training data.",
    )
    parser.add_argument(
        "--exclude-validation-seed",
        type=Path,
        default=DEFAULT_VALIDATION_BENIGN_SEED,
        help="CSV validation seed used to exclude exact benign URLs from the addon.",
    )
    parser.add_argument(
        "--exclude-addon-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory whose existing addon CSV files should also be excluded to avoid duplicates across runs.",
    )
    parser.add_argument(
        "--max-urls-per-seed",
        type=int,
        default=40,
        help="Maximum URL candidates collected per seed site before ranking/exclusion.",
    )
    parser.add_argument(
        "--max-sitemaps-per-seed",
        type=int,
        default=10,
        help="Maximum sitemap documents fetched per official site.",
    )
    parser.add_argument(
        "--request-timeout-seconds",
        type=int,
        default=12,
        help="HTTP timeout used while collecting candidates.",
    )
    parser.add_argument(
        "--max-selected-per-seed",
        type=int,
        default=12,
        help="Maximum hard-negative URL rows kept per seed site after ranking and exclusion.",
    )
    parser.add_argument(
        "--min-hardness-score",
        type=int,
        default=3,
        help="Minimum hardness score required for a URL to be kept in the addon.",
    )
    return parser.parse_args()


def load_excluded_from_official(dataset_path: Path) -> set[str]:
    resolved = resolve_repo_path(dataset_path)
    if not resolved.exists():
        return set()
    df = pd.read_parquet(resolved, columns=["sample_text"])
    return set(df["sample_text"].astype(str).str.strip().str.lower())


def load_excluded_from_validation(seed_path: Path) -> set[str]:
    resolved = resolve_repo_path(seed_path)
    if not resolved.exists():
        return set()
    df = pd.read_csv(resolved)
    if not {"dataset_kind", "input_value"}.issubset(df.columns):
        return set()
    filtered = df.loc[df["dataset_kind"].astype(str).str.lower() == "url", "input_value"]
    return set(filtered.astype(str).str.strip().str.lower())


def load_existing_addon_values(addon_dir: Path) -> set[str]:
    resolved_dir = resolve_repo_path(addon_dir)
    if not resolved_dir.exists():
        return set()
    values: set[str] = set()
    for csv_path in sorted(resolved_dir.glob("*.csv")):
        try:
            df = pd.read_csv(csv_path)
        except Exception:
            continue
        if "input_value" not in df.columns:
            continue
        values.update(df["input_value"].astype(str).str.strip().str.lower().tolist())
    return values


def hard_negative_details(url: str) -> tuple[int, list[str]]:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    path = parsed.path.lower()
    query = parsed.query.lower()
    path_and_query = f"{path}?{query}" if query else path

    score = 0
    matched_patterns: list[str] = []
    labels = [label for label in hostname.split(".") if label]

    if parsed.scheme.lower() == "http":
        score += 4
        matched_patterns.append("http_scheme")
    if query:
        score += 1
        matched_patterns.append("has_query")

    for label in labels:
        if label in HOST_PATTERNS:
            score += HOST_PATTERNS[label]
            matched_patterns.append(f"host:{label}")

    for snippet, weight in PATH_PATTERNS.items():
        if snippet in path_and_query:
            score += weight
            matched_patterns.append(f"path:{snippet}")

    for key, _value in parse_qsl(parsed.query, keep_blank_values=True):
        key_lower = key.lower()
        if key_lower in QUERY_KEY_PATTERNS:
            score += QUERY_KEY_PATTERNS[key_lower]
            matched_patterns.append(f"query:{key_lower}")

    if len(labels) >= 4:
        score += 1
        matched_patterns.append("deep_subdomain")
    if path.count("/") >= 3:
        score += 1
        matched_patterns.append("deep_path")

    deduped_patterns = list(dict.fromkeys(matched_patterns))
    return score, deduped_patterns


def derived_category(record: dict[str, Any]) -> str:
    category = str(record.get("category", ""))
    if category != "university":
        return category
    score, patterns = hard_negative_details(str(record.get("input_value", "")))
    if score >= 4 or any(pattern.startswith("host:") for pattern in patterns):
        return "university_portal"
    return category


def candidate_sort_key(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -int(record["hard_negative_score"]),
        -str(record["input_value"]).count("."),
        -len(str(record["input_value"])),
        str(record["source_name"]),
        str(record["input_value"]),
    )


def keep_top_per_seed(records: list[dict[str, Any]], max_selected_per_seed: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    per_seed_counts: Counter[str] = Counter()
    for record in sorted(records, key=candidate_sort_key):
        seed_id = str(record["seed_id"])
        if per_seed_counts[seed_id] >= max_selected_per_seed:
            continue
        selected.append(record)
        per_seed_counts[seed_id] += 1
    return selected


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "input_value",
        "source",
        "collected_at",
        "category",
        "source_name",
        "seed_id",
        "seed_homepage_url",
        "discovery_method",
        "hostname",
        "registered_domain",
        "hard_negative_score",
        "hard_negative_patterns",
        "note",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def resolve_output_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    if args.output:
        output_path = resolve_repo_path(args.output)
    else:
        stamp = datetime.now().strftime("%Y-%m-%d")
        output_path = resolve_repo_path(
            DEFAULT_OUTPUT_DIR / f"vn_benign_url_addon_{stamp}_phase33.csv"
        )
    summary_path = (
        resolve_repo_path(args.summary_output)
        if args.summary_output
        else output_path.with_name(f"{output_path.stem}_summary.json")
    )
    return output_path, summary_path


def main() -> None:
    args = parse_args()
    output_path, summary_path = resolve_output_paths(args)
    seeds = load_seed_sites(resolve_repo_path(args.seed_file))
    session = session_with_headers()

    excluded_values = set()
    excluded_values.update(load_excluded_from_official(args.exclude_url_dataset))
    excluded_values.update(load_excluded_from_validation(args.exclude_validation_seed))
    excluded_values.update(load_existing_addon_values(args.exclude_addon_dir))

    candidate_rows: list[dict[str, Any]] = []
    skipped_rows = {
        "already_in_official_or_validation_or_existing_addon": 0,
        "below_min_hardness_score": 0,
    }
    per_seed_summary: list[dict[str, Any]] = []

    collected_at = datetime.now().strftime("%Y-%m-%d")

    for seed in seeds:
        url_records, _domain_records, summary = collect_from_seed(
            session=session,
            seed=seed,
            max_urls_per_seed=args.max_urls_per_seed,
            max_sitemaps_per_seed=args.max_sitemaps_per_seed,
            timeout_seconds=args.request_timeout_seconds,
        )

        kept_for_seed = 0
        for record in url_records:
            input_value = str(record["input_value"]).strip().lower()
            if input_value in excluded_values:
                skipped_rows["already_in_official_or_validation_or_existing_addon"] += 1
                continue

            hardness_score, patterns = hard_negative_details(str(record["input_value"]))
            if hardness_score < args.min_hardness_score:
                skipped_rows["below_min_hardness_score"] += 1
                continue

            candidate_rows.append(
                {
                    "input_value": str(record["input_value"]),
                    "source": "vn_benign_url_addon_phase33",
                    "collected_at": collected_at,
                    "category": derived_category(record),
                    "source_name": str(record["source_name"]),
                    "seed_id": str(record["seed_id"]),
                    "seed_homepage_url": str(record["seed_homepage_url"]),
                    "discovery_method": str(record["discovery_method"]),
                    "hostname": str(record["hostname"]),
                    "registered_domain": str(record["registered_domain"]),
                    "hard_negative_score": hardness_score,
                    "hard_negative_patterns": " | ".join(patterns),
                    "note": f"{record['note']} Hard-negative benign URL collected for URL model Phase 33.",
                }
            )
            kept_for_seed += 1

        per_seed_summary.append(
            {
                **summary,
                "candidates_after_filters": kept_for_seed,
            }
        )

    deduped_candidates = {
        str(row["input_value"]).strip().lower(): row for row in candidate_rows
    }
    selected_rows = keep_top_per_seed(list(deduped_candidates.values()), args.max_selected_per_seed)
    selected_rows.sort(key=lambda row: (str(row["category"]), str(row["source_name"]), candidate_sort_key(row)))

    write_csv(output_path, selected_rows)

    pattern_counter: Counter[str] = Counter()
    for row in selected_rows:
        for pattern in str(row["hard_negative_patterns"]).split(" | "):
            if pattern:
                pattern_counter[pattern] += 1

    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "seed_file": str(resolve_repo_path(args.seed_file).relative_to(BASE_DIR)),
        "output": str(output_path.relative_to(BASE_DIR)),
        "exclude_url_dataset": str(resolve_repo_path(args.exclude_url_dataset).relative_to(BASE_DIR)),
        "exclude_validation_seed": str(resolve_repo_path(args.exclude_validation_seed).relative_to(BASE_DIR)),
        "counts": {
            "candidate_rows_before_dedup": len(candidate_rows),
            "candidate_rows_after_dedup": len(deduped_candidates),
            "selected_rows": len(selected_rows),
            **skipped_rows,
        },
        "selected_by_category": dict(sorted(Counter(str(row["category"]) for row in selected_rows).items())),
        "selected_by_source": dict(sorted(Counter(str(row["source_name"]) for row in selected_rows).items())),
        "pattern_counts": dict(sorted(pattern_counter.items())),
        "per_seed": per_seed_summary,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(output_path)
    print(summary_path)
    print(f"rows={len(selected_rows)}")
    print(json.dumps(summary["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
