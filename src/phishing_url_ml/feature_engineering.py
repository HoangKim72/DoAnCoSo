from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache
from urllib.parse import parse_qsl, urlparse

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
DIGIT_RUN_PATTERN = re.compile(r"\d+")
PERCENT_ENCODED_PATTERN = re.compile(r"%[0-9a-fA-F]{2}")
BASE64_LIKE_VALUE_PATTERN = re.compile(r"^[A-Za-z0-9+/_=-]{16,}$")
MAX_BRAND_LENGTH = max(len(brand) for brand in TOP_BRANDS)
BRAND_LIKE_SIMILARITY_THRESHOLD = 0.8

LOGIN_PATH_KEYWORDS = (
    "auth",
    "login",
    "logon",
    "signin",
    "signon",
    "sso",
)

VERIFY_PATH_KEYWORDS = (
    "confirm",
    "validate",
    "verification",
    "verify",
)

REDIRECT_QUERY_KEYS = {
    "callback",
    "continue",
    "dest",
    "destination",
    "goto",
    "next",
    "redir",
    "redirect",
    "redirect_to",
    "redirect_uri",
    "redirect_url",
    "return",
    "return_to",
    "returnurl",
    "return_url",
    "target",
    "url",
}


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
def _count_tokens_matching_keywords(text: str, keywords: tuple[str, ...]) -> int:
    tokens = _tokenize_text(text)
    return sum(any(keyword in token for keyword in keywords) for token in tokens)


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
def _brand_similarity_ratio(token: str, brand: str) -> float:
    if not token or not brand:
        return 0.0
    distance = _levenshtein_distance(token, brand)
    denominator = max(len(token), len(brand), 1)
    return max(0.0, 1.0 - (distance / denominator))


@lru_cache(maxsize=200_000)
def _closest_brand_similarity_ratio_for_token(token: str) -> float:
    if len(token) < 4:
        return 0.0
    return max(_brand_similarity_ratio(token, brand) for brand in TOP_BRANDS)


@lru_cache(maxsize=200_000)
def _closest_brand_similarity_ratio(text: str) -> float:
    tokens = _tokenize_text(text)
    if not tokens:
        return 0.0
    return max(_closest_brand_similarity_ratio_for_token(token) for token in tokens)


@lru_cache(maxsize=200_000)
def _brand_like_token_count(text: str) -> int:
    tokens = _tokenize_text(text)
    return sum(
        BRAND_LIKE_SIMILARITY_THRESHOLD <= _closest_brand_similarity_ratio_for_token(token) < 1.0
        for token in tokens
    )


@lru_cache(maxsize=200_000)
def _num_brand_mentions(text: str) -> int:
    tokens = _tokenize_text(text)
    return sum(any(brand in token for brand in TOP_BRANDS) for token in tokens)


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
def _avg_token_length(text: str) -> float:
    tokens = _tokenize_text(text)
    if not tokens:
        return 0.0
    return sum(len(token) for token in tokens) / len(tokens)


@lru_cache(maxsize=200_000)
def _max_token_length(text: str) -> float:
    tokens = _tokenize_text(text)
    return float(max((len(token) for token in tokens), default=0))


@lru_cache(maxsize=200_000)
def _mixed_alnum_token_count(text: str) -> int:
    tokens = _tokenize_text(text)
    return sum(any(char.isalpha() for char in token) and any(char.isdigit() for char in token) for token in tokens)


@lru_cache(maxsize=200_000)
def _token_entropy_max(text: str) -> float:
    tokens = _tokenize_text(text)
    return float(max((_shannon_entropy(token) for token in tokens), default=0.0))


@lru_cache(maxsize=200_000)
def _consecutive_digit_run_max(text: str) -> float:
    matches = DIGIT_RUN_PATTERN.findall(text)
    return float(max((len(match) for match in matches), default=0))


@lru_cache(maxsize=200_000)
def _tld_risk_score(suffix: str) -> float:
    return float(TLD_RISK_SCORES.get(suffix.lower(), 0.0))


@lru_cache(maxsize=200_000)
def _is_idn_or_punycode(text: str) -> int:
    return int(bool(PUNYCODE_PATTERN.search(text.lower())))


@lru_cache(maxsize=200_000)
def _split_path_segments(text: str) -> tuple[str, ...]:
    return tuple(segment for segment in text.lower().split("/") if segment)


@lru_cache(maxsize=200_000)
def _path_tokens(text: str) -> tuple[str, ...]:
    segments = _split_path_segments(text)
    tokens: list[str] = []
    for segment in segments:
        tokens.extend(_tokenize_text(segment))
    return tuple(tokens)


