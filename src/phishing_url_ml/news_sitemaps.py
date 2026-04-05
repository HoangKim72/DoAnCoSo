from __future__ import annotations

import gzip
import re
from datetime import date, datetime, timedelta
from typing import Iterable
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET

import requests

from .settings import (
    DEFAULT_NEWS_SITEMAP_PUBLISHERS,
    DEFAULT_USER_AGENT,
    NEWS_SITEMAP_FALLBACK_PATHS,
    NEWS_SITEMAP_PUBLISHERS,
    NEWS_URL_BLOCKLIST_EXTENSIONS,
    NEWS_URL_BLOCKLIST_TOKENS,
)
from .utils import canonicalize_domain, extract_domain_parts, log


DEFAULT_NEWS_LOOKBACK_DAYS = 7
DEFAULT_MAX_URLS_PER_PUBLISHER = 500
DEFAULT_MAX_SITEMAPS_PER_PUBLISHER = 25
UNESCAPED_AMPERSAND_PATTERN = re.compile(r"&(?!amp;|apos;|gt;|lt;|quot;|#\d+;|#x[0-9A-Fa-f]+;)")


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _unique_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            unique_values.append(value)
    return unique_values


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"

    for candidate in (
        cleaned,
        cleaned[:19],
        cleaned[:10],
    ):
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is not None:
                return parsed.astimezone().replace(tzinfo=None)
            return parsed
        except ValueError:
            continue
    return None


def _extract_date_text(*values: str | None) -> str | None:
    for value in values:
        parsed = _parse_datetime(value)
        if parsed is not None:
            return parsed.date().isoformat()
    return None


def _looks_recent(*values: str | None, today: date, lookback_days: int) -> bool:
    threshold = today - timedelta(days=lookback_days)
    for value in values:
        parsed = _parse_datetime(value)
        if parsed is not None and parsed.date() >= threshold:
            return True
    return False


def _fetch_text(session: requests.Session, url: str) -> str:
    response = session.get(url, timeout=(10, 60))
    response.raise_for_status()

    content = response.content
    if url.lower().endswith(".gz") or "gzip" in response.headers.get("Content-Type", "").lower():
        try:
            content = gzip.decompress(content)
        except OSError:
            pass

    encoding = response.encoding or "utf-8"
    return content.decode(encoding, errors="replace")


def _discover_root_sitemaps(session: requests.Session, base_url: str) -> list[str]:
    parsed_base = urlparse(base_url)
    robots_url = f"{parsed_base.scheme}://{parsed_base.netloc}/robots.txt"
    discovered: list[str] = []

    try:
        robots_text = _fetch_text(session, robots_url)
        for line in robots_text.splitlines():
            if line.lower().startswith("sitemap:"):
                discovered.append(line.split(":", 1)[1].strip())
    except requests.RequestException as exc:
        log(f"Could not read robots.txt for {base_url}: {type(exc).__name__}: {exc}")

    if not discovered:
        for fallback_path in NEWS_SITEMAP_FALLBACK_PATHS:
            discovered.append(urljoin(base_url.rstrip("/") + "/", fallback_path.lstrip("/")))
    return _unique_preserve_order(discovered)


def _find_text(element: ET.Element, local_name: str) -> str:
    for child in element.iter():
        if _local_name(child.tag) == local_name and child.text:
            return child.text.strip()
    return ""


def _parse_sitemap_document(xml_text: str) -> tuple[str, list[dict[str, str]]]:
    cleaned_text = xml_text.lstrip("\ufeff")
    if "<" in cleaned_text:
        cleaned_text = cleaned_text[cleaned_text.find("<") :]
    cleaned_text = UNESCAPED_AMPERSAND_PATTERN.sub("&amp;", cleaned_text)
    root = ET.fromstring(cleaned_text)
    root_name = _local_name(root.tag)

    if root_name == "sitemapindex":
        items: list[dict[str, str]] = []
        for child in root:
            if _local_name(child.tag) != "sitemap":
                continue
            items.append({"loc": _find_text(child, "loc"), "lastmod": _find_text(child, "lastmod")})
        return "index", items

    if root_name == "urlset":
        items = []
        for child in root:
            if _local_name(child.tag) != "url":
                continue
            items.append(
                {
                    "loc": _find_text(child, "loc"),
                    "lastmod": _find_text(child, "lastmod"),
                    "publication_date": _find_text(child, "publication_date"),
                    "title": _find_text(child, "title"),
                }
            )
        return "urlset", items

    raise ValueError(f"Unsupported sitemap root element: {root_name}")


