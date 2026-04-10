"""Tests for the SQLite-backed monthly contribution store."""

from __future__ import annotations

import unittest
from pathlib import Path
from uuid import uuid4

from app.services.monthly_contribution_service import START_MONTH, MonthlyContributionStore


class MonthlyContributionStoreTests(unittest.TestCase):
    """Verify contribution initialization and update behavior."""

    def setUp(self) -> None:
        self.test_dir = Path("data") / "test_monthly_contributions"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.test_dir / f"monthly_contributions_{uuid4().hex}.db"
        self.store = MonthlyContributionStore(db_path=str(self.db_path))

    def tearDown(self) -> None:
        if self.db_path.exists():
            try:
                self.db_path.unlink()
            except PermissionError:
                pass

    def test_initialize_starts_from_april_2026(self) -> None:
        records = self.store.initialize_for_user("demo-user")

        self.assertGreaterEqual(len(records), 1)
        self.assertEqual(records[0].month, START_MONTH)
        self.assertEqual(records[0].amount, 0.0)

    def test_update_amount_persists_non_fixed_monthly_value(self) -> None:
        self.store.initialize_for_user("demo-user")
        updated = self.store.update_amount("demo-user", "2026-04", 1500)
        amount_map = self.store.get_amount_map("demo-user")

        self.assertEqual(updated.amount, 1500.0)
        self.assertEqual(amount_map["2026-04"], 1500.0)


if __name__ == "__main__":
    unittest.main()
