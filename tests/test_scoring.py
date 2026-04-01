"""Unit tests for main scoring behavior and action labeling."""

from __future__ import annotations

import unittest

import pandas as pd

from app.services.scoring import ScoringInputError, score_from_indicators


def _build_base_df() -> pd.DataFrame:
    """
    Build a 21-row indicator DataFrame for deterministic scoring tests.

    21 rows are required because the scoring logic compares latest close
    to close from 20 trading days ago.
    """
    rows = 21
    close_values = [100.0] + [120.0] * (rows - 1)
    return pd.DataFrame(
        {
            "close": close_values,
            "sma_20": [113.0] * rows,
            "sma_50": [112.0] * rows,
            "sma_200": [90.0] * rows,
            "rsi_14": [55.0] * rows,
            "macd_line": [1.5] * rows,
            "macd_signal": [0.5] * rows,
            "avg_volume_20": [1000.0] * rows,
            "volume": [1500.0] * rows,
            "distance_from_52w_high_pct": [-5.0] * rows,
            "rolling_volatility_20_pct": [20.0] * rows,
            "drawdown_from_peak_pct": [-5.0] * rows,
        }
    )


class ScoringTests(unittest.TestCase):
    """Main scoring behavior tests."""

    def test_bullish_setup_scores_80_and_strong_candidate(self) -> None:
        """Bullish setup should produce expected high score and action summary."""
        df = _build_base_df()
        result = score_from_indicators(df)

        self.assertEqual(result.trend_score, 40)
        self.assertEqual(result.momentum_score, 25)
        self.assertEqual(result.confirmation_score, 15)
        self.assertEqual(result.risk_penalty, 0)
        self.assertEqual(result.total_score, 80)
        self.assertEqual(result.label, "strong watchlist candidate")
        self.assertEqual(result.action_summary, "accumulate on pullbacks")

    def test_overextended_setup_uses_avoid_chasing_action(self) -> None:
        """Overextended but still decent score should map to 'avoid chasing'."""
        df = _build_base_df()
        df.loc[:, "rsi_14"] = 76.0  # removes RSI momentum + adds overbought penalty

        result = score_from_indicators(df)

        self.assertEqual(result.total_score, 65)
        self.assertEqual(result.label, "watch closely")
        self.assertEqual(result.action_summary, "avoid chasing")

    def test_weak_setup_maps_to_reduce_risk_watch(self) -> None:
        """Weak setup with risk penalties should map to avoid/reduce-risk behavior."""
        df = _build_base_df()
        df.loc[:, "close"] = [100.0] + [80.0] * 20
        df.loc[:, "sma_20"] = 90.0
        df.loc[:, "sma_50"] = 95.0
        df.loc[:, "sma_200"] = 100.0
        df.loc[:, "rsi_14"] = 80.0
        df.loc[:, "macd_line"] = -0.5
        df.loc[:, "macd_signal"] = 0.1
        df.loc[:, "volume"] = 900.0
        df.loc[:, "avg_volume_20"] = 1000.0
        df.loc[:, "distance_from_52w_high_pct"] = -20.0
        df.loc[:, "rolling_volatility_20_pct"] = 50.0
        df.loc[:, "drawdown_from_peak_pct"] = -20.0

        result = score_from_indicators(df)

        self.assertEqual(result.total_score, 0)
        self.assertEqual(result.label, "avoid for now")
        self.assertEqual(result.action_summary, "reduce risk watch")

    def test_missing_columns_raise_scoring_input_error(self) -> None:
        """Missing required indicator columns should raise ScoringInputError."""
        with self.assertRaises(ScoringInputError):
            score_from_indicators(pd.DataFrame({"close": [100.0, 101.0]}))


if __name__ == "__main__":
    unittest.main()

