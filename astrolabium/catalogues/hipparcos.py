from astrolabium import config, fileIO as io
from astrolabium.catalogues import CatalogueBase
from astrolabium.parsers.data.hip_entry import HipparcosEntry
from typing import Any


class Hipparcos(CatalogueBase[HipparcosEntry]):
    def __init__(self, catalogue_path=f"{config.path_datadir}/hipparcos2007", catalogue_data: list[Any] = None):
        super().__init__("HIP", catalogue_path, HipparcosEntry, catalogue_data)

    @classmethod
    def num_entries(cls) -> int:
        return 117955
