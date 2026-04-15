from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from phishing_url_ml.settings import BASE_DIR, IDS_BRIDGE_STATE_PATH
from phishing_url_ml.utils import clean_text, ensure_parent_dir


SUPPORTED_FORMATS = (
    "auto",
    "suricata-eve",
    "zeek-dns-json",
    "zeek-http-json",
    "zeek-ssl-json",
    "zeek-tls-json",
)
DEFAULT_API_URL = "http://127.0.0.1:8080/api/ingest"


@dataclass(frozen=True)
class BridgeEvent:
    dataset_kind: str
    value: str
    metadata: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Bridge real IDS JSON logs into the local phishing dashboard API. "
            "Supports Suricata eve.json and Zeek JSON logs for DNS, HTTP, and TLS."
        )
    )
    parser.add_argument("--input", type=Path, required=True, help="Path to the IDS log file.")
    parser.add_argument(
        "--format",
        default="auto",
        choices=SUPPORTED_FORMATS,
        help="Explicit log format. Use auto to detect line-by-line.",
    )
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="Dashboard ingest endpoint URL.")
    parser.add_argument(
        "--source",
        default="ids_log_bridge",
        help="Source label written into the dashboard event.",
    )
    parser.add_argument(
        "--sensor-name",
        help="Optional sensor/display name shown on the dashboard. Defaults to the input filename.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=IDS_BRIDGE_STATE_PATH,
        help=(
            "JSON file used to remember the last byte offset. "
            "Defaults to data/runtime/ids_bridge_state.json."
        ),
    )
    parser.add_argument("--follow", action="store_true", help="Tail the file and ingest new lines continuously.")
    parser.add_argument(
        "--start-at-end",
        action="store_true",
        help="When following and no saved state exists, start from the current end of file.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="Seconds to wait between polling attempts when --follow is enabled.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="HTTP timeout in seconds for each ingest request.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print transformed payloads instead of sending them.")
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional maximum number of extracted IDS events to process before stopping.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue after API or parsing errors instead of stopping immediately.",
    )
    return parser.parse_args()


def resolve_repo_path(path_value: Path) -> Path:
    return path_value if path_value.is_absolute() else BASE_DIR / path_value


