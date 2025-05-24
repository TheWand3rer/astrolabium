import unittest
from astrolabium.queries import Wikidata, WikiEntities
from astrolabium.parsers.data import WikidataStar
from astrolabium import fileIO as io, config


class TestWikidata(unittest.TestCase):
    def test_get_and_parse_entity(self):
        qid = "Q12176"  # Alpha Centauri system
        entity = Wikidata.get_entity(qid)
        instanceMatches = Wikidata.get_instance_types(entity)
        a_cen = WikidataStar(qid, Wikidata.parse_entity(entity, instanceMatches))
        self.assertEqual(a_cen.id, "Alpha Centauri")

    def test_get_entities_batch(self):
        # same as WikiEntities.retrieve_iau_entities but shorter
        dict = io.read_dict_json(f"{config.path_datadir}/IAU_qid_map")
        entities = Wikidata.get_entities_batch(list(dict.keys())[0:100])
        wikiEntities = WikiEntities(entities)

        self.assertIsNotNone(wikiEntities)
        self.assertEqual(wikiEntities.count, 100)

    def test_get_unit_symbol(self):
        qid = "Q180892"
        label = Wikidata.get_unit_symbol(qid)
        self.assertEqual(label, "M☉ solar mass")

    def test_execute_query(self):
        qid_a_cen_a = "Q2090157"  # Alpha Centauri A
        qid_hipparcos = "Q537199"  # Hipparcos catalogue entity
        hip_a_cen = "71683"
        results = Wikidata.get_qids_from_catalogue_entries(qid_hipparcos, "HIP", [hip_a_cen])
        self.assertEqual(len(results), 1)
        self.assertEqual(qid_a_cen_a, results[0]["qid"])

    def test_get_entity_from_name(self):
        results = Wikidata.get_entity_from_name("Alpha Centauri")
        entity = results[0]
        self.assertEqual(entity["id"], "Q12176")
