"""Tests for immutable virtual account ledger behavior."""

from __future__ import annotations

import unittest
from pathlib import Path
from uuid import uuid4

from app.services.account_ledger_service import AccountLedgerError, AccountLedgerService


class AccountLedgerServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = Path(f"data/test_account_ledger_{uuid4().hex}.db")
        self.service = AccountLedgerService(db_path=str(self.db_path))

    def tearDown(self) -> None:
        if self.db_path.exists():
            try:
                self.db_path.unlink()
            except PermissionError:
                pass

    def test_monthly_contribution_is_immutable(self) -> None:
        self.service.create_monthly_contribution("u1", "2026-04", 1000.0)
        with self.assertRaises(AccountLedgerError):
            self.service.create_monthly_contribution("u1", "2026-04", 1200.0)

    def test_summary_rebuilds_from_ledger_events(self) -> None:
        self.service.create_monthly_contribution("u1", "2026-04", 1000.0)
        self.service.create_manual_deposit("u1", 500.0)
        self.service.create_trade_event(
            user_id="u1",
            action="buy",
            ticker="VOO",
            quantity=3.0,
            price=100.0,
        )
        summary = self.service.build_account_summary("u1", latest_prices={"VOO": 110.0})
        self.assertAlmostEqual(summary["cash"], 1200.0, places=6)
        self.assertAlmostEqual(summary["holdings_value"], 330.0, places=6)
        self.assertAlmostEqual(summary["total_account_value"], 1530.0, places=6)
        self.assertEqual(len(summary["holdings"]), 1)


if __name__ == "__main__":
    unittest.main()
