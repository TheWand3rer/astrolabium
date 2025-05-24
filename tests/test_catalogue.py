import unittest
import astropy.units as u
import os.path
from astrolabium import config
from astrolabium.creator import CatalogueCreator
from astrolabium.catalogues import Hipparcos, WDS, Orb6


class TestCatalogues(unittest.TestCase):
    HIP_Rigel_Kentaurus = "71683"
    WDS_AlphaCentauri = "14396-6050"

    def test_download_catalogues(self):
        CatalogueCreator.download_and_parse_catalogues()
        self.assertTrue(os.path.exists(f"{config.path_cataloguedir}/hipparcos_2007.dat"))
        self.assertTrue(os.path.exists(f"{config.path_cataloguedir}/wds.txt"))
        self.assertTrue(os.path.exists(f"{config.path_cataloguedir}/orb6orbits.txt"))
        self.assertTrue(os.path.exists(f"{config.path_datadir}/hipparcos2007.json"))
        self.assertTrue(os.path.exists(f"{config.path_datadir}/wds.json"))
        self.assertTrue(os.path.exists(f"{config.path_datadir}/orb6orbits.json"))
        self.assertTrue(os.path.exists(f"{config.path_datadir}/crossref_table.json"))

    def test_hipparcos_select(self):
        hipparcos = Hipparcos()

        star = hipparcos.select(self.HIP_Rigel_Kentaurus)

        self.assertIsNotNone(star)
        self.assertAlmostEqual(star.ra, 3.8383352142 * u.rad)
        self.assertAlmostEqual(star.de, -1.061773585 * u.rad)
        self.assertAlmostEqual(star.plx, 754.81 * u.mas)

    def test_wds_select(self):
        wds = WDS()

        entry = wds.select(self.WDS_AlphaCentauri)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.disc, "RHD   1")
        self.assertEqual(entry.comp, "AB")
        self.assertEqual(entry.st, "G2V+K1V")

    def test_wds_select_entries(self):
        wds = WDS()

        entries = wds.select_entries([self.WDS_AlphaCentauri])
        self.assertEqual(len(entries), 3)

    def test_wds_group_entries(self):
        wds = WDS()
        groups = wds.select_entries_grouped(wds_ids=[self.WDS_AlphaCentauri])
        self.assertEqual(len(groups[self.WDS_AlphaCentauri]), 2)

    def test_orb6_select(self):
        orb6 = Orb6()
        entry = orb6.select("05595+4457")

        self.assertIsNotNone(entry)
        self.assertEqual(entry.last, 1992)
        self.assertAlmostEqual(entry.a, 3.3 * u.mas)
        self.assertAlmostEqual(entry.lpa, 0 * u.deg)
