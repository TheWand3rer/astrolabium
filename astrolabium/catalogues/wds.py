import os
from astrolabium import config, fileIO as io
from astrolabium.parsers.data import WDSEntry
from astrolabium.catalogues import CatalogueBase
import astropy.units as u
from collections import defaultdict
from typing import Tuple


class WDS(CatalogueBase[WDSEntry]):
    def __init__(self, catalogue_path=f"{config.path_datadir}/wds", catalogue_data=None):
        super().__init__("WDS", catalogue_path, WDSEntry, catalogue_data)

    def select_entries_grouped(
        self, wds_ids_comp: dict[str, list[str]] = None, wds_ids: list[str] = None, physical=True
    ) -> dict[str, list[WDSEntry]]:
        entries = defaultdict(list)
        if isinstance(wds_ids, list):
            for id in wds_ids:
                for entry in self.select_entries(id):
                    if entry.is_physical == physical:
                        entries[id].append(entry)
            return entries

        if wds_ids_comp is None:
            raise ValueError("Invalid or no arguments provided")

        for id, comp in wds_ids_comp.items():
            wds_entries = self.select_entries([id])
            for entry in wds_entries:
                if entry is not None:
                    entry_comp = getattr(entry, "comp", None)
                    if entry_comp is not None:
                        components = WDS.parse_components(entry_comp)
                    else:
                        continue

                    if bool(set(components) & set(comp)) and entry.is_physical == physical:
                        entries[id].append(entry)
        return entries

    @classmethod
    def parse_components(cls, comp_str: str) -> list[str]:
        """
        Parses component strings like 'AB', 'Aa,Ab', 'AC-D', 'Ca,Cb', etc.
        Returns a list of component pairs like ['A', 'B'], ['Aa', 'Ab'], etc.
        """

        # Stars in a system are usually denoted A, B, C (in order of brightness)
        # However later discoveries might have identified closer companions,
        # which could have been called Aa Ab Ac, etc.

        if "," in comp_str:
            components = [c.strip() for c in comp_str.split(",")]
        elif len(comp_str) == 2:
            components = [comp_str[0], comp_str[1]]
        else:
            components = [comp_str]

        return components

    @classmethod
    def normalise_components(cls, components: list[str]) -> Tuple[list[str], bool]:
        components_processed = []
        is_group = False
        for i, s in enumerate(components):
            if len(s) == 2:
                if s[1] == "a":
                    # We assume that A and Aa refer to the same star (likewise B and Ba, C and Ca, etc.) and
                    # thus pre-process the strings accordingly, to ensure they match.
                    s = s[0]
                elif s.isupper():
                    # Case where a component could be AB or BC
                    # in this case one star is orbiting a group of stars
                    # if the group is the first in the pair, e.g. AB, C
                    # for practical data serialization purposes, we assume C is orbiting A
                    # or rather, the centre of mass of the first "level" (AB) of the tree
                    #
                    # *
                    # ├── A
                    # │   └── C
                    # └── B
                    #
                    # otherwise in the case of A,BC we assume the following hierarchy
                    # A / B / C (B is orbiting A, C is orbiting B)
                    # we get A / B from this entry, but there should  be another entry with just BC
                    s = s[0]
                    if i == 1:
                        # Special case of type A,BC -> we assume B is orbiting A
                        # if instead it was AB, we assume both orbit the CoM
                        is_group = True
            components_processed.append(s)
        return components_processed, is_group
