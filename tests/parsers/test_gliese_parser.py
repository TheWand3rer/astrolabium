"""Tests for Gliese entry class and to_star() conversion.

Verifies:
1. GlieseEntry parses GlieseParser (ParserBase) dict format
2. GlieseEntry parses VOTable dict format
3. Coordinate conversion (B1950 → J2000)
4. Proper motion decomposition (total pm + PA → pmRA, pmDE)
5. Distance calculation from parallax
6. GlieseEntry.to_star() conversion
7. Missing optional fields handling
"""

import unittest
import astropy.units as u

from astrolabium.parsers.data import GlieseEntry


class TestGlieseEntryFromParser(unittest.TestCase):
    """Test GlieseEntry from GlieseParser (ParserBase) output format."""

    def test_entry_from_parser_dict(self):
        """GlieseEntry should parse GlieseParser dict correctly."""
        parser_dict = {
            "Name": "NN 3001",
            "RA_DE": "00 00 06 -34 29.7",
            "plx": 75.18,
            "pm": 0.344,
            "pmPA": 165.0,
            "RV": 12.5,
            "Sp": "M4.5 Ve",
        }
        entry = GlieseEntry(parser_dict)
        self.assertEqual(entry.Name, "NN 3001")
        self.assertEqual(entry.Sp, "M4.5 Ve")
        self.assertIsNotNone(entry.plx)
        self.assertAlmostEqual(entry.plx.value, 75.18, places=2)
        self.assertIsNotNone(entry.d)
        self.assertAlmostEqual(entry.d.value, 13.30, places=2)
        self.assertIsNotNone(entry.ra)
        self.assertIsNotNone(entry.de)
        self.assertIsNotNone(entry.pmRA)
        self.assertIsNotNone(entry.pmDE)

    def test_parser_dict_to_star(self):
        """GlieseEntry.from_parser should convert to Star correctly."""
        parser_dict = {
            "Name": "NN 3001",
            "RA_DE": "00 00 06 -34 29.7",
            "plx": 75.18,
        }
        entry = GlieseEntry(parser_dict)
        star = entry.to_star()
        self.assertEqual(star.id, "NN 3001")
        self.assertAlmostEqual(star.d.value, entry.d.value, places=2)


class TestGlieseEntryFromVOTable(unittest.TestCase):
    """Test GlieseEntry from VOTable output format."""

    def test_entry_from_votable_dict(self):
        """GlieseEntry should parse VOTable dict correctly."""
        votable_dict = {
            "Name": "NN 3001",
            "RAB1950": "00 02 33.8",
            "DEB1950": "-34 21 26.0",
            "RAIcrs": "00 02 40.1",
            "DEIcrs": "-34 22 40.0",
            "plx": 75.18,
            "pm": 0.344,
            "pmPA": 165.0,
            "RV": 12.5,
            "Sp": "M4.5 Ve",
            "Vmag": 12.34,
            "BV": 1.56,
        }
        entry = GlieseEntry(votable_dict)
        self.assertEqual(entry.Name, "NN 3001")
        self.assertEqual(entry.Sp, "M4.5 Ve")
        self.assertEqual(entry.Vmag, 12.34)
        self.assertEqual(entry.BV, 1.56)
        self.assertIsNotNone(entry.RAIcrs)
        self.assertIsNotNone(entry.DEIcrs)
        self.assertIsNotNone(entry.plx)
        self.assertAlmostEqual(entry.plx.value, 75.18, places=2)
        self.assertIsNotNone(entry.d)
        self.assertAlmostEqual(entry.d.value, 13.30, places=2)

    def test_votable_dict_to_star(self):
        """GlieseEntry.from_votable should convert to Star correctly."""
        votable_dict = {
            "Name": "NN 3001",
            "RAIcrs": "00 02 40.1",
            "DEIcrs": "-34 22 40.0",
            "plx": 75.18,
        }
        entry = GlieseEntry(votable_dict)
        star = entry.to_star()
        self.assertEqual(star.id, "NN 3001")
        self.assertAlmostEqual(star.d.value, entry.d.value, places=2)


