from typing import Any, Callable
from astropy import units as u
from astrolabium import fileIO as io, config
from astrolabium.queries import Wikidata as wiki, simbad
from astrolabium.parsers.data import WikidataStar
import math
import time
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)

class WikiEntities:
    def __init__(self, entities: dict[str, Any]):
        self.__entities: dict[str, WikidataStar] = {}
        self.__index: dict[str, str] = {}
        if len(entities) > 0:
            for qid, entity in entities.items():
                self.__entities[qid] = WikidataStar(qid, entity)
        else:
            raise ValueError("No wikidata entities provided")
        pass

    @property
    def count(self) -> int:
        return len(self.__entities)

    @property
    def values(self) -> list[WikidataStar]:
        return list(self.__entities.values())

    def build_index(self, catalogue_label: str):
        for qid, entity in self.__entities.items():
            if catalogue_label.lower() not in entity.cat:
                logger.warning(f"No {catalogue_label} id in {qid}: {entity.cat}")
                continue
            id = entity.cat[catalogue_label.lower()]
            catalogue_id = f"{catalogue_label} {id}"
            self.__index[catalogue_id] = qid

    @classmethod
    def load(cls, entities_path: str) -> "WikiEntities":
        return WikiEntities(io.read_dict_json(entities_path))

    @classmethod
    def retrieve_iau_entities(cls) -> "WikiEntities":
        iau_dict = io.read_dict_json(f"{config.path_datadir}/IAU_qid_map")
        if len(iau_dict)==0:
            return None
        entities = wiki.get_entities_batch(list(iau_dict.keys()))
        io.write_dict_json(entities, f"{config.path_entitiesdir}/IAU_entities")
        return WikiEntities(entities)

    @classmethod
    def filter_distance(cls, e: WikidataStar, lyr) -> bool:
        assert e.d is not None, f"{e.qid}: missing distance"
        return e.d.value <= lyr

    def filter(self, filter: Callable, message: str):
        """
        Removes all entities not matching the filter.
        """
        logger.info(message)
        selected_entities = {}
        for qid, entity in tqdm(self.__entities.items(), colour="GREEN", desc="Filtering"):
            if filter(entity):
                selected_entities[qid] = entity
        self.__entities = selected_entities

    @classmethod
    def retrieve_entities_from_file(
        cls,
        cat_ids=list[str],
        qid_filename=f"{config.path_datadir}/hipparcos2007_qids",
        out_filename=f"{config.path_entitiesdir}/hipparcos2007_entities",
        save=False,
    ) -> dict[str, Any]|None:
        qids = io.read_list_json(qid_filename)
        if len(qids) == 0:
            return None
        cat_qids = [entry["qid"] for entry in qids if entry["id"] in cat_ids]
        entities = wiki.get_entities_batch(cat_qids)
        if save:
            io.write_dict_json(entities, out_filename)
        return entities

    @classmethod
    def retrieve_qids(cls, catalogue_ids: list[str], save=True, out_filename=f"{config.path_temp}/hipparcos2007_qids"):
        batch_size = 250
        start = 0
        end = batch_size
        totalStars = len(catalogue_ids)
        steps = math.ceil(totalStars / batch_size)
        qids = []
        for i in tqdm(range(0, steps), desc="Retrieving Hipparcos qids on Wikidata", colour="GREEN"):
            end = start + batch_size
            batch = catalogue_ids[start:end]
            batch_qids = wiki.get_qids_from_catalogue_entries("Q537199", "HIP", batch)
            batch_qids.sort(key=lambda x: int(x["id"].split(" ")[1]), reverse=False)
            qids.extend(batch_qids)
            start = end
            time.sleep(0.250)

        if save:
            io.write_list_json(qids, out_filename)

    def find_missing(
        self,
        qids_filename=f"{config.path_temp}/hipparcos2007_qids",
        missing_filename=f"{config.path_temp}/hipparcos2007_qids_missing",
    ):
        qids = io.read_list_json(qids_filename)
        hipparcos_catalog = io.read_list_json(f"{config.path_datadir}/hipparcos2007")

        retrieved_qids = set([int(x["id"].split(" ")[1]) for x in qids])
        catalogue_ids = set([x["id"] for x in hipparcos_catalog])
        missing_qids = catalogue_ids - retrieved_qids

        io.write_list_json(sorted(missing_qids), missing_filename)

    def crosscheck_missing(
        self,
        missing_filename=f"{config.path_temp}/hipparcos2007_qids_missing",
        catalogue_labels=["HD", "Gaia DR2", "Gaia DR3", "TYC"],
        main_label="HIP",
    ):
        missing_qids = io.read_list_json(missing_filename)
        crosscheck = simbad.cross_check([f"HIP {x}" for x in missing_qids], catalogue_labels, main_label)
        io.write_dict_json(crosscheck, missing_filename + "_simbad")

    def add(self, entities: list[WikidataStar]):
        for e in entities:
            self.__entities[e.qid] = e

    def save(self, out_filename: str):
        io.write_dict_json(self.__entities, out_filename)

    def query(self, id) -> WikidataStar | None:
        qid = self.__index.get(id, None)
        if qid is not None:
            return self.__entities.get(qid, None)
        else:
            return None
