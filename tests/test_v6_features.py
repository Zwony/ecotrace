"""EcoTrace v6.0 Feature Tests — Live Grid API & Auto-Update System.

Tests use ``unittest.mock`` to simulate external service responses without
requiring actual API keys or network access. Each test verifies both the
success path and the graceful fallback behavior.

Usage:
    python -m pytest tests/test_v6_features.py -v
"""

import unittest
from unittest.mock import patch, MagicMock
import json


class TestLiveGridAPI(unittest.TestCase):
    """Tests for the Electricity Maps Live Grid API integration."""

    def test_fetch_live_carbon_intensity_success(self):
        """Verifies that a valid API response correctly returns the intensity value."""
        from ecotrace.config import fetch_live_carbon_intensity

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "zone": "TR",
            "carbonIntensity": 482,
            "datetime": "2026-03-30T15:00:00.000Z",
            "updatedAt": "2026-03-30T14:55:00.000Z"
        }

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = fetch_live_carbon_intensity("TR", "test-api-key")
            self.assertEqual(result, 482.0)
            mock_get.assert_called_once()

    def test_fetch_live_carbon_intensity_no_key(self):
        """Verifies that None is returned when no API key is provided."""
        from ecotrace.config import fetch_live_carbon_intensity

        result = fetch_live_carbon_intensity("TR", None)
        self.assertIsNone(result)

    def test_fetch_live_carbon_intensity_empty_key(self):
        """Verifies that empty string API key is treated as no key."""
        from ecotrace.config import fetch_live_carbon_intensity

        result = fetch_live_carbon_intensity("TR", "")
        self.assertIsNone(result)

    def test_fetch_live_carbon_intensity_network_error(self):
        """Verifies graceful fallback when the network is unreachable."""
        from ecotrace.config import fetch_live_carbon_intensity

        with patch("requests.get", side_effect=ConnectionError("No internet")):
            result = fetch_live_carbon_intensity("TR", "test-api-key")
            self.assertIsNone(result)

    def test_fetch_live_carbon_intensity_timeout(self):
        """Verifies graceful fallback when the API times out."""
        from ecotrace.config import fetch_live_carbon_intensity
        import requests

        with patch("requests.get", side_effect=requests.Timeout("Timeout")):
            result = fetch_live_carbon_intensity("TR", "test-api-key")
            self.assertIsNone(result)

    def test_fetch_live_carbon_intensity_invalid_response(self):
        """Verifies graceful fallback when API returns malformed data."""
        from ecotrace.config import fetch_live_carbon_intensity

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"zone": "TR"}  # Missing carbonIntensity

        with patch("requests.get", return_value=mock_response):
            result = fetch_live_carbon_intensity("TR", "test-api-key")
            self.assertIsNone(result)

    def test_fetch_live_carbon_intensity_negative_value(self):
        """Verifies that negative intensity values are rejected."""
        from ecotrace.config import fetch_live_carbon_intensity

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "zone": "TR",
            "carbonIntensity": -50
        }

        with patch("requests.get", return_value=mock_response):
            result = fetch_live_carbon_intensity("TR", "test-api-key")
            self.assertIsNone(result)

    def test_zone_mapping_coverage(self):
        """Verifies that all supported regions have a zone mapping entry."""
        from ecotrace.config import ZONE_MAPPING

        expected_regions = [
            "TR", "DE", "FR", "US", "GB", "IN", "CN", "AU", "CA", "BR",
            "JP", "KR", "NL", "SE", "NO", "PL", "IT", "ES", "PT", "BE",
            "CH", "AT", "FI", "DK", "CZ", "HU", "RO", "ZA", "MX", "AR",
            "ID", "MY", "TH", "PH", "SG", "NZ", "EG", "NG",
            "IE", "IL", "TW", "AE", "CO", "KE", "CL", "GR", "UA"
        ]
        for region in expected_regions:
            self.assertIn(region, ZONE_MAPPING,
                          f"Region '{region}' missing from ZONE_MAPPING")


