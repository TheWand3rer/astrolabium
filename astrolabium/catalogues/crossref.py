from typing import Any, Tuple, Callable
import os
from astrolabium import config, fileIO as io, Table
from astrolabium.parsers.data import EntryBase
import astropy.units as u
from astrolabium.queries import simbad
from astrolabium.catalogues import filters


class Crossref:
    catalogue_labels = [
        "NAME",
        "b",
        "fl",
        "TYC",
        "HD",
        "HR",
        "GJ",
        "WDS",
        "2MASS",
        "PSR",
        "Gaia DR2",
        "Gaia DR3",
    ]

    def __init__(self, crossref_table_path=f"{config.path_datadir}/crossref_table", crossref_data: list[Any] = None):
        self.crossref_table_path = crossref_table_path
        if crossref_data is None:
            self.table = io.read_list_json(self.crossref_table_path)
            if (len(self.table)==0):
                raise ValueError(f"Crossref table not found in f{self.crossref_table_path}")
        else:
            self.table = crossref_data
        pass

    def select(self, catalogue_label: str) -> list[Any]:
        return [entry for entry in self.table if filters.any_catalogues(entry, catalogue_label)]

    def select_ids(self, catalogue_label: str) -> list[str]:
        return [entry[catalogue_label] for entry in self.select(catalogue_label)]

    def query_distance(
        self,
        stars: list,
        distance,
        main_catalogue_id,
        other_catalogue_labels: list[str] | None = None,
        distance_key="d",
        save_path: str | None = None,
    ) -> list[Any]:
        query_filters = [
            lambda star: filters.distance(star, distance, distance_key),
        ]
        if other_catalogue_labels is not None:
            query_filters.append(lambda star: filters.any_catalogues(star, other_catalogue_labels))

        return self.query_filters(stars, main_catalogue_id, query_filters, save_path)

    def query_filters(
        self,
        stars: list[EntryBase],
        catalogue_label: str,
        filters: list[Callable] = filters.crossref_filters,
        save_path: str | None = None,
    ) -> list[Any]:
        cross_table = Table.join(stars, self.table, catalogue_label)
        result = [star for star in cross_table if all(lambda_star(star) for lambda_star in filters)]
        if save_path:
            io.write_list_json(result, save_path)
        return result

    def query_catalogue_partial(self, catalogue_code: str) -> list[Any]:
        catalogue_label, catalogue_id = self.__split_catalogue_code(catalogue_code)
        return [
            entry
            for entry in self.table
            if catalogue_label in entry and self.__id_match_partial(entry, catalogue_label, catalogue_id)
        ]

    def query_catalogue_code(self, catalogue_code: str) -> Any:
        catalogue_label, catalogue_id = self.__split_catalogue_code(catalogue_code)
        return self.query_catalog_id(catalogue_label, catalogue_id)

    def query_catalog_id(self, catalogue_label: str, catalogue_id: str) -> Any:
        return next(
            entry
            for entry in self.table
            if catalogue_label in entry and self.__id_match_exact(entry, catalogue_label, catalogue_id)
        )

    def __split_catalogue_code(self, catalogue_code) -> Tuple[str, str]:
        catalogue_parts = catalogue_code.split(" ")
        catalogue_label = catalogue_parts[0]
        catalogue_id = catalogue_parts[1]
        return catalogue_label, catalogue_id

    def __id_match_partial(self, e, catalogue_label, catalogue_id):
        return catalogue_id in e[catalogue_label]

    def __id_match_exact(self, e, catalogue_label, catalogue_id):
        return e[catalogue_label] == catalogue_id

    @classmethod
    def build_table(
        self,
        main_id: str,
        catalogue_ids: list[str],
        selected_catalogs: list[str] = [],
        crossref_path=f"{config.path_datadir}/crossref_table",
        exclude_label=False,
        save=True,
    ) -> list[Any]:
        """
        Queries simbad and retrieve all matching identifiers from the list provided.
        """
        if not selected_catalogs or len(selected_catalogs) == 0:
            selected_catalogs = self.catalogue_labels

        crossref = simbad.cross_check(catalogue_ids, selected_catalogs, main_id, exclude_label=exclude_label)
        if save and crossref:
            io.write_list_json(crossref, crossref_path)
        return crossref
