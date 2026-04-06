from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RUNTIME_DIR = DATA_DIR / "runtime"
MODELS_DIR = BASE_DIR / "models"
IDS_EVENTS_PATH = RUNTIME_DIR / "ids_events.jsonl"
OFFICIAL_MODEL_REGISTRY_PATH = MODELS_DIR / "official_model_registry.json"

DEFAULT_USER_AGENT = "DoAnCoSo/0.1 (academic phishing URL ML project)"
VALID_URL_SCHEMES = {"http", "https"}
DEFAULT_PORTS = {"http": 80, "https": 443}
TRACKING_QUERY_PARAMS = {
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "msclkid",
    "ref",
    "ref_src",
    "source",
    "spm",
    "utm_campaign",
    "utm_content",
    "utm_id",
    "utm_medium",
    "utm_name",
    "utm_source",
    "utm_term",
    "yclid",
}
NEWS_SITEMAP_FALLBACK_PATHS = (
    "/news-sitemap.xml",
    "/news_sitemap.xml",
    "/news.xml",
    "/sitemap-news.xml",
    "/sitemap_news.xml",
    "/sitemap.xml",
    "/sitemap_index.xml",
)
NEWS_URL_BLOCKLIST_TOKENS = {
    "/amp",
    "/author/",
    "/authors/",
    "/category/",
    "/categories/",
    "/live/",
    "/podcast/",
    "/podcasts/",
    "/profile/",
    "/profiles/",
    "/search",
    "/section/",
    "/sections/",
    "/tag/",
    "/tags/",
    "/topic/",
    "/topics/",
    "/video/",
    "/videos/",
    "account",
    "login",
    "newsletter",
    "register",
    "signin",
    "signup",
    "subscribe",
}
NEWS_URL_BLOCKLIST_EXTENSIONS = {
    ".css",
    ".csv",
    ".gif",
    ".jpeg",
    ".jpg",
    ".js",
    ".json",
    ".mp3",
    ".mp4",
    ".pdf",
    ".png",
    ".rss",
    ".svg",
    ".txt",
    ".xml",
    ".zip",
}


@dataclass(frozen=True)
class SourceConfig:
    name: str
    url: str
    raw_subdir: str
    extension: str
    enabled_by_default: bool = True
    requires_opt_in: bool = False
    published_date: str | None = None
    notes: str = ""


@dataclass(frozen=True)
class NewsPublisherConfig:
    name: str
    base_url: str
    notes: str = ""


SOURCE_CONFIGS = {
    "phishtank": SourceConfig(
        name="phishtank",
        url="http://data.phishtank.com/data/online-valid.json",
        raw_subdir="phishtank",
        extension=".json",
        enabled_by_default=True,
        notes=(
            "Official PhishTank feed. For automated use at scale, register an app key "
            "and set PHISHTANK_APP_KEY."
        ),
    ),
    "openphish": SourceConfig(
        name="openphish",
        url="https://openphish.com/feed.txt",
        raw_subdir="openphish",
        extension=".txt",
        enabled_by_default=False,
        requires_opt_in=True,
        notes=(
            "OpenPhish terms state the community service is for personal use. "
            "Academic work may qualify for the Academic Use Program."
        ),
    ),
    "mendeley_phishing_url": SourceConfig(
        name="mendeley_phishing_url",
        url="https://data.mendeley.com/public-api/zip/vfszbj9b36/download/1",
        raw_subdir="mendeley_phishing_url",
        extension=".zip",
        enabled_by_default=True,
        published_date="2024-04-02",
        notes=(
            "Mendeley Data dataset 'Phishing URL dataset' DOI 10.17632/vfszbj9b36.1, "
            "licensed CC BY 4.0."
        ),
    ),
    "mendeley_legitphish": SourceConfig(
        name="mendeley_legitphish",
        url="https://data.mendeley.com/public-api/zip/hx4m73v2sf/download/1",
        raw_subdir="mendeley_legitphish",
        extension=".zip",
        enabled_by_default=True,
        published_date="2025-04-07",
        notes=(
            "Mendeley Data dataset 'LegitPhish Dataset' DOI 10.17632/hx4m73v2sf.1, "
            "licensed CC BY 4.0."
        ),
    ),
    "tranco": SourceConfig(
        name="tranco",
        url="https://tranco-list.eu/top-1m.csv.zip",
        raw_subdir="tranco",
        extension=".csv.zip",
        enabled_by_default=True,
        notes="Official latest Tranco top 1M list.",
    ),
    "news_sitemaps": SourceConfig(
        name="news_sitemaps",
        url="",
        raw_subdir="news_sitemaps",
        extension=".json",
        enabled_by_default=False,
        notes=(
            "Collected benign URL candidates from official publisher news sitemaps. "
            "URLs are weak-labeled as benign after overlap filtering."
        ),
    ),
}

NEWS_SITEMAP_PUBLISHERS = {
    "apnews": NewsPublisherConfig(
        name="apnews",
        base_url="https://apnews.com",
        notes="Associated Press official website.",
    ),
    "bbc": NewsPublisherConfig(
        name="bbc",
        base_url="https://www.bbc.com",
        notes="BBC official website.",
    ),
    "npr": NewsPublisherConfig(
        name="npr",
        base_url="https://www.npr.org",
        notes="NPR official website.",
    ),
    "reuters": NewsPublisherConfig(
        name="reuters",
        base_url="https://www.reuters.com",
        notes="Reuters official website.",
    ),
    "vnexpress": NewsPublisherConfig(
        name="vnexpress",
        base_url="https://vnexpress.net",
        notes="VNExpress official website.",
    ),
}
DEFAULT_NEWS_SITEMAP_PUBLISHERS = ("apnews", "npr", "reuters")
