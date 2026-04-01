"""Run simulation-only paper trading status for one ticker.

This script never connects to brokers and never executes real orders.
"""

from __future__ import annotations

import argparse
import logging

from bootstrap import ensure_project_root_on_path

ensure_project_root_on_path()

from app.services.indicators import add_technical_indicators
from app.services.market_data import get_price_history
from app.services.paper_simulator import run_paper_simulation

logger = logging.getLogger(__name__)


def main() -> int:
    """CLI entrypoint for paper simulation."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    parser = argparse.ArgumentParser(description="Run simulation-only paper trading status.")
    parser.add_argument("--ticker", default="VOO", help="Ticker symbol, default VOO")
    parser.add_argument("--period", default="5y", help="History period, default 5y")
    parser.add_argument(
        "--initial-cash",
        type=float,
        default=10_000.0,
        help="Simulation starting cash, default 10000.0",
    )
    args = parser.parse_args()

    print("\n=== PAPER SIMULATION ONLY ===")
    print("No real-money trading. No broker execution. Hypothetical events only.")

    try:
        price_df = get_price_history(ticker=args.ticker, period=args.period)
        indicators_df = add_technical_indicators(price_df)
        result = run_paper_simulation(
            ticker=args.ticker,
            indicators_df=indicators_df,
            initial_cash=args.initial_cash,
        )
    except Exception as exc:
        logger.exception("Paper simulation failed: %s", exc)
        print("\nERROR:", exc)
        return 1

    latest_close = float(indicators_df.iloc[-1]["close"])

    print("\n=== PAPER STATUS ===")
    print(f"Ticker: {result.ticker}")
    print(f"Latest close: {latest_close:.2f}")
    print(f"Initial cash: {result.initial_cash:.2f}")
    print(f"Cash: {result.cash:.2f}")
    print(f"Position qty: {result.position_qty:.6f}")
    print(f"Avg entry price: {result.avg_entry_price if result.avg_entry_price is not None else 'N/A'}")
    print(f"Position market value: {result.position_market_value:.2f}")
    print(f"Total equity: {result.total_equity:.2f}")
    print(f"Realized PnL: {result.realized_pnl:.2f}")
    print(f"Unrealized PnL: {result.unrealized_pnl:.2f}")
    print(f"Event count: {len(result.events)}")

    print("\n=== LATEST EVENTS (up to 20) ===")
    preview = result.events[-20:]
    if not preview:
        print("- No would-buy/would-sell events generated for this window.")
    else:
        for event in preview:
            print(
                f"- {event.date} | {event.event} | price={event.price:.2f} "
                f"| qty={event.quantity:.6f} | realized_pnl={event.realized_pnl:.2f} | {event.note}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

