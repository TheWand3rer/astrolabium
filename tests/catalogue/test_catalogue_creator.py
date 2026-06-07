import unittest
import astropy.units as u
from astrolabium.creator import CatalogueCreator, Galaxy


class TestCatalogueCreator(unittest.TestCase):
    def test_find_star_systems(self):
        creator = CatalogueCreator()

        stars = creator.find_star_systems(rebuild=True)
        self.assertEqual(len(stars), 119)

    def test_find_multiple_systems(self):
        creator = CatalogueCreator()

        systems = creator.find_multiple_systems(rebuild=True)

        galaxy = Galaxy(systems)
        self.assertIsNotNone(systems)
        a_cen = galaxy.select("Alpha Centauri")

        self.assertEqual(len(a_cen.Orbiters), 2)
        self.assertEqual(["Rigel Kentaurus", "Proxima", "Toliman"], [star.Name for star in a_cen.stars])

        a_cma = galaxy.select("Alpha Canis Majoris")
        self.assertEqual(len(a_cen.Orbiters), 2)

        # TODO: Simbad has two names for it but Sirius should be preferred
        self.assertEqual(a_cma.primary.Name, "Dog Star")

    def test_get_stars_from_IAU(self):
        creator = CatalogueCreator()
        stars = creator.get_stars_from_IAU()
        self.assertEqual(len(stars), 1)

    def test_create(self):
        creator = CatalogueCreator()
        galaxy = creator.create()
        self.assertEqual(galaxy.count, 194)

        a_cen = galaxy.select("Alpha Centauri")
        self.assertIsNotNone(a_cen)
        self.assertEqual(a_cen.orbiters_catalogue_ids, ["HIP 71683", "HIP 70890", "HIP 71681"])
