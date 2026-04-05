from __future__ import annotations

import ipaddress
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import pandas as pd
import tldextract

from .settings import DEFAULT_PORTS, RAW_DIR, TRACKING_QUERY_PARAMS, VALID_URL_SCHEMES


DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")
DOMAIN_LABEL_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
INVALID_LITERAL_VALUES = {"", "-", "--", "---", "n/a", "na", "none", "null", "unknown"}
INVALID_SCHEME_PREFIXES = ("javascript:", "data:", "about:blank")
TLD_EXTRACTOR = tldextract.TLDExtract(suffix_list_urls=None)


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def clean_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def parse_date_from_filename(path: Path) -> str:
    match = DATE_PATTERN.search(path.name)
    if not match:
        raise ValueError(f"Could not find YYYY-MM-DD in filename: {path}")
    return match.group(1)


def raw_source_dirs(source: str) -> list[Path]:
    directories = [RAW_DIR / source]
    if source == "openphish":
        directories.append(RAW_DIR / "openphish_snapshots")
    return directories


def iter_raw_files(source: str, start_date: str | None = None, end_date: str | None = None) -> Iterable[Path]:
    selected_paths: list[Path] = []
    for source_dir in raw_source_dirs(source):
        if not source_dir.exists():
            continue

        for path in sorted(source_dir.glob(f"{source}_*")):
            try:
                collected_at = parse_date_from_filename(path)
            except ValueError:
                continue

            if start_date and collected_at < start_date:
                continue
            if end_date and collected_at > end_date:
                continue
            selected_paths.append(path)
    return selected_paths


def looks_like_ip(hostname: str) -> bool:
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


def canonicalize_domain(value: object) -> str | None:
    hostname = clean_text(value).lower().strip(".")
    if not hostname or hostname in INVALID_LITERAL_VALUES:
        return None
    if any(char.isspace() for char in hostname):
        return None
    try:
        hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError:
        return None
    hostname = hostname.strip(".").lower()
    return hostname or None


def is_valid_hostname(hostname: str | None) -> bool:
    if not hostname:
        return False
    if looks_like_ip(hostname):
        return True
    if len(hostname) > 253 or "." not in hostname:
        return False

    labels = hostname.split(".")
    for label in labels:
        if not DOMAIN_LABEL_PATTERN.fullmatch(label):
            return False
    return True


def extract_domain_parts(hostname: str | None) -> dict[str, str]:
    empty = {
        "subdomain": "",
        "domain": "",
        "suffix": "",
        "registered_domain": "",
    }
    if not hostname:
        return empty
    if looks_like_ip(hostname):
        return {
            "subdomain": "",
            "domain": hostname,
            "suffix": "",
            "registered_domain": hostname,
        }

    extracted = TLD_EXTRACTOR(hostname)
    registered_domain = getattr(extracted, "top_domain_under_public_suffix", "") or ".".join(
        part for part in [extracted.domain, extracted.suffix] if part
    )
    return {
        "subdomain": extracted.subdomain or "",
        "domain": extracted.domain or "",
        "suffix": extracted.suffix or "",
        "registered_domain": registered_domain or "",
    }


def canonicalize_url(value: object) -> str | None:
    raw_url = clean_text(value)
    if not raw_url:
        return None
    lowered = raw_url.lower()
    if lowered.startswith(INVALID_SCHEME_PREFIXES):
        return None

    try:
        parsed = urlparse(raw_url)
    except ValueError:
        return None
    scheme = (parsed.scheme or "").lower()
    if scheme not in VALID_URL_SCHEMES:
        return None

    hostname = canonicalize_domain(parsed.hostname)
    if not hostname or not is_valid_hostname(hostname):
        return None

    try:
        port = parsed.port
    except ValueError:
        return None

    netloc = hostname
    if port and port != DEFAULT_PORTS.get(scheme):
        netloc = f"{hostname}:{port}"

    path = parsed.path or "/"
    if not path.startswith("/"):
        path = f"/{path}"

    query_pairs = [
        (key, val)
        for key, val in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in TRACKING_QUERY_PARAMS
    ]
    query_pairs.sort(key=lambda item: (item[0], item[1]))
    query = urlencode(query_pairs, doseq=True)

    return urlunparse((scheme, netloc, path, "", query, ""))


def build_parsed_record(original_value: object, record_type: object) -> dict[str, object]:
    base = {
        "scheme": "",
        "hostname": "",
        "subdomain": "",
        "domain": "",
        "suffix": "",
        "registered_domain": "",
        "path": "",
        "query": "",
        "fragment": "",
        "is_ip_host": 0,
        "canonical_domain": "",
        "canonical_hostname": "",
        "canonical_registered_domain": "",
        "canonical_url": "",
        "parse_ok": False,
        "invalid_reason": "",
    }

    value = clean_text(original_value)
    normalized_record_type = clean_text(record_type).lower()
    if not value or value.lower() in INVALID_LITERAL_VALUES:
        base["invalid_reason"] = "empty_value"
        return base
    if normalized_record_type not in {"domain", "url"}:
        base["invalid_reason"] = "unknown_record_type"
        return base

    if normalized_record_type == "domain":
        hostname = canonicalize_domain(value)
        if not hostname:
            base["invalid_reason"] = "invalid_domain"
            return base
        if not is_valid_hostname(hostname):
            base["invalid_reason"] = "invalid_hostname"
            return base

        parts = extract_domain_parts(hostname)
        base.update(
            {
                "hostname": hostname,
                "subdomain": parts["subdomain"],
                "domain": parts["domain"],
                "suffix": parts["suffix"],
                "registered_domain": parts["registered_domain"],
                "is_ip_host": int(looks_like_ip(hostname)),
                "canonical_domain": hostname,
                "canonical_hostname": hostname,
                "canonical_registered_domain": parts["registered_domain"],
                "parse_ok": True,
            }
        )
        return base

    lowered = value.lower()
    if lowered.startswith(INVALID_SCHEME_PREFIXES):
        base["invalid_reason"] = "unsupported_scheme"
        return base

    try:
        parsed = urlparse(value)
    except ValueError:
        base["invalid_reason"] = "invalid_url_parse"
        return base
    scheme = (parsed.scheme or "").lower()
    if scheme not in VALID_URL_SCHEMES:
        base["invalid_reason"] = "unsupported_scheme"
        return base

    hostname = canonicalize_domain(parsed.hostname)
    if not hostname:
        base["invalid_reason"] = "missing_hostname"
        return base
    if not is_valid_hostname(hostname):
        base["invalid_reason"] = "invalid_hostname"
        return base

    canonical_url = canonicalize_url(value)
    if not canonical_url:
        base["invalid_reason"] = "invalid_url"
        return base

    parts = extract_domain_parts(hostname)
    base.update(
        {
            "scheme": scheme,
            "hostname": hostname,
            "subdomain": parts["subdomain"],
            "domain": parts["domain"],
            "suffix": parts["suffix"],
            "registered_domain": parts["registered_domain"],
            "path": parsed.path or "/",
            "query": parsed.query or "",
            "fragment": parsed.fragment or "",
            "is_ip_host": int(looks_like_ip(hostname)),
            "canonical_domain": hostname,
            "canonical_hostname": hostname,
            "canonical_registered_domain": parts["registered_domain"],
            "canonical_url": canonical_url,
            "parse_ok": True,
        }
    )
    return base


def require_columns(df: pd.DataFrame, columns: Iterable[str], dataset_name: str) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"{dataset_name} is missing required columns: {missing_text}")


def write_json(path: Path, payload: dict[str, object]) -> None:
    ensure_parent_dir(path)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
