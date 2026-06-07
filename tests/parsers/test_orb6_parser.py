"""Tests for Orb6 parser and entry class.

Verifies:
1. Orb6Parser extracts fields correctly from fixed-width lines
2. Orb6Entry parses dict and string input
3. JSON serialization round-trip
4. Orb6Entry properties (sma_AU calculation)
"""

import json
import unittest
import astropy.units as u

from astrolabium.parsers import Orb6Parser
from astrolabium.parsers.data import Orb6Entry


class TestOrb6Parser(unittest.TestCase):
    """Test Orb6Parser line parsing."""

    def test_parse_line_extracts_fields(self):
        """Parser should extract all expected fields from an Orb6 line."""
        line = "000123.67+393638.2 00014+3937 HLD  60        17178 224873    110   9.09   9.77    217.2694  y  16.5701     0.87865a  0.01750 128.050    4.231  147.353     2.957   1903.2511  y   1.6226   0.63041  0.01456  148.186    5.431       2015 3 n Izm2019  wds00014+3937e.png"

        orb6 = Orb6Parser()
        orb6._validate_columns()
        result = orb6.parse_line(line, 1)

        self.assertIsInstance(result, Orb6Entry)
        self.assertEqual(result.WDS, "00014+3937")
        self.assertEqual(result.HIP, "110")
        self.assertAlmostEqual(result.P.value, 217.2694, places=4)
        # Orb6Parser converts a from mas to arcsec (878.65 mas = 0.87865 arcsec)
        self.assertAlmostEqual(result.a.value, 0.87865, places=5)
        self.assertAlmostEqual(result.e, 0.63041, places=5)

    def test_parse_line_returns_entry_for_valid_line(self):
        """Parser should return an Orb6Entry for valid lines."""
        line = "000123.67+393638.2 00014+3937 HLD  60        17178 224873    110   9.09   9.77    217.2694  y  16.5701     0.87865a  0.01750 128.050    4.231  147.353     2.957   1903.2511  y   1.6226   0.63041  0.01456  148.186    5.431       2015 3 n Izm2019  wds00014+3937e.png"
        orb6 = Orb6Parser()
        orb6._validate_columns()
        result = orb6.parse_line(line, 1)
        self.assertIsInstance(result, Orb6Entry)


class TestOrb6Entry(unittest.TestCase):
    """Test Orb6Entry dict parsing and properties."""

    def test_entry_from_dict(self):
        """Orb6Entry should parse dict input correctly."""
        orb6_dict = {
            "WDS": "00014+3937",
            "HD": "224873",
            "HIP": "110",
            "P": 217.2694,
            "P_e": 16.5701,
            "a": 878.65,
            "a_e": 17.5,
            "i": 128.05,
            "i_e": 4.231,
            "lan": 147.353,
            "lan_e": 2.957,
            "lpa": 148.186,
            "lpa_e": 5.431,
            "e": 0.63041,
            "e_e": 0.01456,
            "orb_g": 3,
            "last": 2015,
            "notes": "n",
        }
        entry = Orb6Entry(orb6_dict)
        self.assertEqual(entry.WDS, "00014+3937")
        self.assertEqual(entry.HIP, "110")
        self.assertAlmostEqual(entry.P.value, 217.2694, places=4)
        self.assertAlmostEqual(entry.a.value, 878.65, places=2)
        self.assertAlmostEqual(entry.e, 0.63041, places=5)

    def test_entry_from_dict_no_string(self):
        """Orb6Entry should parse dict input (from_string=False) correctly."""
        orb6_dict = {
            "WDS": "00014+3937",
            "HIP": "110",
            "P": 217.2694,
            "a": 878.65,
            "e": 0.63041,
        }
        entry = Orb6Entry(orb6_dict, from_string=False)
        self.assertEqual(entry.WDS, "00014+3937")
        self.assertAlmostEqual(entry.P.value, 217.2694, places=4)
        self.assertAlmostEqual(entry.a.value, 878.65, places=2)

    def test_sma_mas_to_au_with_distance(self):
        """Orb6Entry.calculate_sma_AU should convert mas separation to AU given distance."""
        orb6_dict = {"WDS": "00014+3937", "a": 878.65}
        entry = Orb6Entry(orb6_dict)
        d = 100 * u.pc
        au = entry.calculate_sma_AU(d)
        # a (mas) -> arcsec -> * d (pc) = AU
        # 878.65 mas = 0.87865 arcsec, * 100 pc = 87.865 AU
        self.assertAlmostEqual(au.value, 87.865, places=2)


class TestOrb6EntryToDict(unittest.TestCase):
    """Test Orb6Entry.to_dict() serialization."""

    def test_to_dict_json_serializable(self):
        """to_dict() output should be JSON serializable."""
        orb6_dict = {
            "WDS": "00014+3937",
            "HIP": "110",
            "P": 217.2694,
            "a": 878.65,
            "e": 0.63041,
        }
        entry = Orb6Entry(orb6_dict)
        json_str = json.dumps(entry.to_dict(), default=str)
        self.assertIsNotNone(json_str)

    def test_to_dict_contains_orbital_fields(self):
        """to_dict() should include orbital parameters."""
        orb6_dict = {
            "WDS": "00014+3937",
            "P": 217.2694,
            "a": 878.65,
            "e": 0.63041,
            "i": 128.05,
            "lan": 147.353,
            "lpa": 148.186,
        }
        entry = Orb6Entry(orb6_dict)
        d = entry.to_dict()
        self.assertIn("P", d)
        self.assertIn("a", d)
        self.assertIn("e", d)
        self.assertIn("i", d)
        self.assertIn("lan", d)
        self.assertIn("lpa", d)


class TestOrb6EntryRoundTrip(unittest.TestCase):
    """Test Orb6Entry dict → entry → dict round-trip."""

    def test_round_trip_preserves_values(self):
        """Entry → dict → entry should preserve field values."""
        orb6_dict = {
            "WDS": "00014+3937",
            "HIP": "110",
            "P": 217.2694,
            "a": 878.65,
            "e": 0.63041,
        }
        entry1 = Orb6Entry(orb6_dict)
        d = entry1.to_dict()
        entry2 = Orb6Entry(d)
        self.assertEqual(entry1.WDS, entry2.WDS)
        self.assertAlmostEqual(entry1.P.value, entry2.P.value, places=4)
        self.assertAlmostEqual(entry1.e, entry2.e, places=5)


if __name__ == "__main__":
    unittest.main()
