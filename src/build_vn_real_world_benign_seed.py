from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pandas as pd

from collect_vn_benign_train_addon import (
    collect_from_seed,
    load_seed_sites,
    resolve_repo_path,
    session_with_headers,
)
from phishing_url_ml.settings import BASE_DIR


DEFAULT_DOMAIN_EXCLUDE = Path("data/processed/official/domain_model_official.parquet")
DEFAULT_URL_EXCLUDE = Path("data/processed/official/url_model_official.parquet")

PRIORITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}

HOST_PORTAL_LABELS = {
    "account",
    "auth",
    "billing",
    "cas",
    "daotao",
    "elearning",
    "hocphi",
    "hocvu",
    "hocvudientu",
    "login",
    "mail",
    "online",
    "portal",
    "sinhvien",
    "sso",
}

PATH_PORTAL_SNIPPETS = (
    "/account",
    "/auth/",
    "/billing",
    "/cas/login",
    "/dang-nhap",
    "/daotao",
    "/elearning",
    "/hocphi",
    "/hoc-vu",
    "/hocvu",
    "/login",
    "/portal",
    "/sinhvien",
    "/sso",
    "/tra-cuu",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an expanded Vietnamese real-world benign validation seed from official websites "
            "while excluding rows that already exist in the official training datasets."
        )
    )
    parser.add_argument(
        "--seed-file",
        type=Path,
        default=Path("data/curated/vn_official_site_seeds_focus.csv"),
        help="CSV file listing official websites used as validation seed sources.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/validation/vn_real_world_benign_seed_expanded.csv"),
        help="CSV output path for the expanded benign validation seed.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        help="Optional JSON summary output path. Defaults next to --output.",
    )
    parser.add_argument(
        "--exclude-domain-dataset",
        type=Path,
        default=DEFAULT_DOMAIN_EXCLUDE,
        help="Parquet dataset used to exclude domain rows that already appear in official train data.",
    )
    parser.add_argument(
        "--exclude-url-dataset",
        type=Path,
        default=DEFAULT_URL_EXCLUDE,
        help="Parquet dataset used to exclude URL rows that already appear in official train data.",
    )
    parser.add_argument(
        "--max-urls-per-seed",
        type=int,
        default=18,
        help="Maximum URL candidates collected per official site before train-overlap exclusion.",
    )
    parser.add_argument(
        "--max-sitemaps-per-seed",
        type=int,
        default=6,
        help="Maximum sitemap documents fetched per official site.",
    )
    parser.add_argument(
        "--request-timeout-seconds",
        type=int,
        default=12,
        help="HTTP timeout used while collecting validation candidates.",
    )
    parser.add_argument(
        "--max-url-rows-per-seed",
        type=int,
        default=3,
        help="Maximum URL validation rows kept per seed site after ranking.",
    )
    parser.add_argument(
        "--max-domain-rows-per-seed",
        type=int,
        default=2,
        help="Maximum domain validation rows kept per seed site after ranking.",
    )
    parser.add_argument(
        "--max-url-rows-per-category",
        type=int,
        default=12,
        help="Maximum URL validation rows kept per category.",
    )
    parser.add_argument(
        "--max-domain-rows-per-category",
        type=int,
        default=10,
        help="Maximum domain validation rows kept per category.",
    )
    return parser.parse_args()


def load_exclusion_values(dataset_path: Path, column_name: str = "sample_text") -> set[str]:
    resolved_path = resolve_repo_path(dataset_path)
    if not resolved_path.exists():
        return set()
    df = pd.read_parquet(resolved_path, columns=[column_name])
    return set(df[column_name].astype(str).str.strip().str.lower())


def priority_rank(value: str) -> int:
    return PRIORITY_ORDER.get(value, 99)


def portal_keyword_hits(value: str) -> int:
    candidate = value if "://" in value else f"https://{value}/"
    parsed = urlparse(candidate)
    hostname = (parsed.hostname or parsed.path or "").lower()
    path_and_query = f"{parsed.path.lower()}?{parsed.query.lower()}"
    labels = [label for label in hostname.split(".") if label]
    host_hits = sum(label in HOST_PORTAL_LABELS for label in labels)
    path_hits = sum(snippet in path_and_query for snippet in PATH_PORTAL_SNIPPETS)
    return host_hits + path_hits


def validation_portal_score(value: str) -> tuple[int, int, str]:
    lowered = value.lower()
    keyword_hits = portal_keyword_hits(lowered)
    host_depth = lowered.count(".")
    return (-keyword_hits, -host_depth, lowered)


def derived_category(record: dict[str, Any]) -> str:
    category = str(record["category"])
    value = str(record["input_value"])
    if category == "university" and portal_keyword_hits(value) > 0:
        return "university_portal"
    return category


def derived_priority(record: dict[str, Any]) -> str:
    category = str(record["category"])
    value = str(record["input_value"])
    hits = portal_keyword_hits(value)
    if category == "university" and hits > 0:
        return "critical" if hits >= 2 else "high"
    if category in {"banking", "government"}:
        return "high"
    return "medium"


def candidate_sort_key(record: dict[str, Any]) -> tuple[Any, ...]:
    value = str(record["input_value"])
    portal_value = value if str(record["dataset_kind"]) == "url" else f"https://{value}/"
    return (
        priority_rank(str(record["priority"])),
        0 if str(record["category"]) == "university_portal" else 1,
        validation_portal_score(portal_value),
        str(record.get("source_name", "")),
        value,
    )


