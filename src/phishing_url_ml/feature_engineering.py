from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache

import pandas as pd


SENSITIVE_KEYWORDS = (
    "account",
    "admin",
    "auth",
    "bank",
    "billing",
    "bonus",
    "claim",
    "confirm",
    "gift",
    "invoice",
    "login",
    "mfa",
    "oauth",
    "password",
    "payment",
    "recover",
    "reset",
    "secure",
    "service",
    "session",
    "signin",
    "support",
    "token",
    "unlock",
    "update",
    "verify",
    "wallet",
    "webscr",
)

TOP_BRANDS = (
    "adobe",
    "amazon",
    "amex",
    "apple",
    "bankofamerica",
    "binance",
    "chase",
    "citi",
    "coinbase",
    "dhl",
    "docusign",
    "dropbox",
    "facebook",
    "fedex",
    "google",
    "icloud",
    "instagram",
    "microsoft",
    "netflix",
    "office365",
    "outlook",
    "paypal",
    "roblox",
    "shopee",
    "telegram",
    "usps",
    "whatsapp",
)

TLD_RISK_SCORES = {
    "buzz": 0.6,
    "cam": 0.5,
    "cf": 1.0,
    "click": 0.8,
    "country": 0.5,
    "fit": 0.5,
    "ga": 1.0,
    "gq": 1.0,
    "live": 0.6,
    "ml": 1.0,
    "mom": 0.5,
    "monster": 0.6,
    "online": 0.7,
    "quest": 0.5,
    "rest": 0.6,
    "run": 0.5,
    "shop": 0.7,
    "site": 0.7,
    "support": 0.5,
    "tk": 1.0,
    "today": 0.5,
    "top": 0.8,
    "vip": 0.6,
    "work": 0.6,
    "xyz": 0.8,
}

TOKEN_SPLIT_PATTERN = re.compile(r"[^a-z0-9]+")
CONSONANT_RUN_PATTERN = re.compile(r"[bcdfghjklmnpqrstvwxyz]+")
PUNYCODE_PATTERN = re.compile(r"(^|[.-])xn--")
MAX_BRAND_LENGTH = max(len(brand) for brand in TOP_BRANDS)


def _get_text_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series("", index=df.index, dtype="string")
    return df[column].fillna("").astype("string")


def _shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    length = len(text)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def _safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace(0, 1)
    return numerator / denominator


@lru_cache(maxsize=200_000)
def _tokenize_text(text: str) -> tuple[str, ...]:
    normalized = TOKEN_SPLIT_PATTERN.sub(" ", text.lower())
    return tuple(token for token in normalized.split() if token)


@lru_cache(maxsize=200_000)
def _contains_brand_name(text: str) -> int:
    lowered = text.lower()
    return int(any(brand in lowered for brand in TOP_BRANDS))


@lru_cache(maxsize=200_000)
def _contains_sensitive_keyword(text: str) -> int:
    lowered = text.lower()
    return int(any(keyword in lowered for keyword in SENSITIVE_KEYWORDS))


@lru_cache(maxsize=200_000)
def _count_sensitive_keywords(text: str) -> int:
    lowered = text.lower()
    return sum(keyword in lowered for keyword in SENSITIVE_KEYWORDS)


@lru_cache(maxsize=200_000)
def _levenshtein_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous_row = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current_row = [i]
        for j, right_char in enumerate(right, start=1):
            insert_cost = current_row[j - 1] + 1
            delete_cost = previous_row[j] + 1
            replace_cost = previous_row[j - 1] + (left_char != right_char)
            current_row.append(min(insert_cost, delete_cost, replace_cost))
        previous_row = current_row
    return previous_row[-1]


@lru_cache(maxsize=200_000)
def _min_edit_distance_to_top_brand(text: str) -> float:
    tokens = _tokenize_text(text)
    if not tokens:
        return float(MAX_BRAND_LENGTH)
    return float(min(_levenshtein_distance(token, brand) for token in tokens for brand in TOP_BRANDS))


@lru_cache(maxsize=200_000)
def _brand_position_score(text: str) -> float:
    lowered = text.lower()
    positions = [lowered.find(brand) for brand in TOP_BRANDS if brand in lowered]
    if not positions:
        return 0.0
    earliest = min(position for position in positions if position >= 0)
    denominator = max(1, len(lowered) - 1)
    return float(1.0 - (earliest / denominator))


@lru_cache(maxsize=200_000)
def _consonant_run_max(text: str) -> float:
    lowered = text.lower()
    matches = CONSONANT_RUN_PATTERN.findall(lowered)
    return float(max((len(match) for match in matches), default=0))


@lru_cache(maxsize=200_000)
def _char_repeat_ratio(text: str) -> float:
    lowered = text.lower()
    if not lowered:
        return 0.0
    repeat_count = sum(1 for index in range(1, len(lowered)) if lowered[index] == lowered[index - 1])
    return repeat_count / len(lowered)


@lru_cache(maxsize=200_000)
def _subdomain_count(text: str) -> int:
    return len([part for part in text.split(".") if part]) if text else 0


@lru_cache(maxsize=200_000)
def _num_tokens_domain(text: str) -> int:
    return len(_tokenize_text(text))


