from __future__ import annotations

import argparse
import signal
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

from phishing_url_ml.settings import DEFAULT_USER_AGENT, RAW_DIR, SOURCE_CONFIGS
from phishing_url_ml.utils import ensure_parent_dir, log


STOP_REQUESTED = False


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Value must be a positive integer.")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect timestamped OpenPhish snapshots into a dedicated archive folder."
    )
    parser.add_argument(
        "--include-openphish",
        action="store_true",
        help="Required opt-in flag before collecting the OpenPhish community feed.",
    )
    parser.add_argument(
        "--interval-minutes",
        type=positive_int,
        default=20,
        help="How many minutes to wait between downloads.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RAW_DIR / "openphish_snapshots",
        help="Dedicated directory used to store archived OpenPhish snapshots.",
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Download exactly one snapshot and exit. Useful for Task Scheduler or quick testing.",
    )
    parser.add_argument(
        "--max-runs",
        type=positive_int,
        help="Optional maximum number of download cycles before exiting while running continuously in the terminal.",
    )
    parser.add_argument(
        "--request-timeout-seconds",
        type=positive_int,
        default=120,
        help="Read timeout used for the OpenPhish HTTP request.",
    )
    return parser.parse_args()


def install_signal_handlers() -> None:
    def handle_stop(signum: int, frame) -> None:  # type: ignore[no-untyped-def]
        del signum, frame
        global STOP_REQUESTED
        STOP_REQUESTED = True
        log("Stop requested. The collector will exit after the current cycle finishes.")

    signal.signal(signal.SIGINT, handle_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_stop)


def build_snapshot_path(output_dir: Path, timestamp: datetime) -> Path:
    base_name = f"openphish_{timestamp:%Y-%m-%d_%H-%M}"
    candidate = output_dir / f"{base_name}.txt"
    if not candidate.exists():
        return candidate

    suffix = 1
    while True:
        candidate = output_dir / f"{base_name}_{suffix:02d}.txt"
        if not candidate.exists():
            return candidate
        suffix += 1


def download_snapshot(output_dir: Path, request_timeout_seconds: int) -> Path:
    source = SOURCE_CONFIGS["openphish"]
    snapshot_time = datetime.now()
    output_path = build_snapshot_path(output_dir, snapshot_time)
    ensure_parent_dir(output_path)

    response = requests.get(
        source.url,
        headers={"User-Agent": DEFAULT_USER_AGENT},
        timeout=(10, request_timeout_seconds),
    )
    response.raise_for_status()

    rows = [line.strip() for line in response.text.splitlines() if line.strip()]
    payload = "\n".join(rows)
    if payload:
        payload += "\n"
    output_path.write_text(payload, encoding="utf-8")

    size_kb = output_path.stat().st_size / 1024
    log(f"Saved OpenPhish snapshot to {output_path} ({len(rows):,} rows, {size_kb:.1f} KB)")
    return output_path


def sleep_until(next_run_at: datetime) -> None:
    while not STOP_REQUESTED:
        remaining_seconds = (next_run_at - datetime.now()).total_seconds()
        if remaining_seconds <= 0:
            return
        time.sleep(min(30, max(1, remaining_seconds)))


def main() -> None:
    args = parse_args()
    if not args.include_openphish:
        raise SystemExit(
            "OpenPhish collection is opt-in. Re-run with --include-openphish after confirming "
            "the community feed terms fit your academic use case."
        )

    install_signal_handlers()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    log(f"OpenPhish snapshot archive directory: {args.output_dir}")
    if args.run_once:
        log("Collector mode: single snapshot and exit")
    else:
        log(f"Collector mode: continuous loop every {args.interval_minutes} minute(s)")

    completed_runs = 0
    while not STOP_REQUESTED:
        cycle_started_at = datetime.now()
        try:
            download_snapshot(
                output_dir=args.output_dir,
                request_timeout_seconds=args.request_timeout_seconds,
            )
        except requests.RequestException as exc:
            log(f"OpenPhish download failed: {type(exc).__name__}: {exc}")

        completed_runs += 1
        if args.run_once:
            break
        if args.max_runs is not None and completed_runs >= args.max_runs:
            break

        next_run_at = cycle_started_at + timedelta(minutes=args.interval_minutes)
        log(f"Next OpenPhish snapshot scheduled at {next_run_at:%Y-%m-%d %H:%M:%S}")
        sleep_until(next_run_at)

    log("OpenPhish snapshot collector stopped.")


if __name__ == "__main__":
    main()
