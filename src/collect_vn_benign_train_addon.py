from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

import pandas as pd
import requests

from phishing_url_ml.settings import BASE_DIR, DEFAULT_USER_AGENT
from phishing_url_ml.utils import canonicalize_domain, canonicalize_url, ensure_parent_dir, extract_domain_parts, log


SITEMAP_FALLBACK_PATHS = (
    "/robots.txt",
    "/sitemap.xml",
    "/sitemap_index.xml",
    "/sitemap-index.xml",
    "/sitemap_news.xml",
    "/sitemap-news.xml",
)
PORTAL_KEYWORDS = (
    "account",
    "auth",
    "billing",
    "dang-nhap",
    "daotao",
    "elearning",
    "hocphi",
    "hoc-vu",
    "hocvu",
    "login",
    "mail",
    "portal",
    "sinhvien",
    "sso",
    "student",
    "support",
    "tra-cuu",
)


class HrefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.hrefs.append(value)


@dataclass(frozen=True)
class SeedSite:
    seed_id: str
    category: str
    source_name: str
    homepage_url: str
    note: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect a Vietnamese benign train addon from official websites, robots, and sitemaps."
    )
    parser.add_argument(
        "--seed-file",
        type=Path,
        default=Path("data/curated/vn_official_site_seeds.csv"),
        help="CSV file listing official seed websites.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/curated"),
        help="Directory used to store collected addon files.",
    )
    parser.add_argument(
        "--max-urls-per-seed",
        type=int,
        default=18,
        help="Maximum number of URL samples kept per seed site.",
    )
    parser.add_argument(
        "--max-sitemaps-per-seed",
        type=int,
        default=6,
        help="Maximum number of sitemap documents fetched per seed site.",
    )
    parser.add_argument(
        "--request-timeout-seconds",
        type=int,
        default=12,
        help="HTTP timeout used when collecting pages and sitemaps.",
    )
    return parser.parse_args()


def resolve_repo_path(path_value: Path) -> Path:
    return path_value if path_value.is_absolute() else BASE_DIR / path_value