def _select_child_sitemaps(entries: list[dict[str, str]], today: date, lookback_days: int, max_items: int) -> list[str]:
    scored_entries: list[tuple[int, str]] = []
    for entry in entries:
        loc = entry.get("loc", "").strip()
        if not loc:
            continue
        lowered_loc = loc.lower()
        score = 0
        if "news" in lowered_loc:
            score += 4
        if any(token in lowered_loc for token in ("article", "articles", "post", "posts")):
            score += 2
        if _looks_recent(entry.get("lastmod"), today=today, lookback_days=lookback_days):
            score += 1
        scored_entries.append((score, loc))

    if not scored_entries:
        return []

    scored_entries.sort(key=lambda item: (item[0], item[1]), reverse=True)
    selected = [loc for score, loc in scored_entries if score > 0]
    if not selected:
        selected = [loc for _, loc in scored_entries[:max_items]]
    return _unique_preserve_order(selected[:max_items])


def _is_allowed_news_url(url: str, publisher_base_url: str) -> bool:
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"}:
        return False

    hostname = canonicalize_domain(parsed_url.hostname)
    publisher_host = canonicalize_domain(urlparse(publisher_base_url).hostname)
    if not hostname or not publisher_host:
        return False

    publisher_domain = extract_domain_parts(publisher_host)["registered_domain"] or publisher_host
    candidate_domain = extract_domain_parts(hostname)["registered_domain"] or hostname
    if candidate_domain != publisher_domain:
        return False

    path = parsed_url.path or "/"
    if path in {"", "/"}:
        return False

    lowered_url = url.lower()
    lowered_path = path.lower()
    if any(token in lowered_url for token in NEWS_URL_BLOCKLIST_TOKENS):
        return False
    if any(lowered_path.endswith(extension) for extension in NEWS_URL_BLOCKLIST_EXTENSIONS):
        return False
    if lowered_path.endswith("/rss"):
        return False
    return True


def collect_news_sitemap_rows(
    publisher_names: list[str] | None = None,
    lookback_days: int = DEFAULT_NEWS_LOOKBACK_DAYS,
    max_urls_per_publisher: int = DEFAULT_MAX_URLS_PER_PUBLISHER,
    max_sitemaps_per_publisher: int = DEFAULT_MAX_SITEMAPS_PER_PUBLISHER,
) -> list[dict[str, str]]:
    selected_publishers = publisher_names or list(DEFAULT_NEWS_SITEMAP_PUBLISHERS)
    missing_publishers = [name for name in selected_publishers if name not in NEWS_SITEMAP_PUBLISHERS]
    if missing_publishers:
        raise ValueError(f"Unknown news sitemap publishers: {', '.join(sorted(missing_publishers))}")

    today = date.today()
    session = requests.Session()
    session.headers.update({"User-Agent": DEFAULT_USER_AGENT})

    all_rows: list[dict[str, str]] = []
    for publisher_name in selected_publishers:
        publisher = NEWS_SITEMAP_PUBLISHERS[publisher_name]
        discovered_sitemaps = _discover_root_sitemaps(session, publisher.base_url)
        queue = discovered_sitemaps[:]
        visited: set[str] = set()
        kept_urls: set[str] = set()
        publisher_rows: list[dict[str, str]] = []

        while queue and len(visited) < max_sitemaps_per_publisher and len(publisher_rows) < max_urls_per_publisher:
            sitemap_url = queue.pop(0)
            if sitemap_url in visited:
                continue
            visited.add(sitemap_url)

            try:
                xml_text = _fetch_text(session, sitemap_url)
                doc_type, items = _parse_sitemap_document(xml_text)
            except (requests.RequestException, ET.ParseError, ValueError) as exc:
                log(f"Skipping sitemap {sitemap_url}: {type(exc).__name__}: {exc}")
                continue

            if doc_type == "index":
                children = _select_child_sitemaps(
                    items,
                    today=today,
                    lookback_days=lookback_days,
                    max_items=max_sitemaps_per_publisher,
                )
                for child_url in children:
                    if child_url not in visited:
                        queue.append(child_url)
                continue

            for item in items:
                url = item.get("loc", "").strip()
                if not url or url in kept_urls:
                    continue
                if not _is_allowed_news_url(url, publisher.base_url):
                    continue
                if not _looks_recent(
                    item.get("publication_date"),
                    item.get("lastmod"),
                    today=today,
                    lookback_days=lookback_days,
                ):
                    continue

                collected_date = _extract_date_text(item.get("publication_date"), item.get("lastmod")) or today.isoformat()
                publisher_rows.append(
                    {
                        "url": url,
                        "publisher": publisher_name,
                        "publisher_base_url": publisher.base_url,
                        "sitemap_url": sitemap_url,
                        "publication_date": item.get("publication_date", ""),
                        "lastmod": item.get("lastmod", ""),
                        "title": item.get("title", ""),
                        "collected_at": collected_date,
                    }
                )
                kept_urls.add(url)
                if len(publisher_rows) >= max_urls_per_publisher:
                    break

        log(
            f"Collected {len(publisher_rows):,} benign news URL candidates from "
            f"{publisher_name} across {len(visited):,} sitemap files"
        )
        all_rows.extend(publisher_rows)

    return all_rows
