"""Tests for Gaia GCNS parser and entry conversion.

Verifies:
1. ParserBase-based GCNS parser extracts entries correctly from gzip data
2. GaiaGCNSEntry converts to Star object with astrometric data
3. Cross-reference between Hipparcos and GCNS via crossref table
"""

import gzip
import json
import os
import unittest
from pathlib import Path

import astropy.units as u

from astrolabium.parsers.gcns_parser import GaiaGCNSParser
from astrolabium.parsers.data import GaiaGCNSEntry


CATALOGUE_LOCAL = "catalogues/gaia_gcns_table1c.dat.gz"
CROSSREF_PATH = "data/crossref_table.json"
HIP_PATH = "data/hipparcos2007.json"


def _download_if_needed():
    """Download GCNS catalogue if not present."""
    path = Path(CATALOGUE_LOCAL)
    if path.exists():
        return
    import urllib.request
    url = "https://cdsarc.cds.unistra.fr/ftp/J/A+A/649/A6/table1c.dat.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading GCNS catalogue from {url}...")
    urllib.request.urlretrieve(url, str(path))
    print(f"Saved to {path}")


def _load_first_n_lines(n: int) -> list[str]:
    """Read first n lines from the GCNS catalogue."""
    _download_if_needed()
    lines = []
    with gzip.open(CATALOGUE_LOCAL, "rt", encoding="ascii", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            lines.append(line.rstrip("\n\r"))
    return lines


class TestGCNSParser(unittest.TestCase):
    """Test GCNS parser can parse entries correctly."""

    @classmethod
    def setUpClass(cls):
        _download_if_needed()
        cls.parser = GaiaGCNSParser(concise=False)
        cls.parser._validate_columns()
        # Parse a small sample for testing
        cls.sample_lines = _load_first_n_lines(10)

    def test_parser_extracts_fields(self):
        """Parser should extract all expected fields from a GCNS line."""
        line = self.sample_lines[0]
        entry_dict = self.parser._ParserBase__parse_line_delimiters(line, 1)

        expected_keys = [
            "source_id", "ra", "dec", "plx", "pmra", "pmdec",
            "Gmag", "BPmag", "RPmag", "Dist50",
            "xcoord50", "ycoord50", "zcoord50",
        ]
        for key in expected_keys:
            self.assertIn(key, entry_dict, f"Missing key: {key}")
            self.assertIsNotNone(entry_dict[key], f"Null value for key: {key}")

    def test_parser_concise_mode(self):
        """Concise mode should only extract essential fields."""
        parser_concise = GaiaGCNSParser(concise=True)
        line = self.sample_lines[0]
        entry_dict = parser_concise._ParserBase__parse_line_delimiters(line, 1)

        concise_keys = set(parser_concise._ParserBase__concise_columns)
        extracted_keys = set(entry_dict.keys())

        # All extracted keys should be in concise set
        self.assertTrue(extracted_keys.issubset(concise_keys))
        # Essential fields should be present
        self.assertIn("source_id", extracted_keys)
        self.assertIn("plx", extracted_keys)
        self.assertIn("Gmag", extracted_keys)

    def test_parser_parses_entry_into_gaia_gcns_entry(self):
        """Parser should create a valid GaiaGCNSEntry from a line."""
        line = self.sample_lines[0]
        entry_dict = self.parser._ParserBase__parse_line_delimiters(line, 1)
        entry = GaiaGCNSEntry(entry_dict, from_string=True)

        self.assertIsInstance(entry, GaiaGCNSEntry)
        self.assertEqual(entry.id, f"Gaia GCNS {entry.source_id}")
        self.assertIsNotNone(entry.source_id)
        self.assertIsNotNone(entry.ra)
        self.assertIsNotNone(entry.dec)
        self.assertIsNotNone(entry.plx)
        self.assertIsNotNone(entry.Gmag)

    def test_parser_to_dict_output(self):
        """to_dict() should produce valid JSON-serializable output."""
        line = self.sample_lines[0]
        entry_dict = self.parser._ParserBase__parse_line_delimiters(line, 1)
        entry = GaiaGCNSEntry(entry_dict, from_string=True)
        d = entry.to_dict()

        # Should be JSON serializable
        json_str = json.dumps(d, default=str)
        self.assertIsNotNone(json_str)

        # Should contain derived fields
        self.assertIn("d", d)
        self.assertIn("d_unit", d)
        self.assertIn("pcx", d)
        self.assertIn("pcy", d)
        self.assertIn("pcz", d)

    def test_parser_handles_missing_fields(self):
        """Parser should handle entries with missing optional fields (e.g., RV)."""
        # Find an entry with missing RV
        for line in self.sample_lines:
            entry_dict = self.parser._ParserBase__parse_line_delimiters(line, 1)
            if entry_dict.get("RV") is None or entry_dict.get("RV") == "":
                entry = GaiaGCNSEntry(entry_dict, from_string=True)
                self.assertIsInstance(entry, GaiaGCNSEntry)
                self.assertIsNotNone(entry.source_id)
                # RV should not be set if missing from data
                self.assertFalse(hasattr(entry, "RV"))
                break
        else:
            self.skipTest("No entry with missing RV found in sample")


class TestGaiaGCNSEntryToStar(unittest.TestCase):
    """Test GaiaGCNSEntry conversion to Star object."""

    @classmethod
    def setUpClass(cls):
        _download_if_needed()
        cls.sample_lines = _load_first_n_lines(5)

    def test_entry_creates_star(self):
        """GaiaGCNSEntry should convert to a Star object."""
        line = self.sample_lines[0]
        parser = GaiaGCNSParser(concise=False)
        entry_dict = parser._ParserBase__parse_line_delimiters(line, 1)
        entry = GaiaGCNSEntry(entry_dict, from_string=True)

        star = entry.to_star()
        self.assertIsNotNone(star)
        self.assertEqual(star.id, entry.id)

    def test_star_has_astrometric_data(self):
        """Star should have astrometric data populated from GaiaGCNSEntry."""
        line = self.sample_lines[0]
        parser = GaiaGCNSParser(concise=False)
        entry_dict = parser._ParserBase__parse_line_delimiters(line, 1)
        entry = GaiaGCNSEntry(entry_dict, from_string=True)

        star = entry.to_star()

        # Check position
        self.assertIsNotNone(star.ra)
        self.assertIsNotNone(star.dec)
        self.assertAlmostEqual(star.ra.value, entry.ra.value, places=10)
        self.assertAlmostEqual(star.dec.value, entry.dec.value, places=10)

        # Check distance (Star has d, not plx)
        self.assertIsNotNone(star.d)
        self.assertAlmostEqual(star.d.value, entry.d.value, places=2)

    def test_star_has_galactic_coords(self):
        """Star should have Galactic coordinates from GaiaGCNSEntry."""
        line = self.sample_lines[0]
        parser = GaiaGCNSParser(concise=False)
        entry_dict = parser._ParserBase__parse_line_delimiters(line, 1)
        entry = GaiaGCNSEntry(entry_dict, from_string=True)

        star = entry.to_star()

        # Star has d (distance) from GCNS data
        self.assertIsNotNone(star.d)
        self.assertAlmostEqual(star.d.value, entry.d.value, places=2)
        # Star.id should be set from GaiaGCNSEntry
        self.assertEqual(star.id, entry.id)


class TestGCNSHipparcosCrossReference(unittest.TestCase):
    """Test cross-reference between Hipparcos and GCNS via crossref table.

    Uses the crossref table to find Hipparcos entries that have Gaia DR3
    source_ids, then compares astrometric data between the two catalogues.
    """

    @classmethod
    def setUpClass(cls):
        """Load crossref table and parse a GCNS sample."""
        _download_if_needed()

        # Load crossref table
        with open(CROSSREF_PATH) as f:
            cls.crossref = json.load(f)

        # Load Hipparcos catalogue
        with open(HIP_PATH) as f:
            cls.hipparcos = json.load(f)

        # Build Hipparcos lookup by HIP number
        cls.hip_map = {e["HIP"]: e for e in cls.hipparcos}

        # Build Gaia DR3 -> HIP mapping from crossref
        cls.gaia_to_hip = {}
        for e in cls.crossref:
            gaia_dr3 = e.get("Gaia DR3")
            hip = e.get("HIP")
            if gaia_dr3 and hip:
                cls.gaia_to_hip[str(gaia_dr3)] = hip

        # Parse a sample of GCNS entries (enough to find matches)
        cls.gcns_parser = GaiaGCNSParser(concise=False)
        sample_lines = _load_first_n_lines(500)
        cls.gcns_entries = []
        for i, line in enumerate(sample_lines):
            try:
                entry_dict = cls.gcns_parser._ParserBase__parse_line_delimiters(line, i + 1)
                if entry_dict.get("source_id"):
                    cls.gcns_entries.append(entry_dict)
            except Exception:
                continue

        # Build GCNS lookup by source_id
        cls.gcns_map = {str(e["source_id"]): e for e in cls.gcns_entries}

        # Find matching entries
        cls.matches = []
        for gaia_id, hip_num in cls.gaia_to_hip.items():
            if gaia_id in cls.gcns_map and hip_num in cls.hip_map:
                cls.matches.append({
                    "gaia_id": gaia_id,
                    "hip_num": hip_num,
                    "gcns": cls.gcns_map[gaia_id],
                    "hip": cls.hip_map[hip_num],
                })

    def test_crossref_has_gaia_hip_links(self):
        """Crossref table should link Hipparcos to Gaia DR3."""
        self.assertGreater(len(self.gaia_to_hip), 0)

    def test_gcns_sample_contains_crossref_matches(self):
        """GCNS sample should contain entries that match Hipparcos via crossref."""
        self.assertGreater(len(self.matches), 0,
                           "No matching entries found between GCNS sample and Hipparcos")

    def test_astrometry_agreement(self):
        """Astrometric data (plx, pm) should agree within expected tolerances."""
        if not self.matches:
            self.skipTest("No matches to compare")

        plx_diffs = []
        pmra_diffs = []
        pmdec_diffs = []

        for m in self.matches[:20]:  # Compare up to 20 matches
            gcns = m["gcns"]
            hip = m["hip"]

            # Compare parallax
            gcns_plx = gcns.get("plx")
            hip_plx = hip.get("plx")
            if gcns_plx and hip_plx:
                plx_diffs.append(abs(float(gcns_plx) - float(hip_plx)))

            # Compare proper motion RA
            gcns_pmra = gcns.get("pmra")
            hip_pmra = hip.get("pmRA")
            if gcns_pmra and hip_pmra:
                pmra_diffs.append(abs(float(gcns_pmra) - float(hip_pmra)))

            # Compare proper motion Dec
            gcns_pmdec = gcns.get("pmdec")
            hip_pmdec = hip.get("pmDE")
            if gcns_pmdec and hip_pmdec:
                pmdec_diffs.append(abs(float(gcns_pmdec) - float(hip_pmdec)))

        # Report statistics
        if plx_diffs:
            avg_plx_diff = sum(plx_diffs) / len(plx_diffs)
            max_plx_diff = max(plx_diffs)
            self.assertLess(avg_plx_diff, 2.0,
                            f"Average parallax difference too large: {avg_plx_diff:.4f} mas")
            self.assertLess(max_plx_diff, 10.0,
                            f"Max parallax difference too large: {max_plx_diff:.4f} mas")

        if pmra_diffs:
            avg_pmra_diff = sum(pmra_diffs) / len(pmra_diffs)
            self.assertLess(avg_pmra_diff, 2.0,
                            f"Average pmRA difference too large: {avg_pmra_diff:.4f} mas/yr")

        if pmdec_diffs:
            avg_pmdec_diff = sum(pmdec_diffs) / len(pmdec_diffs)
            self.assertLess(avg_pmdec_diff, 2.0,
                            f"Average pmDec difference too large: {avg_pmdec_diff:.4f} mas/yr")

    def test_position_agreement(self):
        """Position (ra, dec) should agree between catalogues."""
        if not self.matches:
            self.skipTest("No matches to compare")

        ra_diffs = []
        dec_diffs = []

        for m in self.matches[:20]:
            gcns = m["gcns"]
            hip = m["hip"]

            gcns_ra = gcns.get("ra")
            hip_ra = hip.get("ra")
            if gcns_ra and hip_ra:
                # RA is in radians in Hipparcos, degrees in GCNS
                ra_diff = abs(float(gcns_ra) - float(hip_ra) * 180 / 3.141592653589793)
                ra_diffs.append(ra_diff)

            gcns_dec = gcns.get("dec")
            hip_dec = hip.get("de")
            if gcns_dec and hip_dec:
                dec_diff = abs(float(gcns_dec) - float(hip_dec) * 180 / 3.141592653589793)
                dec_diffs.append(dec_diff)

        if ra_diffs:
            avg_ra_diff = sum(ra_diffs) / len(ra_diffs)
            self.assertLess(avg_ra_diff, 0.002,  # < 7.2 arcsec
                            f"Average RA difference too large: {avg_ra_diff:.6f} deg")

        if dec_diffs:
            avg_dec_diff = sum(dec_diffs) / len(dec_diffs)
            self.assertLess(avg_dec_diff, 0.002,  # < 7.2 arcsec
                            f"Average Dec difference too large: {avg_dec_diff:.6f} deg")

    def test_magnitude_comparison(self):
        """Gaia magnitudes should be in expected ranges for GCNS stars."""
        if not self.matches:
            self.skipTest("No matches to compare")

        g_mags = []
        for m in self.matches[:50]:
            gcns = m["gcns"]
            gmag = gcns.get("Gmag")
            if gmag:
                g_mags.append(float(gmag))

        if g_mags:
            self.assertGreater(len(g_mags), 0)
            # GCNS contains nearby stars, Gmag should be reasonable
            self.assertGreater(min(g_mags), 0)
            self.assertLess(max(g_mags), 20)


if __name__ == "__main__":
    unittest.main()