def load_seed_sites(path: Path) -> list[SeedSite]:
    df = pd.read_csv(path)
    required = ["seed_id", "category", "source_name", "homepage_url", "note"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Seed file is missing required columns: {', '.join(missing)}")
    return [
        SeedSite(
            seed_id=str(row.seed_id),
            category=str(row.category),
            source_name=str(row.source_name),
            homepage_url=str(row.homepage_url),
            note=str(row.note),
        )
        for row in df.itertuples(index=False)
    ]


def session_with_headers() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": DEFAULT_USER_AGENT})
    return session


def fetch_text(session: requests.Session, url: str, timeout_seconds: int) -> str:
    response = session.get(url, timeout=timeout_seconds, allow_redirects=True)
    response.raise_for_status()
    return response.text


def normalized_registered_domain(url_or_host: str) -> str:
    parsed = urlparse(url_or_host if "://" in url_or_host else f"https://{url_or_host}")
    hostname = canonicalize_domain(parsed.hostname or parsed.path)
    if not hostname:
        return ""
    return extract_domain_parts(hostname).get("registered_domain", "") or hostname


def parse_homepage_links(html_text: str, base_url: str) -> list[str]:
    parser = HrefParser()
    parser.feed(html_text)
    return [urljoin(base_url, href) for href in parser.hrefs]


def parse_robots_for_sitemaps(text: str) -> list[str]:
    sitemap_urls: list[str] = []
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip().lower() == "sitemap":
            sitemap_urls.append(value.strip())
    return sitemap_urls


def parse_sitemap_xml(text: str) -> tuple[list[str], list[str]]:
    text = text.strip()
    if not text:
        return [], []
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError:
        return [], []

    namespace_match = re.match(r"\{(.*)\}", root.tag)
    namespace = namespace_match.group(1) if namespace_match else ""
    loc_tag = f"{{{namespace}}}loc" if namespace else "loc"
    sitemap_tag = f"{{{namespace}}}sitemap" if namespace else "sitemap"
    url_tag = f"{{{namespace}}}url" if namespace else "url"

    sitemap_urls = [node.findtext(loc_tag, default="").strip() for node in root.findall(sitemap_tag)]
    page_urls = [node.findtext(loc_tag, default="").strip() for node in root.findall(url_tag)]
    return [url for url in sitemap_urls if url], [url for url in page_urls if url]


def portal_score(value: str) -> tuple[int, int, str]:
    lowered = value.lower()
    keyword_hits = sum(keyword in lowered for keyword in PORTAL_KEYWORDS)
    subdomain_depth = len([part for part in urlparse(value).hostname.split(".") if part]) if "://" in value and urlparse(value).hostname else 0
    return (-keyword_hits, -subdomain_depth, lowered)


def filter_internal_urls(urls: Iterable[str], registered_domain: str) -> list[str]:
    kept: list[str] = []
    seen: set[str] = set()
    for url in urls:
        canonical = canonicalize_url(url)
        if not canonical or canonical in seen:
            continue
        hostname = canonicalize_domain(urlparse(canonical).hostname)
        if not hostname:
            continue
        if extract_domain_parts(hostname).get("registered_domain", "") != registered_domain:
            continue
        seen.add(canonical)
        kept.append(canonical)
    return kept


def collect_from_seed(
    session: requests.Session,
    seed: SeedSite,
    max_urls_per_seed: int,
    max_sitemaps_per_seed: int,
    timeout_seconds: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    registered_domain = normalized_registered_domain(seed.homepage_url)
    if not registered_domain:
        return [], [], {"seed_id": seed.seed_id, "source_name": seed.source_name, "status": "invalid_seed_domain"}

    collected_urls: dict[str, dict[str, object]] = {}
    collected_domains: dict[str, dict[str, object]] = {}
    fetch_notes: list[str] = []

    def add_url(candidate_url: str, discovery_method: str) -> None:
        canonical = canonicalize_url(candidate_url)
        if not canonical:
            return
        hostname = canonicalize_domain(urlparse(canonical).hostname)
        if not hostname:
            return
        parts = extract_domain_parts(hostname)
        if parts.get("registered_domain", "") != registered_domain:
            return
        if canonical not in collected_urls:
            collected_urls[canonical] = {
                "category": seed.category,
                "source_name": seed.source_name,
                "seed_id": seed.seed_id,
                "seed_homepage_url": seed.homepage_url,
                "dataset_kind": "url",
                "input_value": canonical,
                "expected_label": "benign",
                "discovery_method": discovery_method,
                "hostname": hostname,
                "registered_domain": parts.get("registered_domain", ""),
                "note": seed.note,
            }
        if hostname not in collected_domains:
            collected_domains[hostname] = {
                "category": seed.category,
                "source_name": seed.source_name,
                "seed_id": seed.seed_id,
                "seed_homepage_url": seed.homepage_url,
                "dataset_kind": "domain",
                "input_value": hostname,
                "expected_label": "benign",
                "discovery_method": discovery_method,
                "hostname": hostname,
                "registered_domain": parts.get("registered_domain", ""),
                "note": seed.note,
            }

    try:
        homepage_html = fetch_text(session, seed.homepage_url, timeout_seconds)
        homepage_links = parse_homepage_links(homepage_html, seed.homepage_url)
        for url in filter_internal_urls(homepage_links, registered_domain):
            add_url(url, "homepage")
    except Exception as exc:  # pragma: no cover - depends on network
        fetch_notes.append(f"homepage_error: {exc}")

    sitemap_queue: list[str] = []
    robots_url = urljoin(seed.homepage_url, "/robots.txt")
    try:
        robots_text = fetch_text(session, robots_url, timeout_seconds)
        sitemap_queue.extend(parse_robots_for_sitemaps(robots_text))
    except Exception as exc:  # pragma: no cover - depends on network
        fetch_notes.append(f"robots_error: {exc}")

    for path in SITEMAP_FALLBACK_PATHS[1:]:
        sitemap_queue.append(urljoin(seed.homepage_url, path))

    normalized_sitemaps: list[str] = []
    seen_sitemaps: set[str] = set()
    for sitemap_url in sitemap_queue:
        if sitemap_url in seen_sitemaps:
            continue
        seen_sitemaps.add(sitemap_url)
        normalized_sitemaps.append(sitemap_url)

    processed_sitemaps = 0
    extra_sitemaps: list[str] = []
    while normalized_sitemaps and processed_sitemaps < max_sitemaps_per_seed:
        sitemap_url = normalized_sitemaps.pop(0)
        try:
            sitemap_text = fetch_text(session, sitemap_url, timeout_seconds)
            child_sitemaps, page_urls = parse_sitemap_xml(sitemap_text)
            for page_url in filter_internal_urls(page_urls, registered_domain):
                add_url(page_url, "sitemap")
            for child_sitemap in child_sitemaps:
                if child_sitemap not in seen_sitemaps:
                    seen_sitemaps.add(child_sitemap)
                    extra_sitemaps.append(child_sitemap)
            processed_sitemaps += 1
        except Exception as exc:  # pragma: no cover - depends on network
            fetch_notes.append(f"sitemap_error[{sitemap_url}]: {exc}")
    normalized_sitemaps.extend(extra_sitemaps)

    ranked_urls = sorted(collected_urls.values(), key=lambda item: portal_score(str(item["input_value"])))
    ranked_domains = sorted(collected_domains.values(), key=lambda item: portal_score(f"https://{item['input_value']}/"))

    selected_urls = ranked_urls[:max_urls_per_seed]
    selected_hosts = {str(item["hostname"]) for item in selected_urls}
    selected_domains = [item for item in ranked_domains if str(item["hostname"]) in selected_hosts]
    if len(selected_domains) < min(len(selected_urls), max_urls_per_seed):
        remaining_domains = [item for item in ranked_domains if str(item["hostname"]) not in selected_hosts]
        selected_domains.extend(remaining_domains[: max_urls_per_seed - len(selected_domains)])

    summary = {
        "seed_id": seed.seed_id,
        "source_name": seed.source_name,
        "category": seed.category,
        "registered_domain": registered_domain,
        "selected_url_count": len(selected_urls),
        "selected_domain_count": len(selected_domains),
        "notes": fetch_notes,
    }
    return selected_urls, selected_domains, summary


def assign_sample_ids(records: list[dict[str, object]], prefix: str) -> list[dict[str, object]]:
    assigned: list[dict[str, object]] = []
    for index, record in enumerate(records, start=1):
        assigned.append({"sample_id": f"{prefix}{index:04d}", **record})
    return assigned


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    ensure_parent_dir(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    args = parse_args()
    seed_path = resolve_repo_path(args.seed_file)
    output_dir = resolve_repo_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    seeds = load_seed_sites(seed_path)
    session = session_with_headers()

    all_url_records: list[dict[str, object]] = []
    all_domain_records: list[dict[str, object]] = []
    per_seed_summaries: list[dict[str, object]] = []

    for seed in seeds:
        log(f"Collecting official benign addon from {seed.source_name} ({seed.homepage_url})")
        url_records, domain_records, summary = collect_from_seed(
            session=session,
            seed=seed,
            max_urls_per_seed=args.max_urls_per_seed,
            max_sitemaps_per_seed=args.max_sitemaps_per_seed,
            timeout_seconds=args.request_timeout_seconds,
        )
        all_url_records.extend(url_records)
        all_domain_records.extend(domain_records)
        per_seed_summaries.append(summary)
        log(
            f"Collected {len(url_records)} URL rows and {len(domain_records)} domain rows "
            f"for {seed.source_name}"
        )

    deduped_urls = {str(row["input_value"]): row for row in all_url_records}
    deduped_domains = {str(row["input_value"]): row for row in all_domain_records}
    url_rows = assign_sample_ids(list(deduped_urls.values()), "VU")
    domain_rows = assign_sample_ids(list(deduped_domains.values()), "VD")

    url_rows.sort(key=lambda row: (str(row["category"]), str(row["source_name"]), str(row["input_value"])))
    domain_rows.sort(key=lambda row: (str(row["category"]), str(row["source_name"]), str(row["input_value"])))

    urls_path = output_dir / "vn_real_world_benign_train_addon_urls.csv"
    domains_path = output_dir / "vn_real_world_benign_train_addon_domains.csv"
    summary_path = output_dir / "vn_real_world_benign_train_addon_summary.json"

    common_fields = [
        "sample_id",
        "category",
        "source_name",
        "seed_id",
        "seed_homepage_url",
        "dataset_kind",
        "input_value",
        "expected_label",
        "discovery_method",
        "hostname",
        "registered_domain",
        "note",
    ]
    write_csv(urls_path, common_fields, url_rows)
    write_csv(domains_path, common_fields, domain_rows)

    summary = {
        "seed_file": str(seed_path),
        "generated_at": pd.Timestamp.now(tz="Asia/Saigon").isoformat(),
        "url_rows": len(url_rows),
        "domain_rows": len(domain_rows),
        "per_seed": per_seed_summaries,
        "artifacts": {
            "urls_csv": str(urls_path),
            "domains_csv": str(domains_path),
        },
        "category_counts": {
            "urls": pd.Series([row["category"] for row in url_rows]).value_counts().sort_index().to_dict(),
            "domains": pd.Series([row["category"] for row in domain_rows]).value_counts().sort_index().to_dict(),
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    log(f"Wrote URL addon file to {urls_path}")
    log(f"Wrote domain addon file to {domains_path}")
    log(f"Wrote summary to {summary_path}")
    log(f"Final counts: {len(url_rows)} URL rows, {len(domain_rows)} domain rows")


if __name__ == "__main__":
    main()