def state_key(log_path: Path, log_format: str) -> str:
    return f"{log_format}|{log_path.resolve()}"


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(path: Path, payload: dict[str, Any]) -> None:
    ensure_parent_dir(path)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def iso_timestamp(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat(timespec="seconds")
        except (OverflowError, OSError, ValueError):
            return str(value)
    text = clean_text(value)
    return text


def compact_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    compacted: dict[str, Any] = {}
    for key, value in payload.items():
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
            if not value:
                continue
        compacted[key] = value
    return compacted


def infer_http_scheme(port_value: Any) -> str:
    try:
        port = int(port_value)
    except (TypeError, ValueError):
        return "http"
    return "https" if port == 443 else "http"


def build_url_value(hostname: Any, raw_target: Any, scheme: str) -> str:
    host_text = clean_text(hostname)
    target_text = clean_text(raw_target)
    if target_text.startswith(("http://", "https://")):
        return target_text
    if not host_text:
        return ""
    if not target_text:
        return f"{scheme}://{host_text}/"
    if not target_text.startswith("/"):
        target_text = f"/{target_text}"
    return f"{scheme}://{host_text}{target_text}"


def first_non_empty(*values: Any) -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def detect_line_format(payload: dict[str, Any]) -> str | None:
    if clean_text(payload.get("event_type")):
        return "suricata-eve"
    if clean_text(payload.get("query")):
        return "zeek-dns-json"
    if clean_text(payload.get("host")) or clean_text(payload.get("uri")):
        return "zeek-http-json"
    if clean_text(payload.get("server_name")):
        return "zeek-ssl-json"
    return None


def build_common_metadata(
    payload: dict[str, Any],
    *,
    parser_format: str,
    ids_event_type: str,
    log_path: Path,
    line_number: int,
    sensor_name: str,
) -> dict[str, Any]:
    return compact_metadata(
        {
            "sensor_name": sensor_name,
            "parser_format": parser_format,
            "ids_event_type": ids_event_type,
            "observed_at": iso_timestamp(payload.get("timestamp") or payload.get("ts")),
            "src_ip": payload.get("src_ip") or payload.get("id.orig_h"),
            "src_port": payload.get("src_port") or payload.get("id.orig_p"),
            "dest_ip": payload.get("dest_ip") or payload.get("id.resp_h"),
            "dest_port": payload.get("dest_port") or payload.get("id.resp_p"),
            "uid": payload.get("uid"),
            "flow_id": payload.get("flow_id"),
            "community_id": payload.get("community_id"),
            "log_path": str(log_path),
            "log_line_number": line_number,
        }
    )


def extract_suricata_event(
    payload: dict[str, Any],
    *,
    log_path: Path,
    line_number: int,
    sensor_name: str,
) -> BridgeEvent | None:
    event_type = clean_text(payload.get("event_type")).lower()
    metadata = build_common_metadata(
        payload,
        parser_format="suricata-eve",
        ids_event_type=event_type or "unknown",
        log_path=log_path,
        line_number=line_number,
        sensor_name=sensor_name,
    )
    if event_type == "dns":
        dns_payload = payload.get("dns") or {}
        value = first_non_empty(dns_payload.get("rrname"), dns_payload.get("query"))
        if not value:
            return None
        return BridgeEvent("domain", value, metadata)

    if event_type == "tls":
        tls_payload = payload.get("tls") or {}
        value = clean_text(tls_payload.get("sni"))
        if not value:
            return None
        return BridgeEvent("domain", value, metadata)

    if event_type == "http":
        http_payload = payload.get("http") or {}
        hostname = first_non_empty(
            http_payload.get("hostname"),
            http_payload.get("http_host"),
            payload.get("dest_ip"),
        )
        url_target = first_non_empty(http_payload.get("url"), http_payload.get("uri"))
        scheme = infer_http_scheme(payload.get("dest_port"))
        value = build_url_value(hostname, url_target, scheme)
        if not value:
            return None
        metadata = compact_metadata(
            {
                **metadata,
                "http_method": http_payload.get("http_method"),
            }
        )
        return BridgeEvent("url", value, metadata)

    return None


def extract_zeek_dns_event(
    payload: dict[str, Any],
    *,
    log_path: Path,
    line_number: int,
    sensor_name: str,
) -> BridgeEvent | None:
    value = clean_text(payload.get("query"))
    if not value:
        return None
    metadata = build_common_metadata(
        payload,
        parser_format="zeek-dns-json",
        ids_event_type="dns",
        log_path=log_path,
        line_number=line_number,
        sensor_name=sensor_name,
    )
    return BridgeEvent("domain", value, metadata)


def extract_zeek_http_event(
    payload: dict[str, Any],
    *,
    log_path: Path,
    line_number: int,
    sensor_name: str,
) -> BridgeEvent | None:
    hostname = first_non_empty(payload.get("host"), payload.get("id.resp_h"))
    scheme = infer_http_scheme(payload.get("id.resp_p"))
    value = build_url_value(hostname, payload.get("uri"), scheme)
    if not value:
        return None
    metadata = compact_metadata(
        {
            **build_common_metadata(
                payload,
                parser_format="zeek-http-json",
                ids_event_type="http",
                log_path=log_path,
                line_number=line_number,
                sensor_name=sensor_name,
            ),
            "http_method": payload.get("method"),
        }
    )
    return BridgeEvent("url", value, metadata)


def extract_zeek_tls_event(
    payload: dict[str, Any],
    *,
    parser_format: str,
    log_path: Path,
    line_number: int,
    sensor_name: str,
) -> BridgeEvent | None:
    value = clean_text(payload.get("server_name"))
    if not value:
        return None
    metadata = build_common_metadata(
        payload,
        parser_format=parser_format,
        ids_event_type="tls",
        log_path=log_path,
        line_number=line_number,
        sensor_name=sensor_name,
    )
    return BridgeEvent("domain", value, metadata)


def extract_bridge_event(
    payload: dict[str, Any],
    *,
    requested_format: str,
    log_path: Path,
    line_number: int,
    sensor_name: str,
) -> BridgeEvent | None:
    resolved_format = requested_format
    if requested_format == "auto":
        resolved_format = detect_line_format(payload) or ""

    if resolved_format == "suricata-eve":
        return extract_suricata_event(
            payload,
            log_path=log_path,
            line_number=line_number,
            sensor_name=sensor_name,
        )
    if resolved_format == "zeek-dns-json":
        return extract_zeek_dns_event(
            payload,
            log_path=log_path,
            line_number=line_number,
            sensor_name=sensor_name,
        )
    if resolved_format == "zeek-http-json":
        return extract_zeek_http_event(
            payload,
            log_path=log_path,
            line_number=line_number,
            sensor_name=sensor_name,
        )
    if resolved_format == "zeek-ssl-json":
        return extract_zeek_tls_event(
            payload,
            parser_format="zeek-ssl-json",
            log_path=log_path,
            line_number=line_number,
            sensor_name=sensor_name,
        )
    if resolved_format == "zeek-tls-json":
        return extract_zeek_tls_event(
            payload,
            parser_format="zeek-tls-json",
            log_path=log_path,
            line_number=line_number,
            sensor_name=sensor_name,
        )
    return None


def line_iterator(path: Path, *, start_offset: int, follow: bool, poll_interval: float):
    with path.open("r", encoding="utf-8") as handle:
        handle.seek(start_offset)
        while True:
            line = handle.readline()
            if line:
                yield line, handle.tell()
                continue
            if not follow:
                break
            time.sleep(max(0.1, poll_interval))
            try:
                current_size = path.stat().st_size
            except FileNotFoundError:
                current_size = 0
            if current_size < handle.tell():
                handle.seek(0)


def initial_offset(
    log_path: Path,
    *,
    requested_format: str,
    state_path: Path,
    follow: bool,
    start_at_end: bool,
) -> int:
    saved_state = load_state(state_path)
    saved = saved_state.get(state_key(log_path, requested_format), {})
    offset = int(saved.get("offset", 0)) if isinstance(saved, dict) else 0
    file_size = log_path.stat().st_size
    if offset > file_size:
        return 0
    if offset > 0:
        return offset
    if follow and start_at_end:
        return file_size
    return 0


def main() -> None:
    args = parse_args()
    log_path = resolve_repo_path(args.input)
    if not log_path.exists():
        raise FileNotFoundError(f"Input log not found: {log_path}")

    state_path = resolve_repo_path(args.state_file)
    sensor_name = clean_text(args.sensor_name) or log_path.stem
    should_persist_state = not args.dry_run
    start_offset = initial_offset(
        log_path,
        requested_format=args.format,
        state_path=state_path,
        follow=args.follow,
        start_at_end=args.start_at_end,
    )

    counters = {
        "lines_read": 0,
        "events_extracted": 0,
        "events_sent": 0,
        "events_skipped": 0,
        "parse_errors": 0,
        "api_errors": 0,
    }
    processed_events = 0
    session = requests.Session()

    print(
        f"[bridge] input={log_path} format={args.format} "
        f"follow={args.follow} start_offset={start_offset} dry_run={args.dry_run}"
    )

    try:
        for line_number, (line, next_offset) in enumerate(
            line_iterator(
                log_path,
                start_offset=start_offset,
                follow=args.follow,
                poll_interval=args.poll_interval,
            ),
            start=1,
        ):
            counters["lines_read"] += 1
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                counters["parse_errors"] += 1
                print(f"[skip] line={line_number} reason=json_decode_error detail={exc}")
                if not args.continue_on_error:
                    raise
                continue

            bridge_event = extract_bridge_event(
                payload,
                requested_format=args.format,
                log_path=log_path,
                line_number=line_number,
                sensor_name=sensor_name,
            )
            if not bridge_event:
                counters["events_skipped"] += 1
                if should_persist_state:
                    state = load_state(state_path)
                    state[state_key(log_path, args.format)] = {
                        "offset": next_offset,
                        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                    }
                    save_state(state_path, state)
                continue

            counters["events_extracted"] += 1
            event_payload = {
                "dataset_kind": bridge_event.dataset_kind,
                "value": bridge_event.value,
                "source": args.source,
                "metadata": bridge_event.metadata,
            }

            if args.dry_run:
                print(json.dumps(event_payload, ensure_ascii=False))
            else:
                response = session.post(args.api_url, json=event_payload, timeout=args.timeout)
                if not response.ok:
                    counters["api_errors"] += 1
                    detail = response.text.strip() or response.reason
                    print(
                        f"[error] line={line_number} status={response.status_code} "
                        f"value={bridge_event.value} detail={detail}"
                    )
                    if not args.continue_on_error:
                        response.raise_for_status()
                else:
                    body = response.json()
                    counters["events_sent"] += 1
                    print(
                        f"[sent] line={line_number} kind={body.get('dataset_kind')} "
                        f"class={body.get('predicted_class')} risk={body.get('risk_level')} "
                        f"value={body.get('normalized_value')}"
                    )

            if should_persist_state:
                state = load_state(state_path)
                state[state_key(log_path, args.format)] = {
                    "offset": next_offset,
                    "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                }
                save_state(state_path, state)

            processed_events += 1
            if args.limit and processed_events >= args.limit:
                break
    except KeyboardInterrupt:
        print("[bridge] stopped by user")

    print(
        "[bridge] summary "
        + " ".join(f"{key}={value}" for key, value in counters.items())
    )


if __name__ == "__main__":
    main()