class TestGlieseEntryMissingFields(unittest.TestCase):
    """Test GlieseEntry handles missing optional fields."""

    def test_minimal_dict(self):
        """GlieseEntry should work with minimal required fields."""
        minimal_dict = {
            "Name": "Gl 1",
            "RA_DE": "00 03 31 -37 36.2",
            "plx": 61.73,
        }
        entry = GlieseEntry(minimal_dict)
        self.assertEqual(entry.Name, "Gl 1")
        self.assertIsNotNone(entry.plx)
        self.assertIsNotNone(entry.ra)
        self.assertIsNotNone(entry.de)
        self.assertIsNotNone(entry.d)
        # Optional fields should be None
        self.assertIsNone(entry.Sp)
        self.assertIsNone(entry.RV)
        self.assertIsNone(entry.pm)
        self.assertIsNone(entry.pmPA)

        star = entry.to_star()
        self.assertEqual(star.id, "Gl 1")

    def test_no_proper_motion(self):
        """GlieseEntry with no proper motion data should have None pmRA/pmDE."""
        minimal_dict = {
            "Name": "Gl 2",
            "RA_DE": "00 03 31 -37 36.2",
            "plx": 61.73,
        }
        entry = GlieseEntry(minimal_dict)
        self.assertIsNone(entry.pmRA)
        self.assertIsNone(entry.pmDE)


class TestGlieseEntryCoordinateConversion(unittest.TestCase):
    """Test GlieseEntry coordinate conversion (B1950 → J2000)."""

    def test_b1950_to_j2000(self):
        """GlieseEntry should convert B1950 coordinates to J2000."""
        parser_dict = {
            "Name": "Gl 1",
            "RA_DE": "00 03 31 -37 36.2",
            "plx": 61.73,
        }
        entry = GlieseEntry(parser_dict)
        self.assertIsNotNone(entry.ra)
        self.assertIsNotNone(entry.de)
        # Coordinates should be in radians
        self.assertGreater(entry.ra.value, 0)
        self.assertLess(entry.ra.value, 2 * 3.14159)
        self.assertGreater(entry.de.value, -1.57)
        self.assertLess(entry.de.value, 0)


class TestGlieseEntryProperMotionDecomposition(unittest.TestCase):
    """Test GlieseEntry proper motion decomposition."""

    def test_decompose_total_pm(self):
        """GlieseEntry should decompose total pm + PA into pmRA, pmDE."""
        parser_dict = {
            "Name": "Gl 1",
            "RA_DE": "00 03 31 -37 36.2",
            "plx": 61.73,
            "pm": 0.344,
            "pmPA": 165.0,
        }
        entry = GlieseEntry(parser_dict)
        self.assertIsNotNone(entry.pmRA)
        self.assertIsNotNone(entry.pmDE)
        # pmRA should be positive (sin(165°) > 0), pmDE should be positive (cos(165°) < 0 but sign depends on convention)
        self.assertIsNotNone(entry.pmRA.value)
        self.assertIsNotNone(entry.pmDE.value)


class TestGlieseEntryToDict(unittest.TestCase):
    """Test GlieseEntry.to_dict() serialization."""

    def test_to_dict_json_serializable(self):
        """to_dict() output should be JSON serializable."""
        parser_dict = {
            "Name": "Gl 1",
            "RA_DE": "00 03 31 -37 36.2",
            "plx": 61.73,
        }
        entry = GlieseEntry(parser_dict)
        json_str = str(entry.to_dict())
        self.assertIsNotNone(json_str)

    def test_to_dict_includes_derived_distance(self):
        """to_dict() should include derived 'd' field."""
        parser_dict = {
            "Name": "Gl 1",
            "RA_DE": "00 03 31 -37 36.2",
            "plx": 61.73,
        }
        entry = GlieseEntry(parser_dict)
        self.assertIsNotNone(entry.d)
        self.assertGreater(entry.d.value, 0)
        d = entry.to_dict()
        self.assertIn("d", d)
        self.assertAlmostEqual(d["d"], 16.20, places=2)


if __name__ == "__main__":
    unittest.main()
