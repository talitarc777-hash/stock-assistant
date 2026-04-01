"""Daily watchlist scan script with ranking and OpenClaw-ready alerts."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from bootstrap import ensure_project_root_on_path

ensure_project_root_on_path()

from app.services.alerts import (
    AlertGenerationError,
    TickerScanResult,
    generate_alert_messages,
    summarize_attractive_and_risky,
)
from app.services.indicators import IndicatorInputError, add_technical_indicators
from app.services.market_data import EmptyDataError, InvalidTickerError, MarketDataError, get_price_history
from app.services.openclaw_adapter import OpenClawNotifier
from app.services.scoring import ScoringInputError, score_from_indicators

logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> dict:
    """Load watchlist scan config from JSON file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def scan_one_ticker(ticker: str, period: str) -> TickerScanResult:
    """Run indicator + scoring + alert generation for a single ticker."""
    price_df = get_price_history(ticker=ticker, period=period)
    indicators_df = add_technical_indicators(price_df)
    score = score_from_indicators(indicators_df)
    alerts = generate_alert_messages(ticker=ticker, indicators_df=indicators_df)

    latest_close = float(indicators_df.iloc[-1]["close"])
    return TickerScanResult(
        ticker=ticker,
        latest_close=latest_close,
        total_score=score.total_score,
        label=score.label,
        action_summary=score.action_summary,
        alerts=alerts,
    )


def print_ranked_summary(results: list[TickerScanResult]) -> None:
    """Print a compact ranked summary table."""
    print("\n=== DAILY WATCHLIST RANKING ===")
    print("Rank | Ticker | Score | Label                       | Action")
    print("-----+--------+-------+-----------------------------+------------------------")
    for index, item in enumerate(results, start=1):
        print(
            f"{index:>4} | {item.ticker:<6} | {item.total_score:>5} | "
            f"{item.label:<27} | {item.action_summary}"
        )

    summary = summarize_attractive_and_risky(results)
    attractive = ", ".join(summary["attractive"]) if summary["attractive"] else "None"
    risky = ", ".join(summary["risky"]) if summary["risky"] else "None"
    print("\nAttractive tickers (score >= 65):", attractive)
    print("Risky tickers (score < 50):", risky)


def build_openclaw_messages(results: list[TickerScanResult]) -> list[str]:
    """Build notification lines in a channel-friendly, plain-text format."""
    messages: list[str] = []
    messages.append("OPENCLAW_SCAN|TYPE=SUMMARY|SOURCE=stock-assistant")
    for item in results:
        messages.append(
            "OPENCLAW_SCAN|TYPE=RANKED|"
            f"TICKER={item.ticker}|SCORE={item.total_score}|LABEL={item.label}|ACTION={item.action_summary}"
        )
        for alert in item.alerts:
            messages.append(f"OPENCLAW_SCAN|TYPE=ALERT|TICKER={item.ticker}|MESSAGE={alert}")
    return messages


def main() -> None:
    """CLI entrypoint for the daily watchlist scan."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    parser = argparse.ArgumentParser(description="Run daily stock-assistant watchlist scan.")
    parser.add_argument(
        "--config",
        default="config/watchlist.json",
        help="Path to watchlist JSON config file.",
    )
    parser.add_argument(
        "--send-openclaw",
        action="store_true",
        help="Invoke OpenClaw adapter placeholder with generated messages.",
    )
    args = parser.parse_args()

    try:
        config_path = Path(args.config)
        logger.info("Running daily scan with config=%s", config_path)
        config = load_config(config_path)

        watchlist = [ticker.strip().upper() for ticker in config.get("watchlist", []) if ticker.strip()]
        period = str(config.get("period", "5y"))

        if not watchlist:
            raise ValueError("Config must contain at least one ticker in 'watchlist'.")

        results: list[TickerScanResult] = []
        failures: list[str] = []

        for ticker in watchlist:
            try:
                results.append(scan_one_ticker(ticker=ticker, period=period))
                logger.info("Scanned ticker=%s", ticker)
            except (
                InvalidTickerError,
                EmptyDataError,
                MarketDataError,
                IndicatorInputError,
                ScoringInputError,
                AlertGenerationError,
            ) as exc:
                failures.append(f"{ticker}: {exc}")
                logger.warning("Ticker scan failed for %s: %s", ticker, exc)

        results.sort(key=lambda item: item.total_score, reverse=True)
        print_ranked_summary(results)

        if failures:
            print("\n=== FAILURES ===")
            for failure in failures:
                print("-", failure)

        messages = build_openclaw_messages(results)
        print("\n=== OPENCLAW-READY MESSAGES ===")
        for message in messages:
            print(message)

        if args.send_openclaw:
            notifier = OpenClawNotifier()
            notifier.send_messages(messages)
            print("\nOpenClaw adapter placeholder invoked (log-only mode).")
            logger.info("OpenClaw placeholder send invoked with %d messages", len(messages))
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Daily scan failed: %s", exc)
        raise


if __name__ == "__main__":
    main()
