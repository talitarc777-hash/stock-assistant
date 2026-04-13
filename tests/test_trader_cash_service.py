"""Tests for live trader cash and monthly contribution application logic."""

from __future__ import annotations

import unittest
import uuid
from pathlib import Path

from app.services.trader_cash_service import TraderCashService


class TraderCashServiceTests(unittest.TestCase):
    def test_apply_monthly_contributions_prevents_double_count_and_applies_delta(self) -> None:
        db_path = Path("data") / "test_trader_cash_service.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        service = TraderCashService(db_path=str(db_path))
        user_id = f"user-{uuid.uuid4().hex}"

        events_first = service.apply_monthly_contributions(
            user_id=user_id,
            contribution_schedule={"2026-04": 1000.0, "2026-05": 500.0},
            current_month="2026-05",
        )
        snapshot_first = service.get_account_snapshot(user_id)

        self.assertEqual(len(events_first), 2)
        self.assertEqual(snapshot_first.cash, 1500.0)
        self.assertEqual(snapshot_first.total_contributions_applied, 1500.0)

        events_second = service.apply_monthly_contributions(
            user_id=user_id,
            contribution_schedule={"2026-04": 1000.0, "2026-05": 500.0},
            current_month="2026-05",
        )
        snapshot_second = service.get_account_snapshot(user_id)

        self.assertEqual(len(events_second), 0)
        self.assertEqual(snapshot_second.cash, 1500.0)
        self.assertEqual(snapshot_second.total_contributions_applied, 1500.0)

        events_third = service.apply_monthly_contributions(
            user_id=user_id,
            contribution_schedule={"2026-04": 1000.0, "2026-05": 800.0},
            current_month="2026-05",
        )
        snapshot_third = service.get_account_snapshot(user_id)

        self.assertEqual(len(events_third), 1)
        self.assertEqual(events_third[0].month, "2026-05")
        self.assertEqual(events_third[0].delta_applied_now, 300.0)
        self.assertEqual(snapshot_third.cash, 1800.0)
        self.assertEqual(snapshot_third.total_contributions_applied, 1800.0)
