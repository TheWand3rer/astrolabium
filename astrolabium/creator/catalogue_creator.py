from astrolabium import fileIO as io, config
from astrolabium.parsers import HipparcosParser, WDSParser, Orb6Parser
from astrolabium.parsers.data import WikidataStar, Text
from astrolabium.catalogues import Hipparcos, WDS, Crossref, filters
from astrolabium.queries import WikiEntities, gaia
from astrolabium.creator import WDSAnalyser, Star, System, Galaxy
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class CatalogueCreator:
    def __init__(
        self,
        lyr=100,
        catalogue_path=f"{config.path_datadir}/hipparcos2007",
        entities_path=f"{config.path_entitiesdir}/hipparcos2007_entities",
        verbose=False,
    ):
        self.verbose = verbose
        self.lyr = lyr
        self.catalogue_path = catalogue_path
        self.entities_path = entities_path
        self.iau_entities_path = f"{config.path_entitiesdir}/IAU_entities"
        self.output_catalogue_path = f"{config.path_outdir}/catalogue_{self.lyr}_ly"
        self._use_entities = True
        self._analyser: WDSAnalyser = None
        logging.root.setLevel(logging.INFO)
        logging.basicConfig(format="%(message)s")
        logger.info("Astrolabium v0.1.0 by Vindemiatrix Collective (https://vindemiatrixcollective.com)\n")
        io.create_directory(config.path_entitiesdir)
        io.create_directory(config.path_datadir)
        io.create_directory(config.path_temp)
        io.create_directory(config.path_outdir)
        if not io.file_exists(entities_path):
            self._use_entities = False
        pass

    @classmethod
    def download_and_parse_catalogues(cls):
        io.create_directory(config.path_cataloguedir)
        stars = HipparcosParser.run()
        WDSParser.run()
        Orb6Parser.run()
        hip = Hipparcos(catalogue_data=stars)
        Crossref.build_table("HIP", [str(x.HIP) for x in hip.entries], Crossref.catalogue_labels, save=True)

    def find_star_systems(self, query_filters: list[Callable] = None, rebuild=False) -> list[System]:
        hip_stars_path = f"{config.path_temp}/catalogue_stars_{self.lyr}_ly"
        if not rebuild:
            systems_within_distance = io.read_list_json(hip_stars_path)
        else:
            systems_within_distance = None

        if not systems_within_distance or rebuild:
            logger.info(f"Filtering star systems within {self.lyr} ly")
            if not query_filters:
                query_filters = [
                    lambda star: filters.distance(star, self.lyr),
                    lambda star: filters.any_catalogues(star, ["b", "fl", "Name"]),
                ]

            crossref = Crossref()
            hipparcos = Hipparcos()
            systems_within_distance = crossref.query_filters(hipparcos.entries, "HIP", query_filters, hip_stars_path)

        if systems_within_distance is None or len(systems_within_distance) == 0:
            raise ValueError("No single stars found: are the filters too stringent?")

        logger.info(f"Found {len(systems_within_distance)} / {Hipparcos.num_entries()} stars within {self.lyr} lyr")

        systems = []
        for entry in systems_within_distance:
            if "WDS" in entry:
                continue
            star = Star(catalogue_entry=entry, crossref=entry)
            name = Text.classic_system_name(entry)
            systems.append(System(name, star))

        logger.info(f"   of which {len(systems)} are single star systems")
        logger.info(f"   and {len(systems_within_distance) - len(systems)} are potential multiple star systems")

        return systems

    def find_multiple_systems(self, query_filters: list[Callable] = None, rebuild=False):
        wds_stars_path = f"{config.path_temp}/wds_stars_{self.lyr}_ly"
        if not rebuild:
            mult_systems = io.read_list_json(wds_stars_path)
        else:
            mult_systems = None

        if not mult_systems or rebuild:
            hipparcos = Hipparcos()
            wds = WDS()
            if not query_filters:
                query_filters = [
                    lambda star: filters.distance(star, self.lyr),
                    lambda star: filters.any_catalogues(star, ["WDS"]),
                    lambda star: filters.any_catalogues(star, ["b", "fl", "Name"]),
                    lambda star: filters.wds_is_physical(star, wds),
                ]

            crossref = Crossref()
            mult_systems = crossref.query_filters(hipparcos.entries, "HIP", query_filters, wds_stars_path)

        if mult_systems is None or len(mult_systems) == 0:
            raise ValueError("No multiple stars found: are the filters too stringent?")
        logger.info("Analysing multiple star systems")
        self._analyser = WDSAnalyser(crossref_data=mult_systems, verbose=self.verbose)

        systems = self._analyser.analyse()
        return systems

    def __match_systems_to_entities(self, systems: list[System], save=True):
        entities_path = f"{config.path_temp}/catalogue_{self.lyr}_ly_entities"
        wiki_entities = io.read_dict_json(entities_path)

        catalogue_ids = []
        for system in systems:
            catalogue_ids += system.orbiters_catalogue_ids

        if not wiki_entities:
            wiki_entities = io.read_dict_json(self.entities_path)
            if not wiki_entities:
                logger.warning("WARNING: Wikidata entity file not available, retrieving from wikidata")
                wiki_entities = WikiEntities.retrieve_entities_from_file(catalogue_ids, self.entities_path)
            wikiCatalog = WikiEntities(wiki_entities)
            wikiCatalog.filter(lambda e: f"HIP {e.cat['hip']}" in catalogue_ids, "> Selecting stars in Hipparcos 2007 catalogue")
            if save:
                wikiCatalog.save(entities_path)
        else:
            wikiCatalog = WikiEntities(wiki_entities)

        wikiCatalog.add(self.get_stars_from_IAU())
        logger.info(f"> HIP: found {wikiCatalog.count} wikidata entities within {self.lyr} lyr distance")
        wikiCatalog.build_index("HIP")

        for system in systems:
            for star in system.preorder_visit():
                entity = wikiCatalog.query(star.id)
                if entity is not None:
                    star.add_properties(entity)

    def update_names_from_IAU(self, table, namekey="Name"):
        # TODO: ensure IAU names overwrite names we might get from other sources
        raise NotImplementedError("Todo")
        iau_data = io.read_list_json(f"{config.path_datadir}/IAU-CSN.json")

    def get_stars_from_IAU(self) -> list[WikidataStar]:
        iau = WikiEntities(io.read_dict_json(self.iau_entities_path))

        iau.filter(
            lambda e: "hip" not in e.cat,
            "> Adding missing star from IAU",
        )
        iau.filter(lambda e: WikiEntities.filter_distance(e, self.lyr), f"> Removing stars farther than {self.lyr} ly")
        logger.warning(f"> Found {iau.count} stars missing from HIP catalogue")
        return iau.values

    def update_from_gaia(self, stars: dict[str, "Star"]):
        stars_dr3 = {star.dr3: star for key, star in stars.items() if hasattr(star, "dr3")}
        source_ids = list(stars_dr3.keys())
        if len(source_ids) == 0:
            source_ids = [2067518817314952576, 3211922645854328832, 66529975427235712]
        data = gaia.retrieve_data(source_ids)
        gaia.update_data(stars_dr3, data)

    def query_multiple_system(self, wds_id: str):
        if self._analyser is None:
            raise ValueError("Please run <find_multiple_systems()> first.")

        self._analyser.query_system(wds_id)

    def create(self, single_filters=list[Callable] | None, multiple_filters=list[Callable] | None, rebuild=False, match_to_wikidata_entities=True, save=True):
        single_stars = self.find_star_systems(query_filters=single_filters, rebuild=rebuild)
        multiple_stars = self.find_multiple_systems(query_filters=multiple_filters, rebuild=rebuild)
        total_systems = single_stars + multiple_stars

        if not self._use_entities and match_to_wikidata_entities:
            logger.warning("No Wikidata entities file found. Download it from the github repo and place it in your entities/ folder.")
        elif match_to_wikidata_entities:
            self.__match_systems_to_entities(total_systems)

        logger.info("Catalogue creation complete")
        galaxy = Galaxy(total_systems)
        if save:
            galaxy.save(self.output_catalogue_path)
            logger.info(f"Saved to {self.output_catalogue_path}")
        return galaxy
