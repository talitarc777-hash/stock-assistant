"""Tests for the Discord bot settings store."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import bot.settings_store as settings_store


class SettingsStoreTests(unittest.TestCase):
    """Verify per-user settings persistence and safe fallbacks."""

    def setUp(self) -> None:
        self.test_dir = Path("data") / "test_settings_store"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.settings_path = self.test_dir / f"discord_user_settings_{uuid4().hex}.json"

        self.path_patcher = patch.object(settings_store, "USER_SETTINGS_PATH", self.settings_path)
        self.watchlist_patcher = patch.object(
            settings_store,
            "WATCHLIST_TICKERS",
            ["VOO", "SPY", "QQQ"],
        )
        self.reply_language_patcher = patch.object(settings_store, "REPLY_LANGUAGE", "zh")

        self.path_patcher.start()
        self.watchlist_patcher.start()
        self.reply_language_patcher.start()

    def tearDown(self) -> None:
        self.path_patcher.stop()
        self.watchlist_patcher.stop()
        self.reply_language_patcher.stop()
        if self.settings_path.exists():
            self.settings_path.unlink()

    def test_get_user_settings_returns_defaults_for_new_user(self) -> None:
        settings = settings_store.get_user_settings(123)

        self.assertEqual(settings["language"], "zh")
        self.assertFalse(settings["compact_mode"])
        self.assertEqual(settings["default_watchlist"], [])

    def test_language_setting_persists(self) -> None:
        settings_store.set_user_language(123, "bilingual")
        settings = settings_store.get_user_settings(123)

        self.assertEqual(settings["language"], "bilingual")

    def test_compact_mode_setting_persists(self) -> None:
        settings_store.set_user_compact_mode(123, True)
        settings = settings_store.get_user_settings(123)

        self.assertTrue(settings["compact_mode"])

    def test_watchlist_setting_persists_and_normalizes(self) -> None:
        settings_store.set_user_watchlist(123, ["voo", " qqq ", "QQQ", "aapl"])
        settings = settings_store.get_user_settings(123)

        self.assertEqual(settings["default_watchlist"], ["VOO", "QQQ", "AAPL"])

    def test_reset_settings_restores_defaults(self) -> None:
        settings_store.set_user_language(123, "en")
        settings_store.set_user_compact_mode(123, True)
        settings_store.set_user_watchlist(123, ["AAPL", "MSFT"])

        settings = settings_store.reset_user_settings(123)

        self.assertEqual(settings["language"], "zh")
        self.assertFalse(settings["compact_mode"])
        self.assertEqual(settings["default_watchlist"], [])
        self.assertEqual(settings_store.get_user_settings(123)["default_watchlist"], [])

    def test_add_ticker_uses_system_default_when_user_has_no_saved_watchlist(self) -> None:
        settings = settings_store.add_user_ticker(123, "AAPL")

        self.assertEqual(settings["default_watchlist"], ["VOO", "SPY", "QQQ", "AAPL"])

    def test_remove_ticker_uses_system_default_when_user_has_no_saved_watchlist(self) -> None:
        settings = settings_store.remove_user_ticker(123, "SPY")

        self.assertEqual(settings["default_watchlist"], ["VOO", "QQQ"])

    def test_get_effective_watchlist_falls_back_to_system_default(self) -> None:
        watchlist = settings_store.get_effective_watchlist(123)

        self.assertEqual(watchlist, ["VOO", "SPY", "QQQ"])


if __name__ == "__main__":
    unittest.main()
