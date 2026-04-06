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

from .feature_engineering import build_feature_frame
from .settings import BASE_DIR, IDS_EVENTS_PATH, OFFICIAL_MODEL_REGISTRY_PATH
from .utils import build_parsed_record, ensure_parent_dir


RISK_THRESHOLDS = {
    "high": 0.5,
    "medium": 0.60,
    "low": 0.35,
}


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


def risk_level_for_score(score: float) -> str:
    if score >= RISK_THRESHOLDS["high"]:
        return "high"
    if score >= RISK_THRESHOLDS["medium"]:
        return "medium"
    if score >= RISK_THRESHOLDS["low"]:
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
    inference_df, parsed_row = build_inference_row(value, resolved_kind)
    feature_frame = build_feature_frame(inference_df, resolved_kind)
    predicted_label = int(bundle.model.predict(feature_frame)[0])
    score, score_source = normalized_score_for_model(bundle.model, feature_frame)
    risk_level = risk_level_for_score(score)
    feature_values = feature_frame.iloc[0].to_dict()
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
        "recommendation": recommendation_for_prediction(predicted_label, risk_level),
        "signals": summarize_signals(resolved_kind, parsed_row, feature_values),
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
