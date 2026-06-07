"""Tests for WDS parser and entry class.

Verifies:
1. WDSParser extracts fields correctly from fixed-width lines
2. WDSEntry parses dict and string input
3. JSON serialization round-trip
"""

import json
import unittest

from astrolabium.parsers import WDSParser
from astrolabium.parsers.data import WDSEntry
import astropy.units as u


class TestWDSParser(unittest.TestCase):
    """Test WDSParser line parsing."""

    def test_parse_line_extracts_fields(self):
        """Parser should extract all expected fields from a WDS line."""
        line = "00002+4119TDS1235AB    1991 2016    3 105  68   0.5   1.7 10.27 10.67 K2        -001-008 -001-008 +40 5210  Y   000010.69+411928.9"

        wds = WDSParser()
        wds._validate_columns()
        result = wds.parse_line(line, 1)

        self.assertIsInstance(result, WDSEntry)
        self.assertEqual(result.WDS, "00002+4119")
        self.assertEqual(result.disc, "TDS1235")
        self.assertEqual(result.comp, "AB")
        self.assertEqual(result.obs_f, 1991)
        self.assertEqual(result.obs_l, 2016)
        self.assertEqual(result.n_obs, 3)
        self.assertAlmostEqual(result.pa1.value, 105, places=2)
        self.assertAlmostEqual(result.sep1.value, 0.5, places=2)
        self.assertEqual(result.mag1, 10.27)
        self.assertEqual(result.st, "K2")

    def test_parse_line_returns_entry_for_valid_line(self):
        """Parser should return a WDSEntry for valid lines."""
        line = "00002+4119TDS1235AB    1991 2016    3 105  68   0.5   1.7 10.27 10.67 K2        -001-008 -001-008 +40 5210  Y   000010.69+411928.9"
        wds = WDSParser()
        wds._validate_columns()
        result = wds.parse_line(line, 1)
        self.assertIsInstance(result, WDSEntry)


class TestWDSEntry(unittest.TestCase):
    """Test WDSEntry dict parsing."""

    def test_entry_from_dict(self):
        """WDSEntry should parse dict input correctly."""
        wds_dict = {
            "WDS": "00014+3937",
            "disc": "RHD",
            "comp": "AB",
            "obs_f": 1991,
            "obs_l": 2016,
            "n_obs": 3,
            "pa1": 105.0,
            "pa2": 68.0,
            "sep1": 0.5,
            "sep2": 1.7,
            "mag1": 10.27,
            "mag2": 10.67,
            "st": "K2",
            "pm1_ra": -1.0,
            "pm1_dec": -8.0,
            "pm2_ra": -1.0,
            "pm2_dec": -8.0,
            "DM": "+40 5210",
            "notes": "Y",
            "coord": "000010.69+411928.9",
        }
        entry = WDSEntry(wds_dict)
        self.assertEqual(entry.WDS, "00014+3937")
        self.assertEqual(entry.comp, "AB")
        self.assertEqual(entry.st, "K2")
        self.assertAlmostEqual(entry.sep1.value, 0.5, places=2)

    def test_entry_from_dict_no_string(self):
        """WDSEntry should parse dict input (from_string=False) correctly."""
        wds_dict = {
            "WDS": "00002+4119",
            "disc": "TDS1235",
            "comp": "AB",
            "obs_f": 1991,
            "pa1": 105.0,
            "sep1": 0.5,
            "mag1": 10.27,
            "st": "K2",
        }
        entry = WDSEntry(wds_dict, from_string=False)
        self.assertEqual(entry.WDS, "00002+4119")
        self.assertAlmostEqual(entry.pa1.value, 105, places=2)


class TestWDSEntryToDict(unittest.TestCase):
    """Test WDSEntry.to_dict() serialization."""

    def test_to_dict_json_serializable(self):
        """to_dict() output should be JSON serializable."""
        wds_dict = {
            "WDS": "00002+4119",
            "disc": "TDS1235",
            "comp": "AB",
            "obs_f": 1991,
            "pa1": 105.0,
            "sep1": 0.5,
            "mag1": 10.27,
            "st": "K2",
        }
        entry = WDSEntry(wds_dict)
        json_str = json.dumps(entry.to_dict(), default=str)
        self.assertIsNotNone(json_str)

    def test_to_dict_contains_all_fields(self):
        """to_dict() should include all entry fields."""
        wds_dict = {
            "WDS": "00002+4119",
            "disc": "TDS1235",
            "comp": "AB",
            "obs_f": 1991,
            "pa1": 105.0,
            "sep1": 0.5,
            "mag1": 10.27,
            "st": "K2",
        }
        entry = WDSEntry(wds_dict)
        d = entry.to_dict()
        self.assertIn("WDS", d)
        self.assertIn("comp", d)
        self.assertIn("st", d)
        self.assertIn("mag1", d)


class TestWDSEntryRoundTrip(unittest.TestCase):
    """Test WDSEntry dict → entry → dict round-trip."""

    def test_round_trip_preserves_values(self):
        """Entry → dict → entry should preserve field values."""
        wds_dict = {
            "WDS": "00014+3937",
            "disc": "RHD",
            "comp": "AB",
            "obs_f": 1991,
            "pa1": 105.0,
            "sep1": 0.5,
            "mag1": 10.27,
            "st": "K2",
        }
        entry1 = WDSEntry(wds_dict)
        d = entry1.to_dict()
        entry2 = WDSEntry(d)
        self.assertEqual(entry1.WDS, entry2.WDS)
        self.assertEqual(entry1.comp, entry2.comp)
        self.assertAlmostEqual(entry1.sep1.value, entry2.sep1.value, places=2)


if __name__ == "__main__":
    unittest.main()
