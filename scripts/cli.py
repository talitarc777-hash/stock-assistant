"""Automation-friendly CLI for stock-assistant workflows."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any

from bootstrap import ensure_project_root_on_path

ensure_project_root_on_path()

from app.backtest.engine import BacktestInputError, run_backtest
from app.services.benchmark import BenchmarkAnalysisError, compare_to_benchmark
from app.services.indicators import IndicatorInputError, add_technical_indicators
from app.services.market_data import EmptyDataError, InvalidTickerError, MarketDataError, get_price_history
from app.services.scoring import ScoringInputError, score_from_indicators

logger = logging.getLogger(__name__)


def _print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _analyze_one(ticker: str, period: str, benchmark: str) -> dict[str, Any]:
    """Run analysis pipeline for one ticker and return structured data."""
    ticker_df = get_price_history(ticker=ticker, period=period)
    benchmark_df = get_price_history(ticker=benchmark, period=period)
    indicators_df = add_technical_indicators(ticker_df)
    score = score_from_indicators(indicators_df)
    benchmark_cmp = compare_to_benchmark(
        ticker_df=ticker_df,
        benchmark_df=benchmark_df,
        benchmark_symbol=benchmark,
    )

    latest = indicators_df.iloc[-1]
    latest_close = float(latest["close"])
    latest_rsi = _safe_float(latest["rsi_14"])
    macd_bullish = (
        bool(float(latest["macd_line"]) > float(latest["macd_signal"]))
        if latest["macd_line"] is not None and latest["macd_signal"] is not None
        else False
    )

    return {
        "ticker": ticker.strip().upper(),
        "period": period,
        "latest_close": latest_close,
        "score_breakdown": {
            "trend_score": score.trend_score,
            "momentum_score": score.momentum_score,
            "confirmation_score": score.confirmation_score,
            "risk_penalty": score.risk_penalty,
            "total_score": score.total_score,
        },
        "label": score.label,
        "action_summary": score.action_summary,
        "explanation_bullets": score.explanations,
        "benchmark_relative": {
            "benchmark": benchmark_cmp.benchmark,
            "returns_pct": benchmark_cmp.returns,
            "benchmark_returns_pct": benchmark_cmp.benchmark_returns,
            "excess_returns_pct": benchmark_cmp.excess_returns,
            "benchmark_strength_score": benchmark_cmp.benchmark_strength_score,
        },
        "indicator_snapshot": {
            "sma_20": _safe_float(latest["sma_20"]),
            "sma_50": _safe_float(latest["sma_50"]),
            "sma_200": _safe_float(latest["sma_200"]),
            "rsi_14": latest_rsi,
            "macd_line": _safe_float(latest["macd_line"]),
            "macd_signal": _safe_float(latest["macd_signal"]),
            "macd_bullish": macd_bullish,
        },
    }


def _load_watchlist_from_config(config_path: str) -> tuple[list[str], str, str]:
    """Load watchlist config used for CLI automation tasks."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    watchlist = [str(item).strip().upper() for item in payload.get("watchlist", []) if str(item).strip()]
    period = str(payload.get("period", "5y"))
    benchmark = str(payload.get("benchmark", "VOO")).strip().upper()
    return watchlist, period, benchmark


def cmd_analyze_ticker(args: argparse.Namespace) -> int:
    """Handle analyze-ticker command."""
    result = _analyze_one(args.ticker, args.period, args.benchmark)
    _print_section(f"ANALYZE TICKER: {result['ticker']}")
    print(f"Period: {result['period']}")
    print(f"Latest close: {result['latest_close']:.2f}")
    print(f"Score: {result['score_breakdown']['total_score']}")
    print(f"Label: {result['label']}")
    print(f"Action: {result['action_summary']}")
    print(f"Benchmark strength score: {result['benchmark_relative']['benchmark_strength_score']}")
    print("\nExplanation:")
    for bullet in result["explanation_bullets"]:
        print(f"- {bullet}")
    return 0


def cmd_analyze_watchlist(args: argparse.Namespace) -> int:
    """Handle analyze-watchlist command."""
    watchlist, default_period, default_benchmark = _load_watchlist_from_config(args.config)
    period = args.period or default_period
    benchmark = args.benchmark or default_benchmark

    if not watchlist:
        raise ValueError("Watchlist is empty in config.")

    rows: list[dict[str, Any]] = []
    failures: list[str] = []

    for ticker in watchlist:
        try:
            rows.append(_analyze_one(ticker, period, benchmark))
        except (
            InvalidTickerError,
            EmptyDataError,
            MarketDataError,
            IndicatorInputError,
            ScoringInputError,
            BenchmarkAnalysisError,
        ) as exc:
            failures.append(f"{ticker}: {exc}")

    rows.sort(key=lambda item: item["score_breakdown"]["total_score"], reverse=True)

    _print_section("WATCHLIST RANKING")
    print("Rank | Ticker | Score | Label                       | Action")
    print("-----+--------+-------+-----------------------------+------------------------")
    for index, item in enumerate(rows, start=1):
        print(
            f"{index:>4} | {item['ticker']:<6} | {item['score_breakdown']['total_score']:>5} | "
            f"{item['label']:<27} | {item['action_summary']}"
        )

    if failures:
        _print_section("WATCHLIST FAILURES")
        for failure in failures:
            print(f"- {failure}")
    return 0


