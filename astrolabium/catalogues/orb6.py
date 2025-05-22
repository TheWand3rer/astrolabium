from astrolabium import config, fileIO as io
from astrolabium.parsers.data import Orb6Entry
from astrolabium.catalogues import CatalogueBase
from typing import Tuple


class Orb6(CatalogueBase[Orb6Entry]):
    def __init__(self, catalogue_path=f"{config.path_datadir}/orb6orbits"):
        super().__init__("WDS", catalogue_path, Orb6Entry)

    def select_entries(self, catalogue_ids):
        entries = super().select_entries(catalogue_ids)
        return self.__filter_duplicates(entries)

    def __filter_duplicates(self, entries: list[Orb6Entry]) -> list[Orb6Entry]:
        """
        in case of multiple orbits, keep only most recent one
        """
        confirmed_entries: dict[(str, str), Orb6Entry] = {}
        for entry in entries:
            if not hasattr(entry, "comp"):
                continue
            key = (entry.WDS, entry.comp)

            if key in confirmed_entries:
                confirmed = confirmed_entries[key]
                entry_hasLast = hasattr(entry, "last")
                confirmed_hasLast = hasattr(confirmed, "last")
                if (entry_hasLast and confirmed_hasLast and entry.last > confirmed.last) or (
                    entry_hasLast and not confirmed_hasLast
                ):
                    confirmed_entries[key] = entry

            else:
                confirmed_entries[key] = entry

        return list(confirmed_entries.values())
