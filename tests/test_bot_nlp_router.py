"""Tests for the Discord bot's rule-based natural-language router."""

from __future__ import annotations

import unittest

from bot.nlp_router import parse_natural_language_message
from bot.ticker_map import extract_tickers_from_text, resolve_ticker_phrase


class NaturalLanguageRouterTests(unittest.TestCase):
    """Keep the rule-based parser predictable and beginner-friendly."""

    def test_set_language_to_chinese(self) -> None:
        parsed = parse_natural_language_message("set my language to Chinese")
        self.assertEqual(parsed.intent, "set_language")
        self.assertEqual(parsed.language, "zh")

    def test_reply_in_english_only(self) -> None:
        parsed = parse_natural_language_message("reply in English only")
        self.assertEqual(parsed.intent, "set_language")
        self.assertEqual(parsed.language, "en")

    def test_use_bilingual_replies(self) -> None:
        parsed = parse_natural_language_message("use bilingual replies")
        self.assertEqual(parsed.intent, "set_language")
        self.assertEqual(parsed.language, "bilingual")

    def test_enable_compact_mode(self) -> None:
        parsed = parse_natural_language_message("turn on compact mode")
        self.assertEqual(parsed.intent, "set_compact")
        self.assertTrue(parsed.compact_mode)

    def test_add_multiple_tickers(self) -> None:
        parsed = parse_natural_language_message("add AAPL and NVDA to my watchlist")
        self.assertEqual(parsed.intent, "add_watchlist")
        self.assertEqual(parsed.tickers, ["AAPL", "NVDA"])

    def test_add_lowercase_ticker(self) -> None:
        parsed = parse_natural_language_message("add acm to my watchlist")
        self.assertEqual(parsed.intent, "add_watchlist")
        self.assertEqual(parsed.tickers, ["ACM"])

    def test_add_brk_dot_b_normalizes_to_dash(self) -> None:
        parsed = parse_natural_language_message("add BRK.B to my watchlist")
        self.assertEqual(parsed.intent, "add_watchlist")
        self.assertEqual(parsed.tickers, ["BRK-B"])

    def test_company_name_resolves_for_analyze(self) -> None:
        parsed = parse_natural_language_message("check Apple")
        self.assertEqual(parsed.intent, "analyze")
        self.assertEqual(parsed.tickers, ["AAPL"])

    def test_analyze_apple_phrase(self) -> None:
        parsed = parse_natural_language_message("analyze Apple")
        self.assertEqual(parsed.intent, "analyze")
        self.assertEqual(parsed.tickers, ["AAPL"])

    def test_what_do_you_think_about_voo(self) -> None:
        parsed = parse_natural_language_message("what do you think about VOO")
        self.assertEqual(parsed.intent, "analyze")
        self.assertEqual(parsed.tickers, ["VOO"])

    def test_forecast_company_name(self) -> None:
        parsed = parse_natural_language_message("what is the outlook for Tesla")
        self.assertEqual(parsed.intent, "forecast")
        self.assertEqual(parsed.tickers, ["TSLA"])

    def test_show_me_the_forecast_for_microsoft(self) -> None:
        parsed = parse_natural_language_message("show me the forecast for Microsoft")
        self.assertEqual(parsed.intent, "forecast")
        self.assertEqual(parsed.tickers, ["MSFT"])

    def test_forecast_berkshire_resolves_to_brk_b(self) -> None:
        parsed = parse_natural_language_message("show me the forecast for Berkshire")
        self.assertEqual(parsed.intent, "forecast")
        self.assertEqual(parsed.tickers, ["BRK-B"])

    def test_bilingual_language_phrase(self) -> None:
        parsed = parse_natural_language_message("speak in English and Chinese")
        self.assertEqual(parsed.intent, "set_language")
        self.assertEqual(parsed.language, "bilingual")

    def test_show_watchlist(self) -> None:
        parsed = parse_natural_language_message("show my watchlist")
        self.assertEqual(parsed.intent, "show_watchlist")

    def test_what_is_in_my_watchlist(self) -> None:
        parsed = parse_natural_language_message("what is in my watchlist")
        self.assertEqual(parsed.intent, "show_watchlist")

    def test_remove_nvidia_from_watchlist(self) -> None:
        parsed = parse_natural_language_message("remove Nvidia from my watchlist")
        self.assertEqual(parsed.intent, "remove_watchlist")
        self.assertEqual(parsed.tickers, ["NVDA"])

    def test_help_hint_for_missing_forecast_ticker(self) -> None:
        parsed = parse_natural_language_message("forecast please")
        self.assertIsNone(parsed.intent)
        self.assertTrue(parsed.needs_help_hint)
        self.assertIn("forecast VOO", parsed.message or "")

    def test_show_settings(self) -> None:
        parsed = parse_natural_language_message("what are my settings")
        self.assertEqual(parsed.intent, "show_settings")

    def test_unclear_stock_related_message_returns_hint(self) -> None:
        parsed = parse_natural_language_message("can you help with my watchlist thing")
        self.assertIsNone(parsed.intent)
        self.assertTrue(parsed.needs_help_hint)

    def test_extract_company_names_without_random_words(self) -> None:
        match = extract_tickers_from_text("check Apple and Microsoft")
        self.assertEqual(match.tickers, ["AAPL", "MSFT"])

    def test_resolve_extended_company_name(self) -> None:
        match = resolve_ticker_phrase("Microsoft Corporation")
        self.assertEqual(match.tickers, ["MSFT"])

    def test_ambiguous_vanguard_name_requests_clarification(self) -> None:
        match = extract_tickers_from_text("show analysis for Vanguard")
        self.assertTrue(match.ambiguous)
        self.assertIn("Please use the ticker symbol", match.message or "")

    def test_extract_brk_dot_b_is_single_symbol(self) -> None:
        match = extract_tickers_from_text("add BRK.B to my watchlist")
        self.assertEqual(match.tickers, ["BRK-B"])


if __name__ == "__main__":
    unittest.main()
