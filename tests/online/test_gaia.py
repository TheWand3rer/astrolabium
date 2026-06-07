"""Tests for Gaia query module (authentication, retrieval, update)."""

import os
import unittest
from unittest import mock

from astrolabium.queries import gaia


class TestGaiaLogin(unittest.TestCase):
    """Test Gaia authentication functions."""

    def setUp(self):
        """Reset authentication state and clean env vars."""
        gaia.logout()
        os.environ.pop("GAIADATA_USER", None)
        os.environ.pop("GAIADATA_PASSWORD", None)

    def tearDown(self):
        """Reset authentication state and clean env vars."""
        gaia.logout()
        os.environ.pop("GAIADATA_USER", None)
        os.environ.pop("GAIADATA_PASSWORD", None)

    def test_is_authenticated_false_by_default(self):
        """is_authenticated() should return False before login."""
        self.assertFalse(gaia.is_authenticated())

    def test_login_no_credentials_returns_false(self):
        """login() with no credentials should return False."""
        result = gaia.login()
        self.assertFalse(result)
        self.assertFalse(gaia.is_authenticated())

    def test_login_with_env_vars(self):
        """login() should read credentials from environment variables."""
        os.environ["GAIADATA_USER"] = "testuser"
        os.environ["GAIADATA_PASSWORD"] = "testpass"

        with mock.patch.object(gaia.Gaia, "login") as mock_login:
            result = gaia.login()
            self.assertTrue(result)
            mock_login.assert_called_once_with(user="testuser", password="testpass")
            self.assertTrue(gaia.is_authenticated())

    def test_login_with_explicit_args(self):
        """login() should accept explicit user/password args."""
        with mock.patch.object(gaia.Gaia, "login") as mock_login:
            result = gaia.login(user="explicit_user", password="explicit_pass")
            self.assertTrue(result)
            mock_login.assert_called_once_with(
                user="explicit_user", password="explicit_pass"
            )
            self.assertTrue(gaia.is_authenticated())

    def test_login_env_overridden_by_explicit(self):
        """Explicit args should override environment variables."""
        os.environ["GAIADATA_USER"] = "env_user"
        os.environ["GAIADATA_PASSWORD"] = "env_pass"

        with mock.patch.object(gaia.Gaia, "login") as mock_login:
            gaia.login(user="explicit_user", password="explicit_pass")
            mock_login.assert_called_once_with(
                user="explicit_user", password="explicit_pass"
            )

    def test_login_already_authenticated(self):
        """login() when already authenticated should return True without calling Gaia.login."""
        with mock.patch.object(gaia.Gaia, "login") as mock_login:
            gaia.login(user="u", password="p")
            mock_login.reset_mock()
            result = gaia.login()
            self.assertTrue(result)
            mock_login.assert_not_called()

    def test_login_failed_raises_warning(self):
        """login() with bad credentials should return False."""
        with mock.patch.object(gaia.Gaia, "login", side_effect=Exception("bad creds")):
            result = gaia.login(user="bad", password="bad")
            self.assertFalse(result)
            self.assertFalse(gaia.is_authenticated())


class TestGaiaLogout(unittest.TestCase):
    """Test Gaia logout function."""

    def test_logout_clears_authentication(self):
        """logout() should clear authentication state."""
        with mock.patch.object(gaia.Gaia, "login"):
            gaia.login(user="u", password="p")
            self.assertTrue(gaia.is_authenticated())

        with mock.patch.object(gaia.Gaia, "logout"):
            gaia.logout()
            self.assertFalse(gaia.is_authenticated())

    def test_logout_when_not_authenticated(self):
        """logout() when not authenticated should not raise."""
        gaia.logout()  # Should not raise

    def test_logout_handles_exception(self):
        """logout() should not raise even if Gaia.logout() fails."""
        with mock.patch.object(gaia.Gaia, "login"):
            gaia.login(user="u", password="p")

        with mock.patch.object(gaia.Gaia, "logout", side_effect=Exception("fail")):
            gaia.logout()  # Should not raise
            self.assertFalse(gaia.is_authenticated())


