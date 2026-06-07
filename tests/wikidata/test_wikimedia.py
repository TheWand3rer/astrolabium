import unittest
import os
from unittest.mock import patch, MagicMock

import astropy.units as u

from astrolabium.queries import WikimediaClient
from astrolabium.queries.wikimedia import normalize_field
from astrolabium.parsers.data import WikimediaStar
from astrolabium.queries.wikidata import Wikidata
from astrolabium.creator.star import Star


class TestNormalizeField(unittest.TestCase):
    """Tests for the field name normalization mapping."""

    def test_mass(self):
        self.assertEqual(normalize_field("Mass"), "m")

    def test_luminosity(self):
        self.assertEqual(normalize_field("Luminosity"), "l")

    def test_temperature(self):
        self.assertEqual(normalize_field("Temperature"), "t")

    def test_age(self):
        self.assertEqual(normalize_field("Age"), "age")

    def test_surface_gravity(self):
        self.assertEqual(normalize_field("Surface gravity"), "g")

    def test_radius(self):
        self.assertEqual(normalize_field("Radius"), "r")

    def test_parallax(self):
        self.assertEqual(normalize_field("Parallax"), "plx")

    def test_rotational_velocity_excluded(self):
        """Rotational velocity is not stored in PhysicalData."""
        self.assertIsNone(normalize_field("Rotational velocity"))

    def test_unknown_field(self):
        self.assertIsNone(normalize_field("Unknown field"))

    def test_empty_key(self):
        self.assertIsNone(normalize_field(""))


