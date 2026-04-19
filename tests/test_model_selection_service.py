"""Tests for model resolution priority and requested-model validation."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.services.model_selection_service import resolve_selected_model_name


class ModelSelectionPriorityTests(unittest.TestCase):
    @patch("app.services.model_selection_service.list_available_model_options", return_value=[])
    @patch("app.services.model_selection_service.list_compatible_saved_model_candidates")
    @patch("app.services.model_selection_service.get_model_lifecycle_service")
    def test_requested_model_does_not_bypass_production(
        self,
        lifecycle_mock,
        saved_candidates_mock,
        _options_mock,
    ) -> None:
        lifecycle_mock.return_value.get_production_model.side_effect = [
            {"model_name": "random_forest"},
            None,
        ]
        saved_candidates_mock.return_value = []

        resolved = resolve_selected_model_name(
            user_id=None,
            requested_model_name="linear_regression",
            ticker="VOO",
            period="5y",
            target_name="target_5d_updown",
        )
        self.assertEqual(resolved, "random_forest")

    @patch("app.services.model_selection_service.list_available_model_options", return_value=[])
    @patch("app.services.model_selection_service.list_compatible_saved_model_candidates")
    @patch("app.services.model_selection_service.get_model_lifecycle_service")
    def test_uses_compatible_saved_model_before_requested(
        self,
        lifecycle_mock,
        saved_candidates_mock,
        _options_mock,
    ) -> None:
        lifecycle_mock.return_value.get_production_model.return_value = None
        saved_candidates_mock.side_effect = [
            [{"ticker": "VOO", "model_name": "gradient_boosting", "source": "saved_exact_ticker_model"}],
        ]

        resolved = resolve_selected_model_name(
            user_id=None,
            requested_model_name="linear_regression",
            ticker="VOO",
            period="5y",
            target_name="target_5d_updown",
        )
        self.assertEqual(resolved, "gradient_boosting")

    @patch("app.services.model_selection_service.list_available_model_options", return_value=[])
    @patch("app.services.model_selection_service.list_compatible_saved_model_candidates")
    @patch("app.services.model_selection_service.get_model_lifecycle_service")
    def test_requested_model_used_only_when_compatible_artifact_exists(
        self,
        lifecycle_mock,
        saved_candidates_mock,
        _options_mock,
    ) -> None:
        lifecycle_mock.return_value.get_production_model.return_value = None
        saved_candidates_mock.side_effect = [
            [],
            [{"ticker": "GLOBAL", "model_name": "linear_regression", "source": "saved_compatible_requested_model"}],
        ]

        resolved = resolve_selected_model_name(
            user_id=None,
            requested_model_name="linear_regression",
            ticker="QQQ",
            period="5y",
            target_name="target_5d_updown",
        )
        self.assertEqual(resolved, "linear_regression")


if __name__ == "__main__":
    unittest.main()

