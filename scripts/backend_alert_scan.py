"""Scan watchlist alerts via existing backend APIs and format for Discord.

This script is API-driven (uses /watchlist-analyze and /chart-data) so it can
run independently from local indicator/scoring internals.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from bootstrap import ensure_project_root_on_path

ensure_project_root_on_path()

from bot.alert_engine import (  # noqa: E402
    AlertEvent,
    build_ticker_alerts,
    format_alert_batch_for_discord,
)
from bot.stock_api_client import chart_data, watchlist  # noqa: E402


logger = logging.getLogger(__name__)


def load_scan_config(config_path: Path) -> dict:
    """Load JSON config for backend alert scanning."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize_watchlist(raw_watchlist: list[str]) -> list[str]:
    """Normalize watchlist values into uppercase ticker symbols."""
    return [ticker.strip().upper() for ticker in raw_watchlist if str(ticker).strip()]


def _print_ranked_summary(ranked_results: list[dict]) -> None:
    """Print compact ranking summary from /watchlist-analyze output."""
    print("\n=== WATCHLIST RANKING (BACKEND) ===")
    if not ranked_results:
        print("No ranked results returned by backend.")
        return

    for index, item in enumerate(ranked_results, start=1):
        ticker = item.get("ticker", "N/A")
        score = item.get("score_breakdown", {}).get("total_score", "N/A")
        label = item.get("label", "N/A")
        print(f"{index:>2}. {ticker:<6} | Score: {score:<3} | Label: {label}")


def _print_failures(failed_tickers: list[dict], chart_failures: list[str]) -> None:
    """Print backend and per-ticker chart fetch failures."""
    if not failed_tickers and not chart_failures:
        return

    print("\n=== FAILURES ===")
    for item in failed_tickers:
        ticker = item.get("ticker", "N/A")
        error = item.get("error", "Unknown backend error")
        print(f"- {ticker}: {error}")
    for line in chart_failures:
        print(f"- {line}")


def run_backend_alert_scan(
    watchlist_tickers: list[str],
    analysis_period: str,
    chart_period: str,
) -> tuple[list[AlertEvent], list[dict], list[dict], list[str]]:
    """Run API-driven watchlist scan and return alerts + diagnostics."""
    if not watchlist_tickers:
        raise ValueError("Watchlist is empty.")

    tickers_csv = ",".join(watchlist_tickers)
    watchlist_payload = watchlist(tickers_csv=tickers_csv, period=analysis_period)

    ranked_results = watchlist_payload.get("ranked_results", [])
    failed_tickers = watchlist_payload.get("failed_tickers", [])
    ranked_map = {str(item.get("ticker", "")).upper(): item for item in ranked_results}

    all_alerts: list[AlertEvent] = []
    chart_failures: list[str] = []

    for ticker in watchlist_tickers:
        summary_row = ranked_map.get(ticker, {})
        try:
            chart_payload = chart_data(ticker=ticker, period=chart_period)
            series = chart_payload.get("series", [])
            all_alerts.extend(
                build_ticker_alerts(
                    ticker=ticker,
                    summary_row=summary_row,
                    series=series,
                )
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.warning("Chart fetch/alert build failed for %s: %s", ticker, exc)
            chart_failures.append(f"{ticker}: {exc}")

    return all_alerts, ranked_results, failed_tickers, chart_failures


def main() -> None:
    """CLI entrypoint for backend-driven alert scan."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    parser = argparse.ArgumentParser(description="Scan watchlist alerts via existing backend APIs.")
    parser.add_argument(
        "--config",
        default="config/alerts_watchlist.json",
        help="Path to backend alert scan config JSON.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_scan_config(config_path)

    watchlist_tickers = _normalize_watchlist(config.get("watchlist", []))
    analysis_period = str(config.get("analysis_period", "5y"))
    chart_period = str(config.get("chart_period", "6mo"))

    alerts, ranked_results, failed_tickers, chart_failures = run_backend_alert_scan(
        watchlist_tickers=watchlist_tickers,
        analysis_period=analysis_period,
        chart_period=chart_period,
    )

    _print_ranked_summary(ranked_results)
    _print_failures(failed_tickers=failed_tickers, chart_failures=chart_failures)

    print("\n=== DISCORD ALERT PAYLOAD ===")
    print(
        format_alert_batch_for_discord(
            alerts=alerts,
            title="📣 Stock Assistant Alerts",
        )
    )


if __name__ == "__main__":
    main()
