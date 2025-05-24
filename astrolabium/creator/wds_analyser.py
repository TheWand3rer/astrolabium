from astrolabium.creator import Star, System
from astrolabium.parsers.data import HipparcosEntry, WDSEntry, Orb6Entry, Text
from astrolabium.catalogues import Orb6, WDS, Crossref, Hipparcos, CatalogueBase
from anytree import Node, RenderTree, find, findall, PreOrderIter
from collections import defaultdict
from typing import List, Any, Tuple
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)


class WDSAnalyser:
    def __init__(self, crossref_data: list[Any], verbose=False):
        self.verbose = verbose
        self.crossref = Crossref(crossref_data=crossref_data)
        self.catalogue = Hipparcos(catalogue_data=crossref_data)

        wds_ids: defaultdict[str, list[str]] = defaultdict(list)
        wds_entries = [{entry["WDS"][1:11]: entry["WDS"][11:]} for entry in self.crossref.select("WDS")]

        for dict in wds_entries:
            for id, comp in dict.items():
                wds_ids[id].extend(WDS.parse_components(comp))

        self.__wds = WDS()
        self.__wds.select_entries(wds_ids.keys(), filter=True)
        self.wds_groups = self.__wds.select_entries_grouped(wds_ids_comp=wds_ids)
        self.__orb6 = Orb6()

        pass

    def __find_catalogue_entries(self, crossref_entries: list[Any]) -> dict[str, HipparcosEntry | None]:
        # Both the WDS and Orb6 catalogues have entries for each pair of stars
        # but they don't report catalogue ids for the individual stars.
        # For example, in Orb6 there are two entries for Alpha Centauri
        # and both refer to alf01 Cen A or HIP 71683 (Rigel).
        # However the companion is alf02 Cen or HIP 71681 (Toliman).
        # There is also alf Cen C (Proxima) or HIP 70890.
        # The crossref table reports different catalogue codes for the same
        # (partial) WDS code. E.g. J14396-6050 (alf Cen) appears as
        # J14396-6050A, J14396-6050B, and J14396-6050C for each of the
        # three components. But this differentiation is missing for several other stars.
        #
        # So here we attempt to match crossref entries to components of this system.

        entries: dict[str, HipparcosEntry | None] = {}
        for entry in crossref_entries:
            comp = entry["WDS"][11:]
            component: str = None
            if len(comp) == 1:
                component = comp
            elif len(comp) == 2:
                component = comp[0]
            elif len(comp) > 2:
                components = comp.split(",")
                component = components[0]

            if len(component) > 1 and component[1] == "a":
                component = component[0]

            if component is not None:
                # if len(component) > 1 and component[1] == "a":  # e.g. Aa, Ba, Ca ... -> A, B, C
                #     component = component[0]
                id = entry[self.catalogue.label]
                star_match = self.catalogue.select(id)
                if star_match is not None:
                    if self.verbose:
                        logger.info(f"Found match for {component}: {self.catalogue.label} {id}")
                    entries[component] = star_match
                    continue

            if self.verbose:
                logger.info(f"No match found for {component}: in {entry['WDS'][1:10]}")

        return entries

    def __detect_hierarchy(self, wds_id: str, components: List[WDSEntry]) -> System | None:
        """
        Builds a nested hierarchy of star components.
        """

        spectral_types = {}
        for c in components:
            if not hasattr(c, "comp"):
                c.comp = "AB"  # assume that this is a "simple" binary star with only two components

        components = sorted(components, key=lambda x: x.comp)

        root = Node("*")
        stars = set()
        if self.verbose:
            logger.info(f"{wds_id}: {[c.comp for c in components]}")
        for entry in components:
            sub, is_group = WDS.normalise_components(WDS.parse_components(entry.comp))
            if entry.st is not None:
                st_pair = entry.st.split("+")
            else:
                st_pair = [None, None]

            if len(sub) == 2:
                star1, star2 = sub
                stars.add(star1)
                stars.add(star2)

                if star1 not in spectral_types:
                    spectral_types[star1] = st_pair[0]
                if star2 not in spectral_types and len(st_pair) == 2:
                    spectral_types[star2] = st_pair[1]

                nodes = findall(root, lambda n: n.name == star1, maxcount=2)
                if len(nodes) == 0:
                    node1 = Node(star1, parent=root)
                    if is_group:
                        node2 = Node(star2, parent=node1)
                    else:
                        node2 = Node(star2, parent=root)
                else:
                    node = nodes[0]
                    node1 = Node(star2, parent=node)
                    nodes = findall(root, lambda n: n.name == star2, maxcount=2)
                    if len(nodes) == 1:
                        node = nodes[0]
                        if node.parent.name != node1.parent.name:  # use other node parent
                            node.parent = None
                    else:
                        if len(nodes) == 2:
                            depth1 = nodes[0].depth
                            depth2 = nodes[1].depth
                            if depth1 > depth2:
                                nodes[1].parent = None  # keep node with the most depth
                            else:
                                nodes[0].parent = None  # keep node with the most depth
                        else:
                            raise ValueError("Unexpected branch")
            else:
                if len(sub) == 1:
                    component = sub[0] if sub[0] != "" else "A"
                    Node(component, parent=root)
                else:
                    raise ValueError("Unexpected branch")

        if self.__check_duplicates(root) and self.verbose:
            logger.info(f"{wds_id} checked: no duplicates")
        else:
            self.__prune(root, stars)
            if not self.__check_duplicates(root):
                raise ValueError(f"${wds_id}: cannot build system hierarchy")

        system_crossref = self.crossref.query_catalogue_partial(f"WDS {wds_id}")
        companion_orbits = self.__find_orbits(root, self.__orb6.select_entries(wds_id))
        stars_catalog = self.__find_catalogue_entries(system_crossref)

        if "A" not in stars_catalog:
            return None

        if stars_catalog is not None:
            for component in stars:
                if component not in stars_catalog:
                    stars_catalog[component] = None

        if self.verbose:
            self.print_system_tree(root)
        system = self.__create_system(root, stars_catalog, companion_orbits, system_crossref, spectral_types)
        return system

    def __create_system(
        self,
        root: Node,
        stars: dict[str, HipparcosEntry | None],
        orbits: dict[str, Orb6Entry],
        crossref: list[Any],
        spectral_types=dict[str, str],
    ) -> System:
        primary = stars["A"]
        assert primary is not None, "primary"

        crossref_entry = self.crossref.query_catalogue_code(primary.id)
        system = System(Text.classic_system_name(crossref_entry))

        matched_stars: dict[str, Star] = {}
        found_orbits = 0
        for node in PreOrderIter(root):
            if node.name == "*":
                continue

            orbiter_entry = stars.get(node.name, None)
            orbiter_orbit = orbits.get(node.name, None)
            orbiter_crossref = None
            if orbiter_orbit is not None:
                found_orbits += 1

            orbiter = None

            if orbiter_entry:
                orbiter_crossref = next(x for x in crossref if x["HIP"] == orbiter_entry.HIP)
                orbiter = Star(orbiter_entry, orbiter_orbit, orbiter_crossref)
            else:
                orbiter = Star(stars["A"], orbiter_orbit, orbiter_crossref)

            if orbiter.Name is None:
                orbiter.Name = node.name

            matched_stars[node.name] = orbiter
            if node.name in spectral_types and not hasattr(orbiter, "st"):
                orbiter.sc = spectral_types[node.name]

            if node.parent.name == "*":
                assert orbiter is not None, "orbiter"
                system.Orbiters[node.name] = orbiter
            else:
                star = matched_stars[node.parent.name]
                assert star is not None
                assert star.Orbiters is not None, "Orbiters"
                star.Orbiters[node.name] = orbiter

        assert len(orbits) == found_orbits, "System contains orbit but no match was found"
        return system

    def __find_orbits(self, com: Node, orbits: list["Orb6Entry"]) -> dict[str, Orb6Entry]:
        stars_with_orbits = {}
        for orbit in orbits:
            if orbit.comp is None:
                continue

            if len(orbit.comp) == 1:
                companion_star = orbit.comp
            elif len(orbit.comp) == 2:
                if orbit.comp.isupper():
                    companion_star = orbit.comp[1]
                else:
                    raise ValueError(orbit.comp)
            else:
                companion_star = orbit.comp.split(",")[1]

            node = find(com, lambda n: n.name == companion_star)
            if node is None:
                if self.verbose:
                    logger.info(f"Star [{companion_star}] is not present in WDS catalogues or is not physical")
                continue
            stars_with_orbits[node.name] = orbit
        return stars_with_orbits

    def __check_duplicates(self, root: Node):
        comps = set()
        for node in PreOrderIter(root):
            if node.name in comps:
                return False
            else:
                comps.add(node.name)
        return True

    def __prune(self, root, stars):
        for idx in stars:
            nodes = findall(root, lambda n: n.name == idx, maxcount=2)
            if len(nodes) == 2:
                parent1 = nodes[0].parent
                parent2 = nodes[1].parent
                if (parent1.name[0]) == "A":
                    prune_node = nodes[0]
                else:
                    prune_node = nodes[1]
                prune_node.parent = None

    def print_system_tree(self, com):
        for pre, _, node in RenderTree(com):
            print("%s%s" % (pre, node.name))

    def analyse(self) -> list[System]:
        """
        Accepts a list of WDS entries.
        Returns a list of System objects.
        """

        systems = []
        invalid_systems = 0
        for wds_id, components in tqdm(self.wds_groups.items(), desc="Analysing"):
            system = self.__detect_hierarchy(wds_id, components)
            if system is None:
                invalid_systems += 1
                continue
            systems.append(system)

        logger.info(f"Analysed {len(self.wds_groups)} system, of which {invalid_systems} were invalid")
        return systems

    def query_system(self, wds_id: str = "14396-6050") -> System | None:
        """
        Reconstructs the hierarchy of the given WDS id entries using information from ORB6.
        "14396-6050" corresponds to the entries for the Alpha Centauri AB(C) system
        """
        wds_entries = self.__wds.select_entries([wds_id])
        return self.__detect_hierarchy(wds_id, wds_entries)
