"""Tests for catalogue coverage and overlap analysis.

Verifies the relationship between Gliese, Hipparcos 2007, and crossref
catalogues — how many stars overlap, how many are unique to each source,
and how the crossref GJ field bridges Gliese to Hipparcos.
"""

import json
import unittest
from collections import Counter


class TestCatalogueCoverage(unittest.TestCase):
    """Tests for Gliese / Hipparcos / crossref coverage analysis."""

    @classmethod
    def setUpClass(cls):
        """Load all catalogue JSON files once for the test class."""
        with open("data/gliese.json") as f:
            cls.gliese = json.load(f)
        with open("data/hipparcos2007.json") as f:
            cls.hipparcos = json.load(f)
        with open("data/crossref_table.json") as f:
            cls.crossref = json.load(f)

    @staticmethod
    def _get_gj_number(name):
        """Extract GJ number from Gliese name (e.g., 'GJ 1001' -> '1001')."""
        if not name:
            return None
        parts = name.split()
        return parts[1] if len(parts) >= 2 else None

    def _build_crossref_gj_map(self):
        """Build a dict mapping GJ number -> crossref entry."""
        gj_map = {}
        for e in self.crossref:
            if "GJ" in e and e["GJ"]:
                gj_num = e["GJ"].split()[0]
                gj_map[gj_num] = e
        return gj_map

    def test_catalogue_sizes(self):
        """Verify expected catalogue sizes are loaded."""
        self.assertGreater(len(self.gliese), 0)
        self.assertGreater(len(self.hipparcos), 0)
        self.assertGreater(len(self.crossref), 0)
        self.assertEqual(len(self.gliese), 3802)
        self.assertEqual(len(self.hipparcos), 117955)

    def test_gliese_in_crossref(self):
        """How many Gliese stars are found in crossref via GJ field."""
        crossref_gj = self._build_crossref_gj_map()
        matched = [
            e for e in self.gliese
            if self._get_gj_number(e.get("Name")) in crossref_gj
        ]
        self.assertEqual(len(matched), 1815)

    def test_gliese_not_in_crossref(self):
        """How many Gliese stars are NOT in crossref at all."""
        crossref_gj = self._build_crossref_gj_map()
        not_in_crossref = [
            e for e in self.gliese
            if self._get_gj_number(e.get("Name")) not in crossref_gj
        ]
        self.assertEqual(len(not_in_crossref), 1987)

    def test_gliese_matched_to_hipparcos(self):
        """How many Gliese stars match to Hipparcos via crossref."""
        hip_ids = {e["HIP"] for e in self.hipparcos}
        crossref_gj = self._build_crossref_gj_map()
        matched = 0
        for e in self.gliese:
            gj_num = self._get_gj_number(e.get("Name"))
            if gj_num and gj_num in crossref_gj:
                hip_id = crossref_gj[gj_num].get("HIP")
                if hip_id and hip_id in hip_ids:
                    matched += 1
        self.assertEqual(matched, 1815)

    def test_gliese_only_not_in_hipparcos(self):
        """How many Gliese stars are NOT in Hipparcos 2007."""
        hip_ids = {e["HIP"] for e in self.hipparcos}
        crossref_gj = self._build_crossref_gj_map()
        gliese_only = 0
        for e in self.gliese:
            gj_num = self._get_gj_number(e.get("Name"))
            if gj_num and gj_num in crossref_gj:
                hip_id = crossref_gj[gj_num].get("HIP")
                if hip_id and hip_id in hip_ids:
                    continue
            gliese_only += 1
        self.assertEqual(gliese_only, 1987)

    def test_hipparcos_only_not_in_gliese(self):
        """How many Hipparcos stars are NOT in Gliese (via crossref)."""
        crossref_gj = self._build_crossref_gj_map()
        gliese_hips = set()
        for e in self.gliese:
            gj_num = self._get_gj_number(e.get("Name"))
            if gj_num and gj_num in crossref_gj:
                hip_id = crossref_gj[gj_num].get("HIP")
                if hip_id:
                    gliese_hips.add(hip_id)
        hipparcos_only = len(self.hipparcos) - len(gliese_hips)
        self.assertEqual(hipparcos_only, 116372)

    def test_gliese_spectral_type_distribution(self):
        """Verify spectral type distribution of Gliese-only stars."""
        crossref_gj = self._build_crossref_gj_map()
        hip_ids = {e["HIP"] for e in self.hipparcos}

        gliese_only_types = Counter()
        for e in self.gliese:
            gj_num = self._get_gj_number(e.get("Name"))
            is_matched = (
                gj_num and gj_num in crossref_gj
                and crossref_gj[gj_num].get("HIP") in hip_ids
            )
            if not is_matched:
                gliese_only_types[e.get("Sp", "Unknown")] += 1

        # Brown dwarfs (m) should be the most common Gliese-only type
        self.assertGreater(gliese_only_types.get("m", 0), 0)
        # M-dwarfs should be well represented
        m_dwarfs = sum(v for k, v in gliese_only_types.items() if k and k.startswith("M"))
        self.assertGreater(m_dwarfs, 200)

    def test_gliese_companion_stars(self):
        """Gliese-only should include companion stars (e.g., Gl 4.1, Gl 4.2)."""
        crossref_gj = self._build_crossref_gj_map()
        hip_ids = {e["HIP"] for e in self.hipparcos}

        companion_count = 0
        for e in self.gliese:
            gj_num = self._get_gj_number(e.get("Name"))
            is_matched = (
                gj_num and gj_num in crossref_gj
                and crossref_gj[gj_num].get("HIP") in hip_ids
            )
            if not is_matched and e.get("Name") and "." in e["Name"]:
                companion_count += 1

        # Should find companion-like entries (e.g., Gl 4.1, Gl 4.2)
        self.assertGreater(companion_count, 500)

    def test_gliese_distance_range(self):
        """Gliese-only stars should have reasonable distance range."""
        crossref_gj = self._build_crossref_gj_map()
        hip_ids = {e["HIP"] for e in self.hipparcos}

        distances = []
        for e in self.gliese:
            gj_num = self._get_gj_number(e.get("Name"))
            is_matched = (
                gj_num and gj_num in crossref_gj
                and crossref_gj[gj_num].get("HIP") in hip_ids
            )
            if not is_matched:
                plx = e.get("plx")
                if plx and float(plx) > 0:
                    distances.append(1000 / float(plx))

        self.assertGreater(len(distances), 0)
        self.assertGreater(min(distances), 0)
        self.assertLess(max(distances), 100)  # Gliese covers ~81 ly / 25 pc

    def test_gliese_matched_distance_range(self):
        """Matched Gliese stars should also have reasonable distances."""
        crossref_gj = self._build_crossref_gj_map()
        distances = []
        for e in self.gliese:
            gj_num = self._get_gj_number(e.get("Name"))
            if gj_num and gj_num in crossref_gj:
                plx = e.get("plx")
                if plx and float(plx) > 0:
                    distances.append(1000 / float(plx))

        self.assertGreater(len(distances), 0)
        self.assertGreater(min(distances), 0)
        self.assertLess(max(distances), 100)


if __name__ == "__main__":
    unittest.main()