@lru_cache(maxsize=200_000)
def _tld_risk_score(suffix: str) -> float:
    return float(TLD_RISK_SCORES.get(suffix.lower(), 0.0))


@lru_cache(maxsize=200_000)
def _is_idn_or_punycode(text: str) -> int:
    return int(bool(PUNYCODE_PATTERN.search(text.lower())))


def build_domain_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    hostname = _get_text_series(df, "hostname")
    registered_domain = _get_text_series(df, "registered_domain")
    subdomain = _get_text_series(df, "subdomain")
    suffix = _get_text_series(df, "suffix")

    features = pd.DataFrame(index=df.index)
    features["domain_length"] = hostname.str.len()
    features["subdomain_count"] = subdomain.apply(_subdomain_count)
    features["num_tokens_domain"] = hostname.apply(_num_tokens_domain)
    features["num_hyphens"] = hostname.str.count("-")
    digit_count = hostname.str.count(r"\d")
    features["digit_ratio"] = _safe_ratio(digit_count, features["domain_length"])
    features["entropy_domain"] = hostname.apply(_shannon_entropy)
    features["contains_brand_name"] = hostname.apply(_contains_brand_name)
    features["contains_sensitive_keyword"] = hostname.apply(_contains_sensitive_keyword)
    features["edit_distance_to_top_brand"] = hostname.apply(_min_edit_distance_to_top_brand)
    features["tld_risk_score"] = suffix.apply(_tld_risk_score)
    features["brand_position_score"] = hostname.apply(_brand_position_score)
    features["registered_domain_length"] = registered_domain.str.len()
    features["consonant_run_max"] = hostname.apply(_consonant_run_max)
    features["char_repeat_ratio"] = hostname.apply(_char_repeat_ratio)
    features["is_idn_or_punycode"] = hostname.apply(_is_idn_or_punycode)
    return features.astype(float)


def build_url_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    sample = _get_text_series(df, "sample_text")
    hostname = _get_text_series(df, "hostname")
    registered_domain = _get_text_series(df, "registered_domain")
    subdomain = _get_text_series(df, "subdomain")
    path = _get_text_series(df, "path")
    query = _get_text_series(df, "query")
    fragment = _get_text_series(df, "fragment")
    scheme = _get_text_series(df, "scheme")
    is_ip_host = pd.to_numeric(df.get("is_ip_host", 0), errors="coerce").fillna(0).astype(int)

    features = pd.DataFrame(index=df.index)
    features["sample_length"] = sample.str.len()
    features["hostname_length"] = hostname.str.len()
    features["registered_domain_length"] = registered_domain.str.len()
    features["subdomain_length"] = subdomain.str.len()
    features["path_length"] = path.str.len()
    features["query_length"] = query.str.len()
    features["fragment_length"] = fragment.str.len()

    features["dot_count"] = sample.str.count(r"\.")
    features["hyphen_count"] = sample.str.count("-")
    features["underscore_count"] = sample.str.count("_")
    features["slash_count"] = sample.str.count("/")
    features["digit_count"] = sample.str.count(r"\d")
    features["question_mark_count"] = sample.str.count(r"\?")
    features["ampersand_count"] = sample.str.count("&")
    features["equal_count"] = sample.str.count("=")
    features["at_count"] = sample.str.count("@")
    features["percent_count"] = sample.str.count("%")
    features["tilde_count"] = sample.str.count("~")
    features["colon_count"] = sample.str.count(":")

    features["alpha_count"] = sample.str.count(r"[A-Za-z]")
    features["alnum_count"] = sample.str.count(r"[A-Za-z0-9]")
    features["special_char_count"] = features["sample_length"] - features["alnum_count"]
    features["digit_ratio"] = _safe_ratio(features["digit_count"], features["sample_length"])
    features["special_char_ratio"] = _safe_ratio(features["special_char_count"], features["sample_length"])
    features["unique_char_ratio"] = sample.apply(lambda text: len(set(text)) / len(text) if text else 0.0)
    features["sample_entropy"] = sample.apply(_shannon_entropy)
    features["hostname_entropy"] = hostname.apply(_shannon_entropy)

    features["subdomain_depth"] = subdomain.apply(_subdomain_count)
    features["path_depth"] = path.apply(lambda text: len([part for part in text.split("/") if part]) if text else 0)
    features["query_param_count"] = query.apply(lambda text: 0 if not text else text.count("&") + 1)

    features["suspicious_token_count"] = sample.apply(_count_sensitive_keywords)
    features["has_https_token_in_host"] = hostname.str.contains("https", case=False, regex=False).astype(int)
    features["uses_http_scheme"] = scheme.str.lower().eq("http").astype(int)
    features["uses_https_scheme"] = scheme.str.lower().eq("https").astype(int)
    features["has_fragment"] = fragment.ne("").astype(int)
    features["has_query"] = query.ne("").astype(int)
    features["has_ip_host"] = is_ip_host

    return features.astype(float)


def build_feature_frame(df: pd.DataFrame, dataset_kind: str) -> pd.DataFrame:
    if dataset_kind == "domain":
        return build_domain_feature_frame(df)
    if dataset_kind == "url":
        return build_url_feature_frame(df)
    raise ValueError(f"Unsupported dataset_kind: {dataset_kind}")


def build_lexical_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    return build_url_feature_frame(df)