def filter_out_training_overlap(
    records: list[dict[str, Any]],
    excluded_domain_values: set[str],
    excluded_url_values: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for record in records:
        value = str(record["input_value"]).strip().lower()
        dataset_kind = str(record["dataset_kind"])
        exclusion_values = excluded_domain_values if dataset_kind == "domain" else excluded_url_values
        if value in exclusion_values:
            excluded.append(record)
        else:
            kept.append(record)
    return kept, excluded


def select_rows(
    records: list[dict[str, Any]],
    max_rows_per_seed: int,
    max_rows_per_category: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seed_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    for record in sorted(records, key=candidate_sort_key):
        seed_id = str(record["seed_id"])
        category = str(record["category"])
        if seed_counts[seed_id] >= max_rows_per_seed:
            continue
        if category_counts[category] >= max_rows_per_category:
            continue
        selected.append(record)
        seed_counts[seed_id] += 1
        category_counts[category] += 1
    return selected


def assign_sample_ids(records: list[dict[str, Any]], prefix: str) -> list[dict[str, Any]]:
    assigned: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        assigned.append({"sample_id": f"{prefix}{index:03d}", **record})
    return assigned


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_id",
        "category",
        "dataset_kind",
        "input_value",
        "expected_label",
        "priority",
        "source_name",
        "seed_id",
        "seed_homepage_url",
        "discovery_method",
        "hostname",
        "registered_domain",
        "note",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summary_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key, "")) for row in rows)
    return dict(sorted(counter.items()))


def build_validation_records(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    seeds = load_seed_sites(resolve_repo_path(args.seed_file))
    session = session_with_headers()

    excluded_domain_values = load_exclusion_values(args.exclude_domain_dataset)
    excluded_url_values = load_exclusion_values(args.exclude_url_dataset)

    collected_records: list[dict[str, Any]] = []
    excluded_records: list[dict[str, Any]] = []
    per_seed_summary: list[dict[str, Any]] = []

    for seed in seeds:
        url_records, domain_records, summary = collect_from_seed(
            session=session,
            seed=seed,
            max_urls_per_seed=args.max_urls_per_seed,
            max_sitemaps_per_seed=args.max_sitemaps_per_seed,
            timeout_seconds=args.request_timeout_seconds,
        )
        combined_records = [
            {
                **record,
                "category": derived_category(record),
                "priority": derived_priority(record),
                "expected_label": "benign",
            }
            for record in [*url_records, *domain_records]
        ]
        kept_records, removed_records = filter_out_training_overlap(
            combined_records,
            excluded_domain_values=excluded_domain_values,
            excluded_url_values=excluded_url_values,
        )
        collected_records.extend(kept_records)
        excluded_records.extend(removed_records)
        per_seed_summary.append(
            {
                **summary,
                "kept_after_exclusion": len(kept_records),
                "excluded_for_train_overlap": len(removed_records),
            }
        )

    url_records = [record for record in collected_records if str(record["dataset_kind"]) == "url"]
    domain_records = [record for record in collected_records if str(record["dataset_kind"]) == "domain"]

    selected_urls = select_rows(
        url_records,
        max_rows_per_seed=args.max_url_rows_per_seed,
        max_rows_per_category=args.max_url_rows_per_category,
    )
    selected_domains = select_rows(
        domain_records,
        max_rows_per_seed=args.max_domain_rows_per_seed,
        max_rows_per_category=args.max_domain_rows_per_category,
    )

    final_rows = assign_sample_ids(selected_domains, "BD") + assign_sample_ids(selected_urls, "BU")
    final_rows.sort(key=lambda row: (str(row["dataset_kind"]), str(row["category"]), str(row["sample_id"])))

    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "seed_file": str(resolve_repo_path(args.seed_file).relative_to(BASE_DIR)),
        "output": str(resolve_repo_path(args.output).relative_to(BASE_DIR)),
        "exclude_domain_dataset": str(resolve_repo_path(args.exclude_domain_dataset).relative_to(BASE_DIR)),
        "exclude_url_dataset": str(resolve_repo_path(args.exclude_url_dataset).relative_to(BASE_DIR)),
        "counts": {
            "collected_before_exclusion": len(collected_records) + len(excluded_records),
            "excluded_for_train_overlap": len(excluded_records),
            "remaining_after_exclusion": len(collected_records),
            "selected_domain_rows": len(selected_domains),
            "selected_url_rows": len(selected_urls),
            "final_rows": len(final_rows),
        },
        "selected_by_dataset_kind": summary_counts(final_rows, "dataset_kind"),
        "selected_by_category": summary_counts(final_rows, "category"),
        "excluded_by_dataset_kind": summary_counts(excluded_records, "dataset_kind"),
        "excluded_by_category": summary_counts(excluded_records, "category"),
        "per_seed": per_seed_summary,
    }
    return final_rows, summary


def main() -> None:
    args = parse_args()
    output_path = resolve_repo_path(args.output)
    summary_path = (
        resolve_repo_path(args.summary_output)
        if args.summary_output
        else output_path.with_name(f"{output_path.stem}_summary.json")
    )

    rows, summary = build_validation_records(args)
    write_csv(output_path, rows)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(output_path)
    print(summary_path)
    print(f"rows={len(rows)}")
    print(json.dumps(summary["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