@lru_cache(maxsize=200_000)
def _avg_path_segment_length(text: str) -> float:
    segments = _split_path_segments(text)
    if not segments:
        return 0.0
    return sum(len(segment) for segment in segments) / len(segments)


@lru_cache(maxsize=200_000)
def _max_path_segment_length(text: str) -> float:
    segments = _split_path_segments(text)
    return float(max((len(segment) for segment in segments), default=0))


@lru_cache(maxsize=200_000)
def _num_numeric_segments(text: str) -> int:
    return sum(segment.isdigit() for segment in _split_path_segments(text))


@lru_cache(maxsize=200_000)
def _num_mixed_segments(text: str) -> int:
    segments = _split_path_segments(text)
    return sum(any(char.isalpha() for char in segment) and any(char.isdigit() for char in segment) for segment in segments)


@lru_cache(maxsize=200_000)
def _path_entropy(text: str) -> float:
    normalized = "".join(_split_path_segments(text))
    return _shannon_entropy(normalized)


@lru_cache(maxsize=200_000)
def _path_has_keyword(text: str, keywords: tuple[str, ...]) -> int:
    tokens = _path_tokens(text)
    return int(any(any(keyword in token for keyword in keywords) for token in tokens))


@lru_cache(maxsize=200_000)
def _path_has_brand_segment(text: str) -> int:
    tokens = _path_tokens(text)
    return int(any(any(brand in token for brand in TOP_BRANDS) for token in tokens))


@lru_cache(maxsize=200_000)
def _parse_query_pairs(text: str) -> tuple[tuple[str, str], ...]:
    if not text:
        return ()
    return tuple(parse_qsl(text, keep_blank_values=True))


@lru_cache(maxsize=200_000)
def _query_key_count(text: str) -> int:
    pairs = _parse_query_pairs(text)
    return len({key.lower() for key, _ in pairs if key})


@lru_cache(maxsize=200_000)
def _query_value_length_max(text: str) -> float:
    pairs = _parse_query_pairs(text)
    return float(max((len(value) for _, value in pairs), default=0))


@lru_cache(maxsize=200_000)
def _percent_encoded_ratio(text: str) -> float:
    if not text:
        return 0.0
    encoded_triplets = len(PERCENT_ENCODED_PATTERN.findall(text))
    return (encoded_triplets * 3) / len(text)


@lru_cache(maxsize=200_000)
def _redirect_param_count(text: str) -> int:
    pairs = _parse_query_pairs(text)
    return sum(key.lower() in REDIRECT_QUERY_KEYS for key, _ in pairs if key)


@lru_cache(maxsize=200_000)
def _has_redirect_param(text: str) -> int:
    return int(_redirect_param_count(text) > 0)


@lru_cache(maxsize=200_000)
def _sensitive_param_count(text: str) -> int:
    pairs = _parse_query_pairs(text)
    count = 0
    for key, value in pairs:
        key_lower = key.lower()
        value_lower = value.lower()
        if any(keyword in key_lower or keyword in value_lower for keyword in SENSITIVE_KEYWORDS):
            count += 1
    return count


@lru_cache(maxsize=200_000)
def _looks_like_base64_value(value: str) -> bool:
    if len(value) < 16 or not BASE64_LIKE_VALUE_PATTERN.fullmatch(value):
        return False
    return any(char.isalpha() for char in value) and (
        any(char.isdigit() for char in value) or any(char in "+/=_-" for char in value)
    )


@lru_cache(maxsize=200_000)
def _base64_like_value_present(text: str) -> int:
    pairs = _parse_query_pairs(text)
    return int(any(_looks_like_base64_value(value) for _, value in pairs))


@lru_cache(maxsize=200_000)
def _contains_double_slash_in_path(text: str) -> int:
    return int(text.startswith("//") or "//" in text[1:])


@lru_cache(maxsize=200_000)
def _has_explicit_port(url: str) -> int:
    if not url:
        return 0
    try:
        parsed = urlparse(url)
    except ValueError:
        return 0
    try:
        return int(parsed.port is not None)
    except ValueError:
        return 0