class TestGaiaRetrieveData(unittest.TestCase):
    """Test Gaia data retrieval."""

    def test_retrieve_data_empty_source_ids(self):
        """retrieve_data() with empty source_ids should raise ValueError."""
        with self.assertRaises(ValueError):
            gaia.retrieve_data([])

    def test_retrieve_data_single_id(self):
        """retrieve_data() should query for a single source ID."""
        mock_row = {
            "source_id": 12345,
            "ra": 0.5,
            "dec": 0.3,
            "ra_error": None,
            "dec_error": None,
            "parallax": None,
            "parallax_error": None,
            "pmra": None,
            "pmdec": None,
            "pmra_error": None,
            "pmdec_error": None,
            "radial_velocity": None,
            "radial_velocity_error": None,
            "l": None,
            "b": None,
            "ref_epoch": None,
            "teff_gspphot": None,
            "teff_gspphot_lower": None,
            "teff_gspphot_upper": None,
            "logg_gspphot": None,
            "logg_gspphot_lower": None,
            "logg_gspphot_upper": None,
            "distance_gspphot": None,
            "distance_gspphot_lower": None,
            "distance_gspphot_upper": None,
        }
        mock_table = mock.MagicMock()
        mock_table.colnames = ["source_id", "ra", "dec"]
        mock_table.__iter__ = mock.MagicMock(return_value=iter([mock_row]))
        mock_job = mock.MagicMock()
        mock_job.get_results = mock.MagicMock(return_value=mock_table)

        with mock.patch.object(gaia.Gaia, "launch_job", return_value=mock_job):
            result = gaia.retrieve_data([12345])

        self.assertEqual(len(result), 1)
        self.assertIn(12345, result)
        self.assertEqual(result[12345]["ra"].value, 0.5)
        self.assertEqual(result[12345]["dec"].value, 0.3)

    def test_retrieve_data_multiple_ids(self):
        """retrieve_data() should query for multiple source IDs."""
        mock_rows = [
            {
                "source_id": sid,
                "ra": 0.1 * sid,
                "dec": 0.2 * sid,
                "ra_error": None,
                "dec_error": None,
                "parallax": None,
                "parallax_error": None,
                "pmra": None,
                "pmdec": None,
                "pmra_error": None,
                "pmdec_error": None,
                "radial_velocity": None,
                "radial_velocity_error": None,
                "l": None,
                "b": None,
                "ref_epoch": None,
                "teff_gspphot": None,
                "teff_gspphot_lower": None,
                "teff_gspphot_upper": None,
                "logg_gspphot": None,
                "logg_gspphot_lower": None,
                "logg_gspphot_upper": None,
                "distance_gspphot": None,
                "distance_gspphot_lower": None,
                "distance_gspphot_upper": None,
            }
            for sid in [111, 222, 333]
        ]
        mock_table = mock.MagicMock()
        mock_table.colnames = ["source_id", "ra", "dec"]
        mock_table.__iter__ = mock.MagicMock(return_value=iter(mock_rows))
        mock_job = mock.MagicMock()
        mock_job.get_results = mock.MagicMock(return_value=mock_table)

        with mock.patch.object(gaia.Gaia, "launch_job", return_value=mock_job):
            result = gaia.retrieve_data([111, 222, 333])

        self.assertEqual(len(result), 3)
        self.assertIn(111, result)
        self.assertIn(222, result)
        self.assertIn(333, result)

    def test_retrieve_data_daiadr4(self):
        """retrieve_data() should support different data releases."""
        mock_table = mock.MagicMock()
        mock_table.colnames = ["source_id"]
        mock_table.__iter__ = mock.MagicMock(return_value=iter([{"source_id": 1}]))
        mock_job = mock.MagicMock()
        mock_job.get_results = mock.MagicMock(return_value=mock_table)

        with mock.patch.object(gaia.Gaia, "launch_job", return_value=mock_job) as mock_launch:
            gaia.retrieve_data([1], gaiadr=4)
            query = mock_launch.call_args[0][0]
            self.assertIn("gaiadr4", query)


if __name__ == "__main__":
    unittest.main()
