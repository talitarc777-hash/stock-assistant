"""Basic unit tests for SMA and RSI indicator logic."""

from __future__ import annotations

import unittest

import pandas as pd

from app.services.indicators import IndicatorInputError, add_technical_indicators


def _build_ohlcv(close_values: list[float]) -> pd.DataFrame:
    """Create a minimal OHLCV DataFrame for indicator tests."""
    return pd.DataFrame(
        {
            "open": close_values,
            "high": close_values,
            "low": close_values,
            "close": close_values,
            "volume": [1_000] * len(close_values),
        }
    )


class IndicatorTests(unittest.TestCase):
    """Test core indicator calculations."""

    def test_sma_20_matches_manual_average(self) -> None:
        """SMA-20 should match direct average of the latest 20 closes."""
        close_values = [float(i) for i in range(1, 26)]  # 1..25
        df = _build_ohlcv(close_values)

        out = add_technical_indicators(df)
        expected_sma_20 = sum(close_values[-20:]) / 20
        actual_sma_20 = float(out.iloc[-1]["sma_20"])

        self.assertAlmostEqual(actual_sma_20, expected_sma_20, places=8)

    def test_rsi_14_reaches_100_for_strict_uptrend(self) -> None:
        """RSI-14 should be very high when closes increase monotonically."""
        close_values = [float(i) for i in range(1, 40)]  # steady gains
        df = _build_ohlcv(close_values)

        out = add_technical_indicators(df)
        latest_rsi = float(out.iloc[-1]["rsi_14"])

        self.assertAlmostEqual(latest_rsi, 100.0, places=8)

    def test_missing_required_columns_raises(self) -> None:
        """Missing OHLCV fields should raise IndicatorInputError."""
        bad_df = pd.DataFrame({"close": [100.0, 101.0, 102.0]})

        with self.assertRaises(IndicatorInputError):
            add_technical_indicators(bad_df)


if __name__ == "__main__":
    unittest.main()