def build_domain_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    hostname = _get_text_series(df, "hostname")
    registered_domain = _get_text_series(df, "registered_domain")
    subdomain = _get_text_series(df, "subdomain")
    suffix = _get_text_series(df, "suffix")

    features = pd.DataFrame(index=df.index)
    features["domain_length"] = hostname.str.len()
    features["subdomain_count"] = subdomain.apply(_subdomain_count)
    features["num_tokens_domain"] = hostname.apply(_num_tokens_domain)
    features["avg_token_length_domain"] = hostname.apply(_avg_token_length)
    features["max_token_length_domain"] = hostname.apply(_max_token_length)
    features["num_hyphens"] = hostname.str.count("-")
    digit_count = hostname.str.count(r"\d")
    features["digit_ratio"] = _safe_ratio(digit_count, features["domain_length"])
    features["entropy_domain"] = hostname.apply(_shannon_entropy)
    features["contains_brand_name"] = hostname.apply(_contains_brand_name)
    features["contains_sensitive_keyword"] = hostname.apply(_contains_sensitive_keyword)
    features["suspicious_token_count"] = hostname.apply(lambda text: _count_tokens_matching_keywords(text, SENSITIVE_KEYWORDS))
    features["brand_like_token_count"] = hostname.apply(_brand_like_token_count)
    features["mixed_alnum_token_count"] = hostname.apply(_mixed_alnum_token_count)
    features["brand_in_subdomain_only"] = (
        subdomain.apply(_contains_brand_name) & ~registered_domain.apply(_contains_brand_name).astype(bool)
    ).astype(int)
    features["brand_in_registered_domain"] = registered_domain.apply(_contains_brand_name)
    features["num_brand_mentions"] = hostname.apply(_num_brand_mentions)
    features["closest_brand_similarity_ratio"] = hostname.apply(_closest_brand_similarity_ratio)
    features["edit_distance_to_top_brand"] = hostname.apply(_min_edit_distance_to_top_brand)
    features["tld_risk_score"] = suffix.apply(_tld_risk_score)
    features["brand_position_score"] = hostname.apply(_brand_position_score)
    features["registered_domain_length"] = registered_domain.str.len()
    features["consonant_run_max"] = hostname.apply(_consonant_run_max)
    features["char_repeat_ratio"] = hostname.apply(_char_repeat_ratio)
    features["token_entropy_max"] = hostname.apply(_token_entropy_max)
    features["consecutive_digit_run_max"] = hostname.apply(_consecutive_digit_run_max)
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
    features["avg_path_segment_length"] = path.apply(_avg_path_segment_length)
    features["max_path_segment_length"] = path.apply(_max_path_segment_length)
    features["num_numeric_segments"] = path.apply(_num_numeric_segments)
    features["num_mixed_segments"] = path.apply(_num_mixed_segments)
    features["path_entropy"] = path.apply(_path_entropy)
    features["query_param_count"] = query.apply(lambda text: 0 if not text else text.count("&") + 1)
    features["query_key_count"] = query.apply(_query_key_count)
    features["query_value_length_max"] = query.apply(_query_value_length_max)
    features["percent_encoded_ratio"] = sample.apply(_percent_encoded_ratio)

    features["suspicious_token_count"] = sample.apply(_count_sensitive_keywords)
    features["path_has_login_segment"] = path.apply(lambda text: _path_has_keyword(text, LOGIN_PATH_KEYWORDS))
    features["path_has_verify_segment"] = path.apply(lambda text: _path_has_keyword(text, VERIFY_PATH_KEYWORDS))
    features["path_has_brand_segment"] = path.apply(_path_has_brand_segment)
    features["path_has_user_action_keyword"] = path.apply(lambda text: _path_has_keyword(text, SENSITIVE_KEYWORDS))
    features["has_redirect_param"] = query.apply(_has_redirect_param)
    features["redirect_param_count"] = query.apply(_redirect_param_count)
    features["sensitive_param_count"] = query.apply(_sensitive_param_count)
    features["base64_like_value_present"] = query.apply(_base64_like_value_present)
    features["contains_double_slash_in_path"] = path.apply(_contains_double_slash_in_path)
    features["has_https_token_in_host"] = hostname.str.contains("https", case=False, regex=False).astype(int)
    features["uses_http_scheme"] = scheme.str.lower().eq("http").astype(int)
    features["uses_https_scheme"] = scheme.str.lower().eq("https").astype(int)
    features["has_fragment"] = fragment.ne("").astype(int)
    features["has_query"] = query.ne("").astype(int)
    features["has_ip_host"] = is_ip_host
    features["port_specified_flag"] = sample.apply(_has_explicit_port)

    return features.astype(float)


def build_feature_frame(df: pd.DataFrame, dataset_kind: str) -> pd.DataFrame:
    if dataset_kind == "domain":
        return build_domain_feature_frame(df)
    if dataset_kind == "url":
        return build_url_feature_frame(df)
    raise ValueError(f"Unsupported dataset_kind: {dataset_kind}")


def build_lexical_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    return build_url_feature_frame(df)


def align_feature_frame(feature_frame: pd.DataFrame, feature_columns: list[str] | tuple[str, ...] | None) -> pd.DataFrame:
    if not feature_columns:
        return feature_frame.astype(float)

    expected_columns = list(feature_columns)
    aligned = feature_frame.reindex(columns=expected_columns, fill_value=0.0)
    return aligned.astype(float)
