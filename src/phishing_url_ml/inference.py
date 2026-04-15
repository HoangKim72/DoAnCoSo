from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from .feature_engineering import align_feature_frame, build_feature_frame
from .settings import (
    BASE_DIR,
    CURATED_BENIGN_URL_RUNTIME_PATCH_DIR,
    IDS_EVENTS_PATH,
    OFFICIAL_MODEL_REGISTRY_PATH,
    RAW_DIR,
    RUNTIME_RISK_POLICY_PATH,
)
from .utils import build_parsed_record, ensure_parent_dir


DEFAULT_RUNTIME_RISK_POLICY = {
    "version": "builtin_fallback_v1",
    "default": {
        "high": 0.90,
        "medium": 0.65,
        "low": 0.35,
    },
    "dataset_kind_overrides": {
        "domain": {
            "high": 0.95,
            "medium": 0.90,
            "low": 0.55,
        },
        "url": {
            "high": 0.98,
            "medium": 0.75,
            "low": 0.45,
        },
    },
}
CURATED_BENIGN_DOMAIN_DIR = RAW_DIR / "vn_benign_domain_addon"
CURATED_BENIGN_OVERRIDE_SCORE = 0.01


@dataclass(frozen=True)
class OfficialModelBundle:
    dataset_kind: str
    variant_name: str
    model_name: str
    model_path: Path
    run_summary_path: Path
    feature_count: int
    run_summary: dict[str, Any]
    model: Any


def resolve_repo_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else BASE_DIR / path


@lru_cache(maxsize=1)
def load_official_registry() -> dict[str, Any]:
    if not OFFICIAL_MODEL_REGISTRY_PATH.exists():
        raise FileNotFoundError(
            f"Official model registry not found: {OFFICIAL_MODEL_REGISTRY_PATH}"
        )
    return json.loads(OFFICIAL_MODEL_REGISTRY_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=2)
def load_official_model_bundle(dataset_kind: str) -> OfficialModelBundle:
    registry = load_official_registry()["official_default_models"][dataset_kind]
    model_path = resolve_repo_path(registry["selected_model_path"])
    run_summary_path = resolve_repo_path(registry["run_summary_path"])
    run_summary = json.loads(run_summary_path.read_text(encoding="utf-8"))
    model = joblib.load(model_path)
    return OfficialModelBundle(
        dataset_kind=dataset_kind,
        variant_name=str(registry["variant_name"]),
        model_name=str(registry["selected_model_name"]),
        model_path=model_path,
        run_summary_path=run_summary_path,
        feature_count=int(registry["feature_count"]),
        run_summary=run_summary,
        model=model,
    )


@lru_cache(maxsize=1)
def load_curated_benign_domain_allowlist() -> dict[str, frozenset[str]]:
    exact_hostnames: set[str] = set()
    trusted_registered_domains: set[str] = set()

    if not CURATED_BENIGN_DOMAIN_DIR.exists():
        return {
            "exact_hostnames": frozenset(),
            "trusted_registered_domains": frozenset(),
        }

    for csv_path in sorted(CURATED_BENIGN_DOMAIN_DIR.glob("*.csv")):
        try:
            frame = pd.read_csv(csv_path)
        except Exception:
            continue
        if "input_value" not in frame.columns:
            continue

        for raw_value in frame["input_value"].dropna().tolist():
            parsed = build_parsed_record(raw_value, "domain")
            if not parsed.get("parse_ok"):
                continue
            hostname = str(parsed.get("canonical_hostname") or parsed.get("hostname") or "").strip().lower()
            registered_domain = str(
                parsed.get("canonical_registered_domain") or parsed.get("registered_domain") or ""
            ).strip().lower()
            if not hostname:
                continue
            exact_hostnames.add(hostname)
            if hostname == registered_domain:
                trusted_registered_domains.add(registered_domain)

    return {
        "exact_hostnames": frozenset(exact_hostnames),
        "trusted_registered_domains": frozenset(trusted_registered_domains),
    }