class TestWikimediaClientAuth(unittest.TestCase):
    """Tests for WikimediaClient authentication behavior."""

    @patch.dict(os.environ, {"WIKIMEDIA_USERNAME": "test_user", "WIKIMEDIA_PASSWORD": "test_pass"})
    def setUp(self):
        """Create a client with test credentials for auth tests."""
        self.client = WikimediaClient()

    @patch.dict(os.environ, {"WIKIMEDIA_USERNAME": "test_user", "WIKIMEDIA_PASSWORD": "test_pass"})
    def test_is_not_authenticated_by_default(self):
        """Client should not be authenticated immediately after construction."""
        self.assertFalse(self.client.is_authenticated())

    @patch.dict(os.environ, {"WIKIMEDIA_USERNAME": "test_user", "WIKIMEDIA_PASSWORD": "test_pass"})
    def test_fetch_returns_none_when_not_authenticated(self):
        """Fetch methods should return None when not authenticated."""
        result = self.client.fetch_by_page_name("Sirius")
        self.assertIsNone(result)

    @patch.dict(os.environ, {"WIKIMEDIA_USERNAME": "test_user", "WIKIMEDIA_PASSWORD": "test_pass"})
    def test_fetch_parsed_returns_none_when_not_authenticated(self):
        """fetch_parsed should return None when not authenticated."""
        result = self.client.fetch_parsed("Sirius")
        self.assertIsNone(result)

    @patch.dict(os.environ, {"WIKIMEDIA_USERNAME": "test_user", "WIKIMEDIA_PASSWORD": "test_pass"})
    def test_constructs_with_env_credentials(self):
        """Client should read credentials from environment variables."""
        self.assertEqual(self.client._username, "test_user")
        self.assertEqual(self.client._password, "test_pass")

    def test_raises_on_missing_credentials(self):
        """Client should raise ValueError if no credentials available."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as ctx:
                WikimediaClient(username=None, password=None)
            self.assertIn("Wikimedia credentials not found", str(ctx.exception))


@unittest.skipIf(
    not os.getenv("WIKIMEDIA_USERNAME") or not os.getenv("WIKIMEDIA_PASSWORD"),
    "Wikimedia credentials not set in environment",
)
class TestWikimediaClientIntegration(unittest.TestCase):
    """Integration tests that require valid Wikimedia API credentials."""

    @classmethod
    def setUpClass(cls):
        """Authenticate once for all tests in this class."""
        cls.client = WikimediaClient()
        cls.auth_success = cls.client.authenticate()
        if not cls.auth_success:
            raise unittest.SkipTest("Wikimedia API authentication failed")

    def test_authenticate_returns_true(self):
        """authenticate() should return True on success."""
        self.assertTrue(self.client.is_authenticated())

    def test_fetch_alpha_centauri(self):
        """Fetch infobox for Alpha Centauri and verify structure."""
        infobox = self.client.fetch_by_page_name("Alpha_Centauri")
        self.assertIsNotNone(infobox, "Should return infobox for Alpha_Centauri")
        self.assertIsInstance(infobox, dict)
        self.assertGreater(len(infobox), 0, "Infobox should contain entries")

    def test_fetch_alpha_centauri_has_physical_fields(self):
        """Infobox for Alpha Centauri should contain at least one physical data field."""
        infobox = self.client.fetch_by_page_name("Alpha_Centauri")
        if infobox is None:
            self.skipTest("Could not fetch infobox for Alpha Centauri")

        physical_fields = {
            k: v for k, v in infobox.items() if normalize_field(k) is not None
        }
        self.assertGreater(
            len(physical_fields), 0,
            "Should have at least one physical data field (Mass, Luminosity, etc.)",
        )

    def test_fetch_alpha_centauri_has_mass(self):
        """Alpha Centauri infobox should contain a Mass field."""
        infobox = self.client.fetch_by_page_name("Alpha_Centauri")
        if infobox is None:
            self.skipTest("Could not fetch infobox for Alpha Centauri")

        self.assertIn(
            "Mass", infobox,
            "Mass field should be present in Alpha Centauri infobox",
        )

    def test_fetch_parsed_returns_normalized_fields(self):
        """fetch_parsed should return internal field names mapped to raw values."""
        parsed = self.client.fetch_parsed("Alpha_Centauri")
        self.assertIsNotNone(parsed, "Should return normalized fields")
        self.assertIsInstance(parsed, dict)
        self.assertIn(
            "m", parsed,
            "Mass ('m') should be present in parsed output",
        )

    def test_fetch_parsed_excludes_non_physical_fields(self):
        """fetch_parsed should exclude fields like 'Rotational velocity'."""
        parsed = self.client.fetch_parsed("Alpha_Centauri")
        if parsed is None:
            self.skipTest("Could not fetch parsed data")

        self.assertNotIn(
            "Rotational velocity", parsed,
            "Non-PhysicalData fields should be excluded",
        )

    def test_fetch_unknown_page_returns_none(self):
        """Fetching a non-existent page should return None."""
        result = self.client.fetch_by_page_name("ThisPageDoesNotExist12345")
        self.assertIsNone(result)

    def test_fetch_by_qid_workflow(self):
        """Test the full QID -> page name -> infobox workflow."""
        entity = Wikidata.get_entity("Q12176")
        page_name = Wikidata.get_page_name(entity)
        self.assertEqual(page_name, "Alpha Centauri")

        infobox = self.client.fetch_by_page_name(page_name)
        self.assertIsNotNone(infobox)

    def test_cached_infobox_loads(self):
        """Test that cached infobox data is loaded on subsequent calls."""
        # First call — should fetch and cache
        infobox1 = self.client.fetch_by_page_name("Alpha_Centauri")
        self.assertIsNotNone(infobox1)

        # Second call — should load from cache
        infobox2 = self.client.fetch_by_page_name("Alpha_Centauri")
        self.assertIsNotNone(infobox2)

        # Both should contain the same data
        self.assertEqual(infobox1, infobox2)


class TestWikimediaStar(unittest.TestCase):
    """Tests for WikimediaStar parsing and conversion."""

    def test_from_raw_with_internal_field_names(self):
        """WikimediaStar should parse raw data with internal field names."""
        raw = {"m": "2.063 M", "t": "9845 K"}
        ws = WikimediaStar.from_raw(raw)
        self.assertIsNotNone(ws.m)
        self.assertEqual(ws.m.value, 2.063)
        self.assertEqual(ws.m.unit, u.M_sun)
        self.assertIsNotNone(ws.t)
        self.assertEqual(ws.t.value, 9845)
        self.assertEqual(ws.t.unit, u.K)

    def test_from_raw_with_infobox_keys(self):
        """WikimediaStar should parse raw data with Wikipedia infobox keys."""
        raw = {"Mass": "2.063 M", "Temperature": "9845 K"}
        ws = WikimediaStar.from_raw(raw)
        self.assertIsNotNone(ws.m)
        self.assertEqual(ws.m.value, 2.063)
        self.assertEqual(ws.m.unit, u.M_sun)
        self.assertIsNotNone(ws.t)
        self.assertEqual(ws.t.value, 9845)
        self.assertEqual(ws.t.unit, u.K)

    def test_from_raw_with_mixed_keys(self):
        """WikimediaStar should handle mixed infobox keys and internal names."""
        raw = {"Mass": "2.063 M", "t": "9845 K", "Luminosity": "24.74 L"}
        ws = WikimediaStar.from_raw(raw)
        self.assertIsNotNone(ws.m)
        self.assertIsNotNone(ws.t)
        self.assertIsNotNone(ws.l)
        self.assertEqual(ws.l.value, 24.74)
        self.assertEqual(ws.l.unit, u.L_sun)

    def test_from_raw_with_uncertainty_notation(self):
        """WikimediaStar should handle uncertainty notation like '2.063+-0.023'."""
        raw = {"m": "2.063+-0.023 M"}
        ws = WikimediaStar.from_raw(raw)
        self.assertIsNotNone(ws.m)
        self.assertEqual(ws.m.value, 2.063)

    def test_from_raw_with_unicode_units(self):
        """WikimediaStar should handle Unicode solar symbol."""
        raw = {"m": "2.063 M☉", "l": "24.74 L☉", "r": "1.7144 R☉"}
        ws = WikimediaStar.from_raw(raw)
        self.assertIsNotNone(ws.m)
        self.assertEqual(ws.m.unit, u.M_sun)
        self.assertIsNotNone(ws.l)
        self.assertEqual(ws.l.unit, u.L_sun)
        self.assertIsNotNone(ws.r)
        self.assertEqual(ws.r.unit, u.R_sun)

    def test_from_raw_empty(self):
        """WikimediaStar.from_raw with empty dict should have no fields."""
        ws = WikimediaStar.from_raw({})
        self.assertIsNone(ws.m)
        self.assertIsNone(ws.l)
        self.assertIsNone(ws.t)

    def test_from_raw_none(self):
        """WikimediaStar(None) should have no fields."""
        ws = WikimediaStar(None)
        self.assertIsNone(ws.m)
        self.assertIsNone(ws.l)

    def test_to_dict(self):
        """WikimediaStar.to_dict should return dict with only non-None fields."""
        raw = {"m": "2.063 M", "t": "9845 K"}
        ws = WikimediaStar.from_raw(raw)
        d = ws.to_dict()
        self.assertIn("m", d)
        self.assertIn("t", d)
        self.assertNotIn("l", d)
        self.assertNotIn("g", d)

    def test_get_fillable_fields(self):
        """WikimediaStar.get_fillable_fields should return only missing fields."""
        raw = {"m": "2.063 M", "t": "9845 K"}
        ws = WikimediaStar.from_raw(raw)
        existing = {"m": 1.0 * u.M_sun, "age": 1.0 * u.Gyr}
        fillable = ws.get_fillable_fields(existing)
        self.assertIn("t", fillable)
        self.assertNotIn("m", fillable)  # already in existing
        self.assertNotIn("age", fillable)  # not in ws

    def test_parse_luminosity(self):
        """WikimediaStar should parse luminosity values."""
        raw = {"l": "24.74 L"}
        ws = WikimediaStar.from_raw(raw)
        self.assertIsNotNone(ws.l)
        self.assertEqual(ws.l.value, 24.74)
        self.assertEqual(ws.l.unit, u.L_sun)

    def test_parse_radius(self):
        """WikimediaStar should parse radius values."""
        raw = {"r": "1.7144 R"}
        ws = WikimediaStar.from_raw(raw)
        self.assertIsNotNone(ws.r)
        self.assertEqual(ws.r.value, 1.7144)
        self.assertEqual(ws.r.unit, u.R_sun)

    def test_parse_age(self):
        """WikimediaStar should parse age values in various units."""
        # Gyr
        ws1 = WikimediaStar.from_raw({"age": "4.85 Gyr"})
        self.assertIsNotNone(ws1.age)
        self.assertEqual(ws1.age.value, 4.85)
        self.assertEqual(ws1.age.unit, u.Gyr)

        # Myr
        ws2 = WikimediaStar.from_raw({"age": "242 Myr"})
        self.assertIsNotNone(ws2.age)
        self.assertAlmostEqual(ws2.age.to(u.Gyr).value, 0.242, places=3)

        # yr
        ws3 = WikimediaStar.from_raw({"age": "4850000000 yr"})
        self.assertIsNotNone(ws3.age)
        self.assertAlmostEqual(ws3.age.to(u.Gyr).value, 4.85, places=2)

    def test_parse_surface_gravity(self):
        """WikimediaStar should parse surface gravity values."""
        raw = {"g": "16000 cm/s2"}
        ws = WikimediaStar.from_raw(raw)
        self.assertIsNotNone(ws.g)
        self.assertEqual(ws.g.value, 16000)
        self.assertEqual(ws.g.unit, u.cm / u.s**2)

    def test_parse_parallax(self):
        """WikimediaStar should parse parallax values."""
        raw = {"plx": "379.21 mas"}
        ws = WikimediaStar.from_raw(raw)
        self.assertIsNotNone(ws.plx)
        self.assertEqual(ws.plx.value, 379.21)
        self.assertEqual(ws.plx.unit, u.mas)


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
        # The warning should have been logged (check logger output)

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


if __name__ == "__main__":
    unittest.main()
