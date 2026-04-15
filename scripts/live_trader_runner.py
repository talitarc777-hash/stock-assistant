"""Continuous near-live virtual trader runner (simulation only).

Runs a periodic loop:
1. reads alert-enabled users (or explicit --user-id)
2. executes one live trader cycle per user
3. sleeps until next interval
"""

from __future__ import annotations

import argparse
import logging
import time

from app.services.live_virtual_trader import run_live_virtual_trader_now
from app.services.user_profile_service import get_user_profile_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the near-live virtual trader loop.")
    parser.add_argument("--user-id", type=str, default="", help="Optional single user_id to run.")
    parser.add_argument("--interval-seconds", type=int, default=300, help="Loop interval seconds.")
    parser.add_argument("--model-name", type=str, default="logistic_regression", help="Selected model name.")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit.")
    return parser.parse_args()


def _target_users(single_user_id: str) -> list[str]:
    if single_user_id.strip():
        return [single_user_id.strip()]
    rows = get_user_profile_store().list_alert_enabled_user_summaries()
    return [row.user_id for row in rows]


def main() -> int:
    args = _parse_args()
    interval = max(30, int(args.interval_seconds))

    while True:
        users = _target_users(args.user_id)
        if not users:
            logger.info("No users to run. Sleeping...")
        for user_id in users:
            try:
                status = run_live_virtual_trader_now(
                    user_id=user_id,
                    model_name=args.model_name,
                )
                logger.info(
                    "Runner cycle user_id=%s equity=%.2f cash=%.2f decisions=%d",
                    user_id,
                    status.account.get("total_equity", 0.0),
                    status.account.get("cash", 0.0),
                    len(status.latest_decisions),
                )
            except Exception as exc:  # pragma: no cover - runtime defensive
                logger.exception("Runner cycle failed for user_id=%s: %s", user_id, exc)

        if args.once:
            return 0
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