@lru_cache(maxsize=1)
def load_curated_benign_url_runtime_patch() -> dict[str, frozenset[str]]:
    exact_urls: set[str] = set()
    exact_hostnames: set[str] = set()
    url_prefixes: set[str] = set()

    if not CURATED_BENIGN_URL_RUNTIME_PATCH_DIR.exists():
        return {
            "exact_urls": frozenset(),
            "exact_hostnames": frozenset(),
            "url_prefixes": frozenset(),
        }

    for csv_path in sorted(CURATED_BENIGN_URL_RUNTIME_PATCH_DIR.glob("*.csv")):
        try:
            frame = pd.read_csv(csv_path)
        except Exception:
            continue
        if "match_value" not in frame.columns:
            continue

        for row in frame.to_dict(orient="records"):
            rule_type = str(row.get("rule_type", "")).strip().lower() or "exact_url"
            raw_value = str(row.get("match_value", "")).strip()
            if not raw_value:
                continue

            if rule_type == "exact_url":
                parsed = build_parsed_record(raw_value, "url")
                canonical_url = str(parsed.get("canonical_url") or "").strip().lower()
                if canonical_url:
                    exact_urls.add(canonical_url)
            elif rule_type == "exact_hostname":
                parsed = build_parsed_record(raw_value, "domain")
                if not parsed.get("parse_ok"):
                    parsed = build_parsed_record(raw_value, "url")
                hostname = str(parsed.get("canonical_hostname") or parsed.get("hostname") or "").strip().lower()
                if hostname:
                    exact_hostnames.add(hostname)
            elif rule_type == "url_prefix":
                parsed = build_parsed_record(raw_value, "url")
                canonical_url = str(parsed.get("canonical_url") or "").strip().lower()
                if canonical_url:
                    url_prefixes.add(canonical_url)

    return {
        "exact_urls": frozenset(exact_urls),
        "exact_hostnames": frozenset(exact_hostnames),
        "url_prefixes": frozenset(url_prefixes),
    }


