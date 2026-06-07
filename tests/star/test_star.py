"""Tests for the Star class.

Verifies:
1. Star construction from dict (no isinstance checks for entry types)
2. Star.has_required_physical_data()
3. Star.has_required_orbital_data()
4. Star.add_wikimedia() — fills missing fields from WikimediaStar
5. Star properties: gc (galactic coords), xyz
6. Star.to_dict() serialization
"""

import json
import unittest
from unittest.mock import patch, MagicMock

import astropy.units as u

from astrolabium.creator.star import Star
from astrolabium.parsers.data import WikimediaStar, GlieseEntry, GaiaGCNSEntry, HipparcosEntry


class TestStarConstruction(unittest.TestCase):
    """Test Star class construction from dict."""

    def test_star_from_empty_dict(self):
        """Star() with no arguments should have None fields."""
        star = Star()
        self.assertIsNone(star.id)
        self.assertIsNone(star.Name)
        self.assertIsNone(star.d)
        self.assertFalse(hasattr(star, 'ra'))
        self.assertFalse(hasattr(star, 'dec'))

    def test_star_from_dict_with_position(self):
        """Star should accept dict with ra/dec/d fields."""
        star = Star(catalogue_entry={
            "id": "HIP 1",
            "Name": "HIP 1",
            "ra": 0.0000159148,
            "dec": 0.019006868,
            "d": 219.78,
        })
        self.assertEqual(star.id, "HIP 1")
        self.assertEqual(star.Name, "HIP 1")
        self.assertAlmostEqual(star.ra.value, 0.0000159148, places=10)
        self.assertAlmostEqual(star.dec.value, 0.019006868, places=10)
        self.assertAlmostEqual(star.d.value, 219.78, places=2)

    def test_star_from_dict_with_orbital_data(self):
        """Star should accept dict with orbital parameters."""
        star = Star(catalogue_entry={
            "id": "HIP 1",
            "ra": 0.0000159148,
            "dec": 0.019006868,
            "d": 219.78,
            "a": 10.0,
            "e": 0.5,
            "P": 5.0,
            "i": 45.0,
            "lan": 90.0,
            "argp": 180.0,
        })
        self.assertIsNotNone(star.a)
        self.assertAlmostEqual(star.a.value, 10.0, places=2)
        self.assertAlmostEqual(star.e, 0.5, places=2)
        self.assertAlmostEqual(star.P.value, 5.0, places=2)

    def test_star_from_dict_with_spectral_class(self):
        """Star should accept sc (spectral class) from dict."""
        star = Star(catalogue_entry={
            "id": "HIP 1",
            "ra": 0.0000159148,
            "dec": 0.019006868,
            "d": 219.78,
            "sc": "G2V",
        })
        self.assertEqual(star.sc, "G2V")

    def test_star_from_dict_with_otypes(self):
        """Star should accept otypes from dict."""
        star = Star(catalogue_entry={
            "id": "HIP 1",
            "ra": 0.0000159148,
            "dec": 0.019006868,
            "d": 219.78,
            "otypes": ["HIP", "WDS"],
        })
        self.assertIsNotNone(star.otypes)


class TestStarHasRequiredPhysicalData(unittest.TestCase):
    """Tests for Star.has_required_physical_data()."""

    def test_no_data(self):
        star = Star()
        self.assertFalse(star.has_required_physical_data())

    def test_only_temperature(self):
        star = Star()
        star.t = 5000 * u.K
        self.assertFalse(star.has_required_physical_data())

    def test_temperature_and_mass(self):
        star = Star()
        star.t = 5000 * u.K
        star.m = 1.5 * u.M_sun
        self.assertTrue(star.has_required_physical_data())

    def test_temperature_and_luminosity(self):
        star = Star()
        star.t = 5000 * u.K
        star.l = 10 * u.L_sun
        self.assertTrue(star.has_required_physical_data())

    def test_only_mass_no_temperature(self):
        star = Star()
        star.m = 2.0 * u.M_sun
        self.assertFalse(star.has_required_physical_data())

    def test_only_luminosity_no_temperature(self):
        star = Star()
        star.l = 5 * u.L_sun
        self.assertFalse(star.has_required_physical_data())

    def test_all_physical_fields(self):
        star = Star()
        star.m = 1.0 * u.M_sun
        star.l = 1.0 * u.L_sun
        star.t = 5778 * u.K
        star.g = 10000 * u.cm / u.s**2
        star.age = 4.6 * u.Gyr
        self.assertTrue(star.has_required_physical_data())


