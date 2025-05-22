from astrolabium import fileIO as io
from typing import Type


class CatalogueBase[T]:
    def __init__(
        self, catalogue_label: str, catalogue_path: str, entry_class: Type[T], catalogue_data: list | None = None
    ):
        self.__catalogue_label = catalogue_label
        self.catalogue_path = catalogue_path
        if catalogue_data is None:
            catalogue_data = io.read_list_json(self.catalogue_path)
            if len(catalogue_data) == 0:
                raise FileNotFoundError(f"Parsed {catalogue_label} catalogue not found in {catalogue_path}")

        if not any(isinstance(entry, entry_class) for entry in catalogue_data):
            self._entries = list(map(entry_class, catalogue_data))
        else:
            self._entries = catalogue_data

    @property
    def label(self) -> str:
        return self.__catalogue_label

    @property
    def count(self) -> int:
        return len(self._entries)

    @property
    def entries(self) -> list[T]:
        return self._entries

    @entries.setter
    def entries(self, value: list[T]):
        self._entries = value

    def select(self, catalogue_id: str) -> T | None:
        try:
            return next(x for x in self._entries if getattr(x, self.__catalogue_label, None) == catalogue_id)
        except StopIteration:
            print(f"Cannot find entry [{self.__catalogue_label}: {catalogue_id}]")
            return None

    def select_entries(self, catalogue_ids: list[str], filter=False) -> list[T]:
        result = [entry for entry in self.entries if getattr(entry, self.__catalogue_label, None) in catalogue_ids]

        if filter:
            self._entries = result

        return result
