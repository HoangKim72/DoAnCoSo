from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

from phishing_url_ml.feature_engineering import TOP_BRANDS
from phishing_url_ml.settings import BASE_DIR
from phishing_url_ml.utils import canonicalize_domain, canonicalize_url


CATEGORY_RULES = {
    "banking_payment": (
        "bank",
        "bancolombia",
        "paypal",
        "payment",
        "pay",
        "securepay",
        "invoice",
    ),
    "crypto_wallet": (
        "trezor",
        "ledger",
        "metamask",
        "wallet",
        "bitmart",
        "coinbase",
        "binance",
        "crypto",
    ),
    "ecommerce_delivery": (
        "amazon",
        "dhl",
        "dpd",
        "fedex",
        "usps",
        "delivery",
        "package",
        "order",
    ),
    "cloud_email_docs": (
        "onedrive",
        "office365",
        "outlook",
        "icloud",
        "mail",
        "xfinity",
        "pdf",
        "doc",
        "viewpdf",
    ),
    "social_gaming": (
        "roblox",
        "robiox",
        "spotify",
        "facebook",
        "instagram",
        "telegram",
    ),
}

PRIORITY_MAP = {
    "banking_payment": "critical",
    "crypto_wallet": "critical",
    "cloud_email_docs": "high",
    "ecommerce_delivery": "high",
    "social_gaming": "high",
    "generic_portal": "medium",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a phishing validation seed from the latest OpenPhish snapshot without touching the main training datasets."
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        help="Optional explicit OpenPhish snapshot file. Defaults to the latest snapshot in data/raw/openphish_snapshots.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/validation/vn_real_world_phishing_seed.csv"),
        help="CSV output path for the phishing seed.",
    )
    parser.add_argument(
        "--max-pairs",
        type=int,
        default=15,
        help="How many hostname+URL phishing pairs to keep.",
    )
    parser.add_argument(
        "--max-per-category",
        type=int,
        default=4,
        help="Maximum number of selected URL pairs per heuristic category.",
    )
    return parser.parse_args()


def resolve_repo_path(path_value: Path) -> Path:
    return path_value if path_value.is_absolute() else BASE_DIR / path_value


def latest_snapshot_file() -> Path:
    snapshot_dir = BASE_DIR / "data" / "raw" / "openphish_snapshots"
    snapshots = sorted(snapshot_dir.glob("openphish_*.txt"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not snapshots:
        raise FileNotFoundError(f"No OpenPhish snapshots found in {snapshot_dir}")
    return snapshots[0]


def classify_category(value: str) -> str:
    lowered = value.lower()
    for category, tokens in CATEGORY_RULES.items():
        if any(token in lowered for token in tokens):
            return category
    if any(brand in lowered for brand in TOP_BRANDS):
        return "generic_portal"
    return "generic_portal"


def score_candidate(url: str, host: str, category: str) -> tuple[int, int, int, str]:
    lowered = url.lower()
    token_hits = sum(token in lowered for tokens in CATEGORY_RULES.values() for token in tokens)
    special_score = lowered.count("?") + lowered.count("=") + lowered.count("&")
    host_depth = len([part for part in host.split(".") if part])
    category_weight = {
        "banking_payment": 0,
        "crypto_wallet": 1,
        "cloud_email_docs": 2,
        "ecommerce_delivery": 3,
        "social_gaming": 4,
        "generic_portal": 5,
    }[category]
    return (category_weight, -token_hits, -special_score - host_depth, lowered)


def build_rows(snapshot_path: Path, max_pairs: int, max_per_category: int) -> list[dict[str, str]]:
    raw_rows = [line.strip() for line in snapshot_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    candidates: list[dict[str, str]] = []
    seen_hosts: set[str] = set()
    seen_urls: set[str] = set()
    for raw_url in raw_rows:
        canonical = canonicalize_url(raw_url)
        if not canonical or canonical in seen_urls:
            continue
        parsed = urlparse(canonical)
        hostname = canonicalize_domain(parsed.hostname)
        if not hostname or hostname in seen_hosts:
            continue
        category = classify_category(canonical)
        seen_urls.add(canonical)
        seen_hosts.add(hostname)
        candidates.append(
            {
                "url": canonical,
                "hostname": hostname,
                "category": category,
                "priority": PRIORITY_MAP[category],
            }
        )

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for candidate in candidates:
        grouped[candidate["category"]].append(candidate)
    for category in grouped:
        grouped[category].sort(key=lambda item: score_candidate(item["url"], item["hostname"], item["category"]))

    ordered_categories = [
        "banking_payment",
        "crypto_wallet",
        "cloud_email_docs",
        "ecommerce_delivery",
        "social_gaming",
        "generic_portal",
    ]
    selected: list[dict[str, str]] = []
    selected_hosts: set[str] = set()
    counts = Counter()

    while len(selected) < max_pairs:
        progressed = False
        for category in ordered_categories:
            if counts[category] >= max_per_category:
                continue
            bucket = grouped.get(category, [])
            while bucket and bucket[0]["hostname"] in selected_hosts:
                bucket.pop(0)
            if not bucket:
                continue
            item = bucket.pop(0)
            selected.append(item)
            selected_hosts.add(item["hostname"])
            counts[category] += 1
            progressed = True
            if len(selected) >= max_pairs:
                break
        if not progressed:
            break

    rows: list[dict[str, str]] = []
    for index, item in enumerate(selected, start=1):
        rows.append(
            {
                "sample_id": f"P{index:03d}",
                "category": item["category"],
                "dataset_kind": "domain",
                "input_value": item["hostname"],
                "expected_label": "phishing",
                "priority": item["priority"],
                "note": f"Hostname extracted from OpenPhish snapshot {snapshot_path.name}.",
            }
        )
    for index, item in enumerate(selected, start=1):
        rows.append(
            {
                "sample_id": f"U{index:03d}",
                "category": item["category"],
                "dataset_kind": "url",
                "input_value": item["url"],
                "expected_label": "phishing",
                "priority": item["priority"],
                "note": f"URL selected from OpenPhish snapshot {snapshot_path.name}.",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["sample_id", "category", "dataset_kind", "input_value", "expected_label", "priority", "note"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    snapshot_path = resolve_repo_path(args.snapshot) if args.snapshot else latest_snapshot_file()
    output_path = resolve_repo_path(args.output)
    rows = build_rows(snapshot_path, args.max_pairs, args.max_per_category)
    write_csv(output_path, rows)
    print(snapshot_path)
    print(output_path)
    print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()