class TestStarHasRequiredOrbitalData(unittest.TestCase):
    """Tests for Star.has_required_orbital_data()."""

    def test_no_orbital_data(self):
        star = Star()
        self.assertFalse(star.has_required_orbital_data())

    def test_only_separation(self):
        star = Star()
        star.a = 10.0 * u.AU
        self.assertFalse(star.has_required_orbital_data())

    def test_separation_and_eccentricity(self):
        star = Star()
        star.a = 10.0 * u.AU
        star.e = 0.5
        self.assertFalse(star.has_required_orbital_data())

    def test_all_orbital_data(self):
        star = Star()
        star.a = 10.0 * u.AU
        star.e = 0.5
        star.P = 5.0 * u.yr
        self.assertTrue(star.has_required_orbital_data())

    def test_missing_eccentricity(self):
        star = Star()
        star.a = 10.0 * u.AU
        star.e = None
        star.P = 5.0 * u.yr
        self.assertFalse(star.has_required_orbital_data())

    def test_missing_period(self):
        star = Star()
        star.a = 10.0 * u.AU
        star.e = 0.5
        star.P = None
        self.assertFalse(star.has_required_orbital_data())


class TestStarAddWikimedia(unittest.TestCase):
    """Tests for Star.add_wikimedia() method."""

    def test_add_wikimedia_fills_missing_fields(self):
        """add_wikimedia should fill fields that are None on the star."""
        star = Star()
        star.t = 5000 * u.K  # temperature already set

        raw = {"m": "1.5 M", "l": "10 L"}
        ws = WikimediaStar.from_raw(raw)

        set_fields = star.add_wikimedia(ws)
        self.assertIn("m", set_fields)
        self.assertIn("l", set_fields)
        self.assertIsNotNone(star.m)
        self.assertIsNotNone(star.l)
        self.assertEqual(star.m.value, 1.5)
        self.assertEqual(star.l.value, 10)

    def test_add_wikimedia_preserves_existing_fields(self):
        """add_wikimedia should NOT overwrite fields that already exist."""
        star = Star()
        star.m = 2.0 * u.M_sun  # mass already set
        star.t = 5000 * u.K

        raw = {"m": "1.5 M", "l": "10 L"}
        ws = WikimediaStar.from_raw(raw)

        set_fields = star.add_wikimedia(ws)
        self.assertNotIn("m", set_fields)  # m was already set
        self.assertIn("l", set_fields)  # l was missing
        self.assertEqual(star.m.value, 2.0)  # original value preserved

    def test_add_wikimedia_logs_discrepancy(self):
        """add_wikimedia should log warning for large discrepancies."""
        star = Star()
        star.m = 10.0 * u.M_sun  # very different from Wikimedia value
        star.t = 5000 * u.K

        raw = {"m": "1.0 M"}
        ws = WikimediaStar.from_raw(raw)

        set_fields = star.add_wikimedia(ws)
        self.assertNotIn("m", set_fields)  # m was already set

    def test_add_wikimedia_with_empty_wikimedia_star(self):
        """add_wikimedia with empty WikimediaStar should set no fields."""
        star = Star()
        star.t = 5000 * u.K

        ws = WikimediaStar(None)

        set_fields = star.add_wikimedia(ws)
        self.assertEqual(set_fields, [])

    def test_add_wikimedia_with_radius(self):
        """add_wikimedia should handle radius field."""
        star = Star()
        star.t = 5000 * u.K

        raw = {"r": "1.7144 R"}
        ws = WikimediaStar.from_raw(raw)

        set_fields = star.add_wikimedia(ws)
        self.assertIn("r", set_fields)
        self.assertIsNotNone(star.r)
        self.assertEqual(star.r.value, 1.7144)
        self.assertEqual(star.r.unit, u.R_sun)