def cmd_backtest(args: argparse.Namespace) -> int:
    """Handle backtest command."""
    price_df = get_price_history(args.ticker, args.period)
    indicators_df = add_technical_indicators(price_df)
    result = run_backtest(indicators_df, transaction_cost_pct=args.transaction_cost_pct)

    _print_section(f"BACKTEST: {args.ticker.strip().upper()}")
    print(f"Period: {args.period}")
    print(f"Transaction cost pct: {args.transaction_cost_pct}")
    print("Metrics:")
    for key, value in result.metrics.items():
        if isinstance(value, float):
            print(f"- {key}: {value:.4f}")
        else:
            print(f"- {key}: {value}")

    print("\nTrade preview (latest 10):")
    preview = result.trades[-10:]
    if not preview:
        print("- No trades generated.")
    else:
        for trade in preview:
            print(
                f"- {trade.entry_date} -> {trade.exit_date} | "
                f"entry {trade.entry_price:.2f} | exit {trade.exit_price:.2f} | "
                f"return {trade.return_pct:.2f}% | {trade.exit_reason}"
            )
    return 0


def cmd_export_report(args: argparse.Namespace) -> int:
    """Handle export-report command."""
    ticker = args.ticker.strip().upper()
    analysis = _analyze_one(ticker, args.period, args.benchmark)
    price_df = get_price_history(ticker, args.period)
    indicators_df = add_technical_indicators(price_df)
    backtest = run_backtest(indicators_df, transaction_cost_pct=args.transaction_cost_pct)

    report_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "ticker": ticker,
        "period": args.period,
        "benchmark": args.benchmark.strip().upper(),
        "analysis": analysis,
        "backtest_metrics": backtest.metrics,
        "backtest_trade_preview": [
            {
                "entry_date": trade.entry_date,
                "entry_price": trade.entry_price,
                "exit_date": trade.exit_date,
                "exit_price": trade.exit_price,
                "return_pct": trade.return_pct,
                "exit_reason": trade.exit_reason,
            }
            for trade in backtest.trades[-20:]
        ],
    }

    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = reports_dir / f"{ticker}_{timestamp}.json"
    output_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

    _print_section("REPORT EXPORTED")
    print(f"Ticker: {ticker}")
    print(f"Path: {output_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build root argument parser and subcommands."""
    parser = argparse.ArgumentParser(description="Stock Assistant automation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_ticker = subparsers.add_parser("analyze-ticker", help="Analyze one ticker.")
    analyze_ticker.add_argument("--ticker", required=True, help="Ticker symbol, e.g. VOO")
    analyze_ticker.add_argument("--period", default="5y", help="History period, default 5y")
    analyze_ticker.add_argument("--benchmark", default="VOO", help="Benchmark ticker, default VOO")
    analyze_ticker.set_defaults(func=cmd_analyze_ticker)

    analyze_watchlist = subparsers.add_parser(
        "analyze-watchlist", help="Analyze watchlist from config/watchlist.json."
    )
    analyze_watchlist.add_argument(
        "--config",
        default="config/watchlist.json",
        help="Watchlist config path, default config/watchlist.json",
    )
    analyze_watchlist.add_argument("--period", default=None, help="Override period from config.")
    analyze_watchlist.add_argument("--benchmark", default=None, help="Override benchmark from config.")
    analyze_watchlist.set_defaults(func=cmd_analyze_watchlist)

    backtest = subparsers.add_parser("backtest", help="Run strategy backtest for one ticker.")
    backtest.add_argument("--ticker", required=True, help="Ticker symbol, e.g. VOO")
    backtest.add_argument("--period", default="10y", help="History period, default 10y")
    backtest.add_argument(
        "--transaction-cost-pct",
        type=float,
        default=0.0,
        help="Optional one-way transaction cost in decimal, e.g. 0.001",
    )
    backtest.set_defaults(func=cmd_backtest)

    export_report = subparsers.add_parser(
        "export-report", help="Export analysis + backtest report to reports/*.json"
    )
    export_report.add_argument("--ticker", required=True, help="Ticker symbol, e.g. VOO")
    export_report.add_argument("--period", default="5y", help="History period, default 5y")
    export_report.add_argument("--benchmark", default="VOO", help="Benchmark ticker, default VOO")
    export_report.add_argument(
        "--transaction-cost-pct",
        type=float,
        default=0.0,
        help="Optional one-way transaction cost in decimal, e.g. 0.001",
    )
    export_report.set_defaults(func=cmd_export_report)

    return parser


def main() -> int:
    """CLI entrypoint."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    parser = build_parser()
    args = parser.parse_args()
    logger.info("CLI command invoked: %s", args.command)

    try:
        return int(args.func(args))
    except (
        FileNotFoundError,
        ValueError,
        InvalidTickerError,
        EmptyDataError,
        MarketDataError,
        IndicatorInputError,
        ScoringInputError,
        BenchmarkAnalysisError,
        BacktestInputError,
    ) as exc:
        _print_section("ERROR")
        print(str(exc))
        logger.exception("CLI command failed")
        return 1
    except Exception as exc:  # pragma: no cover - defensive guard
        _print_section("ERROR")
        print("Unexpected error occurred.")
        logger.exception("Unexpected CLI failure: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
