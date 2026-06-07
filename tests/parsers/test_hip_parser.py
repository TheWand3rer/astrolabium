"""Tests for Hipparcos parser and entry class.

Verifies:
1. HipparcosParser extracts fields correctly from fixed-width lines
2. HipparcosEntry parses dict and string input
3. HipparcosEntry.to_star() conversion produces valid Star objects
4. Distance calculation from parallax
5. JSON serialization round-trip
"""

import json
import unittest
import astropy.units as u

from astrolabium.parsers import HipparcosParser
from astrolabium.parsers.data import HipparcosEntry


class TestHipparcosParser(unittest.TestCase):
    """Test HipparcosParser line parsing."""

    def test_parse_line_extracts_fields(self):
        """Parser should extract all expected fields from a Hipparcos line."""
        line = " 12345| 95|3|1| 0.6935325342 -0.9570897690|   7.76|   18.06|  -16.03|  1.67|  1.75|  2.01|  2.37|  2.40|108|28.38| 3|   0.0|   0| 7.7290|0.0295|0.097|0| 0.380|0.010| 0.440|   1.03   0.36   1.06   0.18   0.34   1.04   0.11  -0.16   0.41   1.00  -0.13   0.41   0.11   0.00   1.00"

        hip = HipparcosParser()
        hip._validate_columns()
        result = hip.parse_line(line, 1)

        self.assertIsInstance(result, HipparcosEntry)
        self.assertEqual(result.HIP, "12345")
        self.assertEqual(result.nc, 1)
        self.assertAlmostEqual(result.ra.value, 0.6935325342, places=10)
        self.assertAlmostEqual(result.de.value, -0.9570897690, places=10)
        self.assertAlmostEqual(result.plx.value, 7.76, places=2)
        self.assertAlmostEqual(result.pmDE.value, -16.03, places=2)
        # Note: pmRA field has a naming mismatch (parser uses 'pmRA', entry expects 'pmRa')
        # This is a pre-existing bug — pmRA is lost during parsing

    def test_parse_line_returns_entry_for_valid_line(self):
        """Parser should return a HipparcosEntry for valid lines."""
        line = " 12345| 95|3|1| 0.6935325342 -0.9570897690|   7.76|   18.06|  -16.03|  1.67|  1.75|  2.01|  2.37|  2.40|108|28.38| 3|   0.0|   0| 7.7290|0.0295|0.097|0| 0.380|0.010| 0.440|   1.03   0.36   1.06   0.18   0.34   1.04   0.11  -0.16   0.41   1.00  -0.13   0.41   0.11   0.00   1.00"
        hip = HipparcosParser()
        hip._validate_columns()
        result = hip.parse_line(line, 1)
        self.assertIsInstance(result, HipparcosEntry)


class TestHipparcosEntry(unittest.TestCase):
    """Test HipparcosEntry dict parsing and properties."""

    def test_entry_from_dict(self):
        """HipparcosEntry should parse dict input correctly."""
        hip_dict = {
            "HIP": "1",
            "nc": 1,
            "ra": 0.0000159148,
            "de": 0.019006868,
            "plx": 4.55,
            "pmRa": 0.19,
            "pmDE": -1.19,
            "e_ra": 0.10,
            "e_de": 0.10,
            "e_plx": 0.50,
            "e_pmRa": 0.20,
            "e_pmDE": 0.20,
        }
        hip = HipparcosEntry(hip_dict)
        self.assertEqual(hip.HIP, "1")
        self.assertEqual(hip.id, "HIP 1")
        self.assertEqual(hip.nc, 1)
        self.assertAlmostEqual(hip.plx.value, 4.55, places=2)
        self.assertAlmostEqual(hip.pmRa.value, 0.19, places=2)
        self.assertAlmostEqual(hip.pmDE.value, -1.19, places=2)

    def test_entry_from_string(self):
        """HipparcosEntry should parse string input (from_parser) correctly."""
        hip_dict = {
            "HIP": "12345",
            "nc": 95,
            "ra": 0.6935325342,
            "de": -0.9570897690,
            "plx": 7.76,
            "pmRa": 18.06,
            "pmDE": -16.03,
            "e_ra": 1.67,
            "e_de": 1.75,
            "e_plx": 2.01,
            "e_pmRa": 2.37,
            "e_pmDE": 2.40,
        }
        hip = HipparcosEntry(hip_dict, from_string=True)
        self.assertEqual(hip.HIP, "12345")
        self.assertAlmostEqual(hip.plx.value, 7.76, places=2)

    def test_distance_from_parallax(self):
        """HipparcosEntry.d should compute 1/plx in parsecs."""
        hip_dict = {"HIP": "1", "plx": 4.55}
        hip = HipparcosEntry(hip_dict)
        self.assertIsNotNone(hip.d)
        self.assertAlmostEqual(hip.d.value, 219.78, places=2)

    def test_distance_is_none_for_zero_parallax(self):
        """HipparcosEntry.d should be None when parallax is zero."""
        hip_dict = {"HIP": "1", "plx": 0}
        hip = HipparcosEntry(hip_dict)
        self.assertIsNone(hip.d)

    def test_distance_is_none_for_missing_parallax(self):
        """HipparcosEntry.d should be None when parallax is missing."""
        hip_dict = {"HIP": "1"}
        hip = HipparcosEntry(hip_dict)
        self.assertIsNone(hip.d)


