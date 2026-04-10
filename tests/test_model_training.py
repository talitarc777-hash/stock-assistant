"""Tests for baseline model training helpers."""

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

try:
    from app.services.model_training import (
        ModelTrainingError,
        _choose_time_series_splits,
        train_baseline_model,
    )
    SKLEARN_AVAILABLE = True
except ModuleNotFoundError:
    ModelTrainingError = ValueError  # type: ignore[assignment]
    _choose_time_series_splits = None
    train_baseline_model = None
    SKLEARN_AVAILABLE = False


def _build_synthetic_dataset(row_count: int = 100) -> pd.DataFrame:
    """Create a deterministic numeric dataset for model-training tests."""
    dates = pd.date_range("2024-01-01", periods=row_count, freq="B")
    base = np.linspace(100.0, 140.0, row_count)
    wave = np.sin(np.linspace(0, 6, row_count))
    close = base + wave

    frame = pd.DataFrame(
        {
            "date": dates,
            "ticker": ["TEST"] * row_count,
            "benchmark": ["VOO"] * row_count,
            "open": close - 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "adj_close": close,
            "volume": np.linspace(1_000_000, 1_500_000, row_count),
            "return_1d_pct": pd.Series(close).pct_change().fillna(0.0) * 100,
            "sma_20": pd.Series(close).rolling(20, min_periods=1).mean(),
            "sma_50": pd.Series(close).rolling(50, min_periods=1).mean(),
            "sma_200": pd.Series(close).rolling(60, min_periods=1).mean(),
            "rsi_14": np.linspace(45.0, 65.0, row_count),
            "macd_line": np.linspace(-1.0, 1.0, row_count),
            "macd_signal": np.linspace(-1.2, 0.8, row_count),
            "macd_histogram": np.linspace(0.2, 0.2, row_count),
            "rolling_volatility_20_pct": np.linspace(10.0, 18.0, row_count),
            "distance_from_52w_high_pct": np.linspace(-8.0, -1.0, row_count),
            "benchmark_strength_score": np.where(np.arange(row_count) % 2 == 0, 75, 50),
            "article_count": np.where(np.arange(row_count) % 3 == 0, 2, 0),
            "average_sentiment": np.where(np.arange(row_count) % 4 == 0, 0.2, -0.1),
            "positive_article_ratio": np.where(np.arange(row_count) % 4 == 0, 1.0, 0.0),
            "negative_article_ratio": np.where(np.arange(row_count) % 5 == 0, 0.5, 0.0),
        }
    )

    future_return = ((pd.Series(close).shift(-5) / pd.Series(close)) - 1) * 100
    frame["target_5d_return"] = future_return
    frame["target_5d_updown"] = (future_return > 0).astype("Int64")
    frame["target_20d_regime"] = "neutral"
    return frame


@unittest.skipUnless(SKLEARN_AVAILABLE, "scikit-learn is required for model-training tests")
class ModelTrainingTests(unittest.TestCase):
    """Verify core baseline-model training behavior."""

    def test_choose_time_series_splits_rejects_small_datasets(self) -> None:
        with self.assertRaises(ModelTrainingError):
            _choose_time_series_splits(20)

    def test_train_baseline_model_saves_classification_artifacts(self) -> None:
        dataset_df = _build_synthetic_dataset()

        with tempfile.TemporaryDirectory() as temp_dir:
            result = train_baseline_model(
                dataset_df=dataset_df,
                ticker="TEST",
                period="2y",
                target_name="target_5d_updown",
                task_type="classification",
                model_name="logistic_regression",
                output_dir=temp_dir,
            )

            self.assertEqual(result.task_type, "classification")
            self.assertGreater(result.metrics["row_count"], 0)
            self.assertIn("accuracy", result.metrics["metrics"])
            self.assertIn("precision", result.metrics["metrics"])
            self.assertIn("recall", result.metrics["metrics"])
            self.assertFalse(result.predictions.empty)
            self.assertFalse(result.evaluation_table.empty)
            self.assertIn("confidence_score", result.evaluation_table.columns)
            self.assertIn("hit_miss", result.evaluation_table.columns)
            self.assertIn("technical_state_summary", result.evaluation_table.columns)
            self.assertIn("news_sentiment_summary", result.evaluation_table.columns)
            self.assertIn("benchmark_strength_summary", result.evaluation_table.columns)
            self.assertIn("explanation", result.evaluation_table.columns)
            self.assertTrue(Path(result.artifact.model_path).exists())
            self.assertTrue(Path(result.artifact.feature_list_path).exists())
            self.assertTrue(Path(result.artifact.metrics_path).exists())
            self.assertTrue(Path(result.artifact.predictions_path).exists())
            self.assertTrue(Path(result.artifact.evaluation_table_path).exists())

    def test_train_baseline_model_saves_regression_artifacts(self) -> None:
        dataset_df = _build_synthetic_dataset()

        with tempfile.TemporaryDirectory() as temp_dir:
            result = train_baseline_model(
                dataset_df=dataset_df,
                ticker="TEST",
                period="2y",
                target_name="target_5d_return",
                task_type="regression",
                model_name="linear_regression",
                output_dir=temp_dir,
            )

            self.assertEqual(result.task_type, "regression")
            self.assertIn("rmse", result.metrics["metrics"])
            self.assertFalse(result.predictions.empty)
            self.assertFalse(result.evaluation_table.empty)
            self.assertIn("actual_future_result", result.evaluation_table.columns)
            self.assertIn("hit_miss", result.evaluation_table.columns)
            self.assertIn("explanation", result.evaluation_table.columns)


if __name__ == "__main__":
    unittest.main()
