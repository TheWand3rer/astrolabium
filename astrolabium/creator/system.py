from typing import Any
from astrolabium.creator import Star
import astropy.units as u


class System:
    def __init__(self, name: str, primary: Star = None):
        self.Name = name
        self.Orbiters: dict[str, Star] = {}
        if primary is not None:
            self.Orbiters["A"] = primary
        self.gc: str | None = None

    @property
    def primary(self) -> Star:
        return self.Orbiters["A"]

    @property
    def coordinates(self) -> str:
        return self.__coord

    @coordinates.setter
    def coordinates(self, value: str):
        self.__coord = value

    def to_dict(self) -> dict:
        json: dict[str, Any] = {}
        json["Name"] = self.Name

        x, y, z = self.primary.xyz
        self.gc = f"{round(float(x), 6)}, {round(float(y), 6)}, {round(float(z), 6)}"

        orbiters = {}

        for key, star in self.Orbiters.items():
            orbiters[key] = star.to_dict()

        json["Orbiters"] = orbiters
        json["c"] = self.gc

        return json

    def __iter__(self):
        return self

    def preorder_visit(self):
        for star in self.Orbiters.values():
            if star is not None:
                yield from Star.preorder_visit(star)

    @property
    def orbiters_catalogue_ids(self) -> list[str]:
        ids = []
        for star in self.preorder_visit():
            if star.id is not None:
                ids.append(star.id)
        return ids

    @property
    def stars(self) -> list[Star]:
        stars = []
        for star in self.preorder_visit():
            stars.append(star)
        return stars