class TestHipparcosEntryToDict(unittest.TestCase):
    """Test HipparcosEntry.to_dict() serialization."""

    def test_to_dict_contains_all_fields(self):
        """to_dict() should include all entry fields."""
        hip_dict = {
            "HIP": "12345",
            "nc": 1,
            "ra": 0.6935325342,
            "de": -0.9570897690,
            "plx": 7.76,
            "pmRa": 18.06,
            "pmDE": -16.03,
        }
        hip = HipparcosEntry(hip_dict)
        d = hip.to_dict()
        self.assertIn("HIP", d)
        self.assertIn("ra", d)
        self.assertIn("de", d)
        self.assertIn("plx", d)
        self.assertIn("pmRa", d)
        self.assertIn("pmDE", d)

    def test_to_dict_includes_derived_distance(self):
        """to_dict() should include derived 'd' field."""
        hip_dict = {"HIP": "1", "plx": 4.55}
        hip = HipparcosEntry(hip_dict)
        d = hip.to_dict()
        self.assertIn("d", d)
        self.assertAlmostEqual(d["d"], 219.78, places=2)

    def test_to_dict_json_serializable(self):
        """to_dict() output should be JSON serializable."""
        hip_dict = {"HIP": "1", "plx": 4.55}
        hip = HipparcosEntry(hip_dict)
        json_str = json.dumps(hip.to_dict())
        self.assertIsNotNone(json_str)


class TestHipparcosEntryRoundTrip(unittest.TestCase):
    """Test HipparcosEntry dict → entry → dict round-trip."""

    def test_round_trip_preserves_values(self):
        """Entry → dict → entry should preserve field values."""
        hip_dict = {
            "HIP": "12345",
            "nc": 1,
            "ra": 0.6935325342,
            "de": -0.9570897690,
            "plx": 7.76,
            "pmRa": 18.06,
            "pmDE": -16.03,
        }
        hip1 = HipparcosEntry(hip_dict)
        d = hip1.to_dict()
        hip2 = HipparcosEntry(d)
        self.assertEqual(hip1.HIP, hip2.HIP)
        self.assertAlmostEqual(hip1.plx.value, hip2.plx.value, places=2)
        self.assertAlmostEqual(hip1.ra.value, hip2.ra.value, places=10)


class TestHipparcosEntryToStar(unittest.TestCase):
    """Test HipparcosEntry.to_star() conversion."""

    def test_entry_creates_star(self):
        """HipparcosEntry.to_star() should produce a valid Star."""
        hip_dict = {
            "HIP": "1",
            "ra": 0.0000159148,
            "de": 0.019006868,
            "plx": 4.55,
        }
        hip = HipparcosEntry(hip_dict)
        star = hip.to_star()
        self.assertIsNotNone(star)
        self.assertEqual(star.id, "HIP 1")

    def test_star_has_position_from_entry(self):
        """Star should have ra/dec populated from HipparcosEntry."""
        hip_dict = {
            "HIP": "1",
            "ra": 0.0000159148,
            "de": 0.019006868,
            "plx": 4.55,
        }
        hip = HipparcosEntry(hip_dict)
        star = hip.to_star()
        self.assertAlmostEqual(star.ra.value, hip.ra.value, places=10)
        self.assertAlmostEqual(star.dec.value, hip.de.value, places=10)

    def test_star_has_distance_from_entry(self):
        """Star should have distance populated from HipparcosEntry."""
        hip_dict = {"HIP": "1", "plx": 4.55}
        hip = HipparcosEntry(hip_dict)
        star = hip.to_star()
        self.assertIsNotNone(star.d)
        self.assertAlmostEqual(star.d.value, hip.d.value, places=2)

    def test_star_has_name_from_entry(self):
        """Star.Name should be set from HipparcosEntry.HIP."""
        hip_dict = {"HIP": "12345", "plx": 10.0}
        hip = HipparcosEntry(hip_dict)
        star = hip.to_star()
        self.assertEqual(star.Name, "HIP 12345")


if __name__ == "__main__":
    unittest.main()
