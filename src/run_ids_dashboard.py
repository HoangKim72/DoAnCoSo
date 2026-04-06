from __future__ import annotations

import argparse

from phishing_url_ml.ids_dashboard_app import create_app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the IDS ingestion API and phishing dashboard using the official hybrid models."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=8080, help="Port for the local web server.")
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