class TestAutoUpdater(unittest.TestCase):
    """Tests for the PyPI auto-update system."""

    def test_fetch_latest_version_success(self):
        """Verifies that a valid PyPI response returns the version string."""
        from ecotrace.updater import _fetch_latest_version

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "info": {"version": "7.0.0"}
        }

        with patch("requests.get", return_value=mock_response):
            result = _fetch_latest_version()
            self.assertEqual(result, "7.0.0")

    def test_fetch_latest_version_network_error(self):
        """Verifies graceful None on network failure."""
        from ecotrace.updater import _fetch_latest_version

        with patch("requests.get", side_effect=ConnectionError("No internet")):
            result = _fetch_latest_version()
            self.assertIsNone(result)

    def test_is_newer_version_true(self):
        """Verifies that a newer version is correctly detected."""
        from ecotrace.updater import _is_newer_version

        self.assertTrue(_is_newer_version("6.0.0", "6.1.0"))
        self.assertTrue(_is_newer_version("6.0.0", "7.0.0"))
        self.assertTrue(_is_newer_version("0.5.2", "6.0.0"))

    def test_is_newer_version_false(self):
        """Verifies that same or older versions are not flagged as updates."""
        from ecotrace.updater import _is_newer_version

        self.assertFalse(_is_newer_version("6.0.0", "6.0.0"))
        self.assertFalse(_is_newer_version("6.1.0", "6.0.0"))
        self.assertFalse(_is_newer_version("7.0.0", "6.0.0"))

    def test_check_for_updates_no_update_available(self):
        """Verifies that no prompt is shown when version is current."""
        from ecotrace.updater import check_for_updates

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "info": {"version": "6.0.0"}
        }

        with patch("requests.get", return_value=mock_response):
            with patch("builtins.input") as mock_input:
                check_for_updates("6.0.0")
                mock_input.assert_not_called()

    def test_check_for_updates_user_declines(self):
        """Verifies that user declining ('n') doesn't trigger pip upgrade."""
        from ecotrace.updater import check_for_updates

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "info": {"version": "7.0.0"}
        }

        with patch("requests.get", return_value=mock_response):
            with patch("builtins.input", return_value="n"):
                with patch("subprocess.run") as mock_subprocess:
                    check_for_updates("6.0.0")
                    mock_subprocess.assert_not_called()

    def test_check_for_updates_user_accepts(self):
        """Verifies that user accepting ('y') triggers pip upgrade."""
        from ecotrace.updater import check_for_updates

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "info": {"version": "7.0.0"}
        }

        mock_pip = MagicMock()
        mock_pip.returncode = 0

        with patch("requests.get", return_value=mock_response):
            with patch("builtins.input", return_value="y"):
                with patch("subprocess.run", return_value=mock_pip) as mock_subprocess:
                    check_for_updates("6.0.0")
                    mock_subprocess.assert_called_once()

    def test_check_for_updates_network_failure_silent(self):
        """Verifies that network failure doesn't raise or print errors."""
        from ecotrace.updater import check_for_updates

        with patch("requests.get", side_effect=ConnectionError("No internet")):
            # Should complete without raising any exceptions
            check_for_updates("6.0.0")


class TestCoreIntegration(unittest.TestCase):
    """Integration tests for EcoTrace v6.0 __init__ with new features."""

    @patch("ecotrace.updater.check_for_updates")
    @patch("ecotrace.config.fetch_live_carbon_intensity", return_value=None)
    def test_init_with_check_updates_disabled(self, mock_fetch, mock_update):
        """Verifies that check_updates=False skips the updater entirely."""
        from ecotrace import EcoTrace

        eco = EcoTrace(region_code="TR", check_updates=False)
        mock_update.assert_not_called()
        self.assertEqual(eco._intensity_source, "static")

    @patch("ecotrace.updater.check_for_updates")
    @patch("ecotrace.core.fetch_live_carbon_intensity", return_value=350.0)
    def test_init_with_live_grid_api(self, mock_fetch, mock_update):
        """Verifies that live API data is preferred when available."""
        from ecotrace import EcoTrace

        eco = EcoTrace(
            region_code="TR",
            grid_api_key="test-key",
            check_updates=False
        )
        self.assertEqual(eco.carbon_intensity, 350.0)
        self.assertEqual(eco._intensity_source, "live")

    @patch("ecotrace.updater.check_for_updates")
    @patch("ecotrace.config.fetch_live_carbon_intensity", return_value=None)
    def test_init_fallback_to_static(self, mock_fetch, mock_update):
        """Verifies static fallback when live API returns None."""
        from ecotrace import EcoTrace

        eco = EcoTrace(
            region_code="TR",
            grid_api_key="bad-key",
            check_updates=False
        )
        self.assertEqual(eco.carbon_intensity, 475)  # Static TR value
        self.assertEqual(eco._intensity_source, "static")


if __name__ == "__main__":
    unittest.main()