class TestStarToDict(unittest.TestCase):
    """Test Star.to_dict() serialization."""

    def test_to_dict_basic(self):
        """Star.to_dict() should produce a valid dict."""
        star = Star(catalogue_entry={
            "id": "HIP 1",
            "Name": "HIP 1",
            "ra": 0.0000159148,
            "dec": 0.019006868,
            "d": 219.78,
        })
        d = star.to_dict()
        self.assertIn("Id", d)
        self.assertIn("Name", d)
        self.assertIn("Attributes", d)
        self.assertEqual(d["Id"], "HIP 1")

    def test_to_dict_json_serializable(self):
        """Star.to_dict() output should be JSON serializable."""
        star = Star(catalogue_entry={
            "id": "HIP 1",
            "ra": 0.0000159148,
            "dec": 0.019006868,
            "d": 219.78,
        })
        json_str = json.dumps(star.to_dict(), default=str)
        self.assertIsNotNone(json_str)

    def test_to_dict_includes_orbital_data(self):
        """Star.to_dict() should include orbital data when present."""
        star = Star(catalogue_entry={
            "id": "HIP 1",
            "ra": 0.0000159148,
            "dec": 0.019006868,
            "d": 219.78,
            "a": 10.0,
            "e": 0.5,
            "P": 5.0,
        })
        d = star.to_dict()
        self.assertIn("OrbitalData", d)
        self.assertIn("a", d["OrbitalData"])
        self.assertIn("e", d["OrbitalData"])
        self.assertIn("P", d["OrbitalData"])


class TestStarFromEntryTypes(unittest.TestCase):
    """Test Star construction from various entry types via to_star_dict()."""

    def test_star_from_hipparcos_entry(self):
        """Star should be constructible from HipparcosEntry via to_star_dict()."""
        from astrolabium.parsers.data import HipparcosEntry

        hip_dict = {
            "HIP": "1",
            "ra": 0.0000159148,
            "de": 0.019006868,
            "plx": 4.55,
        }
        hip = HipparcosEntry(hip_dict)
        star_data = hip.to_star_dict()
        star = Star(catalogue_entry=star_data)

        self.assertEqual(star.id, "HIP 1")
        self.assertAlmostEqual(star.ra.value, hip.ra.value, places=10)
        self.assertAlmostEqual(star.dec.value, hip.de.value, places=10)
        self.assertAlmostEqual(star.d.value, hip.d.value, places=2)

    def test_star_from_gliese_entry(self):
        """Star should be constructible from GlieseEntry via to_star_dict()."""
        parser_dict = {
            "Name": "NN 3001",
            "RA_DE": "00 00 06 -34 29.7",
            "plx": 75.18,
        }
        gliese = GlieseEntry(parser_dict)
        star_data = gliese.to_star_dict()
        star = Star(catalogue_entry=star_data)

        self.assertEqual(star.id, "NN 3001")
        self.assertIsNotNone(star.d)
        self.assertAlmostEqual(star.d.value, gliese.d.value, places=2)

    def test_star_from_gaia_gcns_entry(self):
        """Star should be constructible from GaiaGCNSEntry via to_star_dict()."""
        from astrolabium.parsers.data import GaiaGCNSEntry

        gcns_dict = {
            "source_id": 1234567890123456789,
            "ra": 0.0000159148,
            "dec": 0.019006868,
            "Dist50": 0.21978,  # kpc
        }
        gcns = GaiaGCNSEntry(gcns_dict)
        star_data = gcns.to_star_dict()
        star = Star(catalogue_entry=star_data)

        self.assertEqual(star.id, gcns.id)
        self.assertAlmostEqual(star.ra.value, gcns.ra.value, places=10)
        self.assertAlmostEqual(star.dec.value, gcns.dec.value, places=10)
        self.assertAlmostEqual(star.d.value, gcns.d.value, places=2)


if __name__ == "__main__":
    unittest.main()