@lru_cache(maxsize=1)
def load_runtime_risk_policy() -> dict[str, Any]:
    if not RUNTIME_RISK_POLICY_PATH.exists():
        return DEFAULT_RUNTIME_RISK_POLICY

    try:
        payload = json.loads(RUNTIME_RISK_POLICY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_RUNTIME_RISK_POLICY

    default_thresholds = payload.get("default", {})
    dataset_kind_overrides = payload.get("dataset_kind_overrides", {})
    merged = {
        "version": str(payload.get("version", DEFAULT_RUNTIME_RISK_POLICY["version"])),
        "default": {
            "high": float(default_thresholds.get("high", DEFAULT_RUNTIME_RISK_POLICY["default"]["high"])),
            "medium": float(default_thresholds.get("medium", DEFAULT_RUNTIME_RISK_POLICY["default"]["medium"])),
            "low": float(default_thresholds.get("low", DEFAULT_RUNTIME_RISK_POLICY["default"]["low"])),
        },
        "dataset_kind_overrides": {},
    }

    for dataset_kind, builtin_thresholds in DEFAULT_RUNTIME_RISK_POLICY["dataset_kind_overrides"].items():
        override = dataset_kind_overrides.get(dataset_kind, {})
        merged["dataset_kind_overrides"][dataset_kind] = {
            "high": float(override.get("high", builtin_thresholds["high"])),
            "medium": float(override.get("medium", builtin_thresholds["medium"])),
            "low": float(override.get("low", builtin_thresholds["low"])),
        }
    return merged


def detect_dataset_kind(value: str, requested_kind: str = "auto") -> str:
    if requested_kind in {"domain", "url"}:
        return requested_kind
    normalized = value.strip().lower()
    if "://" in normalized or any(token in normalized for token in ["/", "?", "#"]):
        return "url"
    return "domain"


def build_inference_row(value: str, dataset_kind: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    raw_value = value.strip()
    if not raw_value:
        raise ValueError("Input value is empty.")

    if dataset_kind == "domain":
        parsed = build_parsed_record(raw_value, "domain")
        if not parsed["parse_ok"]:
            url_parsed = build_parsed_record(raw_value, "url")
            if not url_parsed["parse_ok"]:
                reason = parsed.get("invalid_reason") or url_parsed.get("invalid_reason") or "invalid_input"
                raise ValueError(f"Could not parse domain input. Reason: {reason}")
            parsed = url_parsed
        sample_text = parsed["canonical_hostname"] or parsed["hostname"]
        record_type = "domain"
    elif dataset_kind == "url":
        parsed = build_parsed_record(raw_value, "url")
        if not parsed["parse_ok"]:
            reason = parsed.get("invalid_reason") or "invalid_input"
            raise ValueError(f"Could not parse URL input. Reason: {reason}")
        sample_text = parsed["canonical_url"] or raw_value
        record_type = "url"
    else:
        raise ValueError(f"Unsupported dataset kind: {dataset_kind}")

    row = {
        "sample_text": sample_text,
        "label": -1,
        "source": "ids_live",
        "collected_at": datetime.now().strftime("%Y-%m-%d"),
        "record_type": record_type,
        **parsed,
    }
    return pd.DataFrame([row]), row


def normalized_score_for_model(model: Any, features: pd.DataFrame) -> tuple[float, str]:
    if hasattr(model, "predict_proba"):
        probability = float(model.predict_proba(features)[0][1])
        return probability, "predict_proba"
    if hasattr(model, "decision_function"):
        raw_score = float(model.decision_function(features)[0])
        return 1.0 / (1.0 + math.exp(-raw_score)), "sigmoid_decision"
    binary = float(model.predict(features)[0])
    return binary, "predict"


def expected_feature_columns(model: Any, run_summary: dict[str, Any] | None = None) -> list[str] | None:
    if hasattr(model, "feature_names_in_"):
        feature_names = list(getattr(model, "feature_names_in_", []))
        if feature_names:
            return feature_names
    if run_summary:
        feature_columns = run_summary.get("feature_columns")
        if feature_columns:
            return list(feature_columns)
    return None


def risk_thresholds_for_dataset(dataset_kind: str) -> dict[str, float]:
    policy = load_runtime_risk_policy()
    thresholds = dict(policy["default"])
    thresholds.update(policy["dataset_kind_overrides"].get(dataset_kind, {}))
    return thresholds


def risk_level_for_score(score: float, dataset_kind: str) -> str:
    thresholds = risk_thresholds_for_dataset(dataset_kind)
    if score >= thresholds["high"]:
        return "high"
    if score >= thresholds["medium"]:
        return "medium"
    if score >= thresholds["low"]:
        return "low"
    return "minimal"


def recommendation_for_prediction(predicted_label: int, risk_level: str) -> str:
    if predicted_label == 1 and risk_level == "high":
        return "Gửi cảnh báo ngay cho người dùng và đánh dấu sự kiện để SOC kiểm tra."
    if predicted_label == 1 and risk_level == "medium":
        return "Hiển thị cảnh báo trên dashboard và theo dõi thêm các truy cập tiếp theo."
    if predicted_label == 1:
        return "Giữ sự kiện trong log để theo dõi, chưa cần cảnh báo mạnh."
    return "Không cần cảnh báo mạnh; tiếp tục ghi log để đối chiếu hành vi."


def curated_benign_domain_override(parsed_row: dict[str, Any]) -> dict[str, str] | None:
    hostname = str(parsed_row.get("canonical_hostname") or parsed_row.get("hostname") or "").strip().lower()
    registered_domain = str(
        parsed_row.get("canonical_registered_domain") or parsed_row.get("registered_domain") or ""
    ).strip().lower()
    if not hostname:
        return None

    allowlist = load_curated_benign_domain_allowlist()
    if hostname in allowlist["exact_hostnames"]:
        return {
            "reason": "curated_benign_domain_exact_hostname",
            "match_value": hostname,
        }
    if (
        registered_domain
        and registered_domain in allowlist["trusted_registered_domains"]
        and hostname.endswith(f".{registered_domain}")
    ):
        return {
            "reason": "curated_benign_domain_trusted_registered_domain",
            "match_value": registered_domain,
        }
    return None


def curated_benign_url_override(parsed_row: dict[str, Any]) -> dict[str, str] | None:
    canonical_url = str(parsed_row.get("canonical_url") or "").strip().lower()
    hostname = str(parsed_row.get("canonical_hostname") or parsed_row.get("hostname") or "").strip().lower()
    if not canonical_url:
        return None

    allowlist = load_curated_benign_url_runtime_patch()
    if canonical_url in allowlist["exact_urls"]:
        return {
            "reason": "curated_benign_url_exact_url",
            "match_value": canonical_url,
        }
    if hostname and hostname in allowlist["exact_hostnames"]:
        return {
            "reason": "curated_benign_url_exact_hostname",
            "match_value": hostname,
        }
    for prefix in allowlist["url_prefixes"]:
        if canonical_url.startswith(prefix):
            return {
                "reason": "curated_benign_url_prefix",
                "match_value": prefix,
            }
    return None


def summarize_signals(dataset_kind: str, parsed_row: dict[str, Any], features: dict[str, float]) -> list[str]:
    signals: list[str] = []
    if dataset_kind == "domain":
        if features.get("contains_brand_name", 0) >= 1:
            signals.append("Hostname chứa token trùng với thương hiệu phổ biến.")
        if features.get("contains_sensitive_keyword", 0) >= 1:
            signals.append("Hostname chứa từ khóa nhạy cảm như login, verify hoặc payment.")
        if features.get("edit_distance_to_top_brand", 99) <= 1:
            signals.append("Hostname rất gần với tên thương hiệu thật, có dấu hiệu giả mạo.")
        if features.get("tld_risk_score", 0.0) >= 0.7:
            signals.append(f"TLD `.{parsed_row.get('suffix', '')}` nằm trong nhóm rủi ro cao hơn bình thường.")
        if features.get("digit_ratio", 0.0) >= 0.2:
            signals.append("Hostname có tỷ lệ chữ số cao bất thường.")
        if features.get("is_idn_or_punycode", 0) >= 1:
            signals.append("Hostname dùng IDN hoặc punycode.")
    else:
        if features.get("suspicious_token_count", 0) >= 1:
            signals.append("URL chứa từ khóa thường gặp trong phishing như login, verify hoặc reset.")
        if features.get("uses_http_scheme", 0) >= 1:
            signals.append("URL chỉ dùng HTTP, không có HTTPS.")
        if features.get("has_https_token_in_host", 0) >= 1:
            signals.append("Hostname chứa chuỗi `https`, đây là mẫu đánh lừa phổ biến.")
        if features.get("has_ip_host", 0) >= 1:
            signals.append("URL dùng địa chỉ IP thay vì domain.")
        if features.get("query_param_count", 0) >= 4:
            signals.append("URL có nhiều tham số query hơn mức thông thường.")
        if features.get("special_char_ratio", 0.0) >= 0.35:
            signals.append("URL có tỷ lệ ký tự đặc biệt cao.")
    return signals[:4]


def official_model_cards() -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    registry = load_official_registry()["official_default_models"]
    for dataset_kind in ["domain", "url"]:
        entry = registry[dataset_kind]
        bundle = load_official_model_bundle(dataset_kind)
        validation_record = next(
            (
                row
                for row in bundle.run_summary["validation_results"]
                if str(row["model"]) == str(entry["selected_model_name"])
            ),
            bundle.run_summary["validation_results"][0],
        )
        cards.append(
            {
                "dataset_kind": dataset_kind,
                "variant_name": entry["variant_name"],
                "rows": int(entry["rows"]),
                "benign": int(entry["benign"]),
                "phishing": int(entry["phishing"]),
                "feature_count": int(entry["feature_count"]),
                "model_name": entry["selected_model_name"],
                "validation_pr_auc": float(validation_record["pr_auc"]),
                "test_pr_auc": float(bundle.run_summary["test_metrics"]["pr_auc"]),
                "test_f1": float(bundle.run_summary["test_metrics"]["f1"]),
            }
        )
    return cards


def predict_value(
    value: str,
    dataset_kind: str = "auto",
    source: str = "ids_sensor",
    persist: bool = False,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_kind = detect_dataset_kind(value, dataset_kind)
    bundle = load_official_model_bundle(resolved_kind)
    risk_policy = load_runtime_risk_policy()
    thresholds = risk_thresholds_for_dataset(resolved_kind)
    inference_df, parsed_row = build_inference_row(value, resolved_kind)
    feature_frame = build_feature_frame(inference_df, resolved_kind)
    feature_frame = align_feature_frame(
        feature_frame,
        expected_feature_columns(bundle.model, bundle.run_summary),
    )
    predicted_label = int(bundle.model.predict(feature_frame)[0])
    score, score_source = normalized_score_for_model(bundle.model, feature_frame)
    risk_level = risk_level_for_score(score, resolved_kind)
    feature_values = feature_frame.iloc[0].to_dict()
    override = None
    model_predicted_label = predicted_label
    model_score = round(float(score), 6)
    model_risk_level = risk_level
    model_score_source = score_source
    if predicted_label == 1:
        if resolved_kind == "domain":
            override = curated_benign_domain_override(parsed_row)
        elif resolved_kind == "url":
            override = curated_benign_url_override(parsed_row)
        if override:
            predicted_label = 0
            score = min(float(score), CURATED_BENIGN_OVERRIDE_SCORE)
            score_source = "curated_benign_override"
            risk_level = "minimal"
    signals = summarize_signals(resolved_kind, parsed_row, feature_values)
    if override:
        override_signal = (
            "Khớp danh sách benign runtime da curate; ghi log nhung khong nang canh bao phishing."
        )
        signals = [override_signal, *[signal for signal in signals if signal != override_signal]][:4]
    event = {
        "event_id": uuid.uuid4().hex,
        "received_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "dataset_kind": resolved_kind,
        "source": source,
        "raw_value": value.strip(),
        "normalized_value": parsed_row["sample_text"],
        "predicted_label": predicted_label,
        "predicted_class": "phishing" if predicted_label == 1 else "benign",
        "score": round(float(score), 6),
        "score_source": score_source,
        "risk_level": risk_level,
        "model_name": bundle.model_name,
        "variant_name": bundle.variant_name,
        "feature_count": bundle.feature_count,
        "risk_policy_version": risk_policy["version"],
        "risk_thresholds": thresholds,
        "recommendation": (
            "Khớp danh sách benign đã curate; tiếp tục ghi log nhưng không phát cảnh báo mạnh."
            if override
            else recommendation_for_prediction(predicted_label, risk_level)
        ),
        "signals": signals,
        "parsed": {
            "hostname": parsed_row.get("hostname", ""),
            "registered_domain": parsed_row.get("registered_domain", ""),
            "subdomain": parsed_row.get("subdomain", ""),
            "suffix": parsed_row.get("suffix", ""),
            "path": parsed_row.get("path", ""),
            "query": parsed_row.get("query", ""),
        },
        "metadata": metadata or {},
    }
    if override:
        event["decision_mode"] = "model_plus_curated_benign_override"
        event["override_reason"] = override["reason"]
        event["override_match_value"] = override["match_value"]
        event["model_predicted_label_before_override"] = model_predicted_label
        event["model_predicted_class_before_override"] = (
            "phishing" if model_predicted_label == 1 else "benign"
        )
        event["model_score_before_override"] = model_score
        event["model_score_source_before_override"] = model_score_source
        event["model_risk_level_before_override"] = model_risk_level
    else:
        event["decision_mode"] = "model"
    if persist:
        append_event(event)
    return event


def append_event(event: dict[str, Any], events_path: Path = IDS_EVENTS_PATH) -> None:
    ensure_parent_dir(events_path)
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def load_events(limit: int = 200, events_path: Path = IDS_EVENTS_PATH) -> list[dict[str, Any]]:
    if not events_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with events_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    rows.sort(key=lambda item: item.get("received_at", ""), reverse=True)
    return rows[:limit]


def summarize_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    total_events = len(events)
    phishing_events = sum(event.get("predicted_label") == 1 for event in events)
    high_risk_events = sum(event.get("risk_level") == "high" for event in events)
    domain_events = sum(event.get("dataset_kind") == "domain" for event in events)
    url_events = sum(event.get("dataset_kind") == "url" for event in events)
    return {
        "total_events": total_events,
        "phishing_events": phishing_events,
        "benign_events": total_events - phishing_events,
        "high_risk_events": high_risk_events,
        "domain_events": domain_events,
        "url_events": url_events,
        "latest_event_at": events[0]["received_at"] if events else None,
    }
