from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path

import requests

from phishing_url_ml.news_sitemaps import (
    DEFAULT_MAX_SITEMAPS_PER_PUBLISHER,
    DEFAULT_MAX_URLS_PER_PUBLISHER,
    DEFAULT_NEWS_LOOKBACK_DAYS,
    collect_news_sitemap_rows,
)
from phishing_url_ml.settings import DEFAULT_USER_AGENT, NEWS_SITEMAP_PUBLISHERS, RAW_DIR, SOURCE_CONFIGS
from phishing_url_ml.utils import ensure_parent_dir, log


def build_download_url(source_name: str) -> str:
    source = SOURCE_CONFIGS[source_name]
    if source_name != "phishtank":
        return source.url

    app_key = os.getenv("PHISHTANK_APP_KEY", "").strip()
    if not app_key:
        return source.url
    return source.url.replace("/data/", f"/data/{app_key}/", 1)


def download_source(source_name: str, overwrite: bool) -> Path:
    source = SOURCE_CONFIGS[source_name]
    run_date = date.today().isoformat()
    output_path = RAW_DIR / source.raw_subdir / f"{source.name}_{run_date}{source.extension}"
    ensure_parent_dir(output_path)

    if output_path.exists() and not overwrite:
        log(f"Skipping {source_name}: {output_path.name} already exists")
        return output_path

    headers = {"User-Agent": DEFAULT_USER_AGENT}
    response = requests.get(build_download_url(source_name), headers=headers, timeout=(10, 120))
    response.raise_for_status()
    output_path.write_bytes(response.content)
    size_kb = output_path.stat().st_size / 1024
    log(f"Saved {source_name} raw file to {output_path} ({size_kb:.1f} KB)")
    return output_path


def download_news_sitemaps(
    overwrite: bool,
    publisher_names: list[str] | None,
    lookback_days: int,
    max_urls_per_publisher: int,
    max_sitemaps_per_publisher: int,
) -> Path:
    source = SOURCE_CONFIGS["news_sitemaps"]
    run_date = date.today().isoformat()
    output_path = RAW_DIR / source.raw_subdir / f"{source.name}_{run_date}{source.extension}"
    ensure_parent_dir(output_path)

    if output_path.exists() and not overwrite:
        log(f"Skipping news_sitemaps: {output_path.name} already exists")
        return output_path

    rows = collect_news_sitemap_rows(
        publisher_names=publisher_names,
        lookback_days=lookback_days,
        max_urls_per_publisher=max_urls_per_publisher,
        max_sitemaps_per_publisher=max_sitemaps_per_publisher,
    )
    output_path.write_text(json.dumps(rows, indent=2, ensure_ascii=True), encoding="utf-8")
    size_kb = output_path.stat().st_size / 1024
    log(f"Saved news_sitemaps raw file to {output_path} ({size_kb:.1f} KB, {len(rows):,} rows)")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download raw phishing and benign data feeds.")
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=sorted(SOURCE_CONFIGS),
        default=["tranco", "mendeley_phishing_url", "mendeley_legitphish"],
        help="Sources to download. OpenPhish is opt-in because its terms are stricter.",
    )
    parser.add_argument(
        "--include-openphish",
        action="store_true",
        help="Explicitly allow downloading the OpenPhish community feed.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite today's raw file if it already exists.",
    )
    parser.add_argument(
        "--news-publishers",
        nargs="+",
        choices=sorted(NEWS_SITEMAP_PUBLISHERS),
        help="Optional subset of news publishers used when downloading news_sitemaps.",
    )
    parser.add_argument(
        "--news-lookback-days",
        type=int,
        default=DEFAULT_NEWS_LOOKBACK_DAYS,
        help="How many recent publication days to keep from news sitemaps.",
    )
    parser.add_argument(
        "--news-max-urls-per-publisher",
        type=int,
        default=DEFAULT_MAX_URLS_PER_PUBLISHER,
        help="Cap benign news URLs collected per publisher per run.",
    )
    parser.add_argument(
        "--news-max-sitemaps-per-publisher",
        type=int,
        default=DEFAULT_MAX_SITEMAPS_PER_PUBLISHER,
        help="Cap sitemap files explored per publisher per run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    requested_sources = list(dict.fromkeys(args.sources))

    if "openphish" in requested_sources and not args.include_openphish:
        raise SystemExit(
            "OpenPhish download is disabled by default. Re-run with --include-openphish "
            "after confirming its terms fit your academic use case."
        )

    log(f"Starting raw downloads for sources: {', '.join(requested_sources)}")
    completed_sources: list[str] = []
    failed_sources: list[tuple[str, str]] = []
    for source_name in requested_sources:
        source = SOURCE_CONFIGS[source_name]
        if source.requires_opt_in and not args.include_openphish:
            log(f"Skipping {source_name}: explicit opt-in required")
            continue
        try:
            if source_name == "news_sitemaps":
                download_news_sitemaps(
                    overwrite=args.overwrite,
                    publisher_names=args.news_publishers,
                    lookback_days=args.news_lookback_days,
                    max_urls_per_publisher=args.news_max_urls_per_publisher,
                    max_sitemaps_per_publisher=args.news_max_sitemaps_per_publisher,
                )
            else:
                download_source(source_name, overwrite=args.overwrite)
            completed_sources.append(source_name)
        except requests.HTTPError as exc:
            response = exc.response
            if source_name == "phishtank" and response is not None and response.status_code == 429:
                message = (
                    "PhishTank returned 429 Too Many Requests. Wait and retry later, or register "
                    "an application key and set PHISHTANK_APP_KEY for stable automated downloads."
                )
            else:
                message = f"{type(exc).__name__}: {exc}"
            failed_sources.append((source_name, message))
            log(f"Failed to download {source_name}: {message}")
        except requests.RequestException as exc:
            message = f"{type(exc).__name__}: {exc}"
            failed_sources.append((source_name, message))
            log(f"Failed to download {source_name}: {message}")
        except ValueError as exc:
            message = f"{type(exc).__name__}: {exc}"
            failed_sources.append((source_name, message))
            log(f"Failed to download {source_name}: {message}")

    if not completed_sources and failed_sources:
        failure_text = "; ".join(f"{name} -> {message}" for name, message in failed_sources)
        raise SystemExit(f"Raw download failed for all requested sources: {failure_text}")

    if failed_sources:
        failure_text = "; ".join(f"{name} -> {message}" for name, message in failed_sources)
        log(f"Raw download completed with warnings: {failure_text}")
    else:
        log("Raw download step completed")


if __name__ == "__main__":
    main()
