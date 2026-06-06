from astrolabium.creator import System, Star
from astrolabium import fileIO as io
import json
from typing import Any


class Galaxy:
    def __init__(
        self,
        systems: list[System],
        lyr: float | None = None,
        version: str | None = None,
        timestamp: str | None = None,
    ):
        self.Name = "Milky Way"
        self.systems: dict[str, System] = {}
        self._metadata: dict[str, Any] = {}
        if lyr is not None:
            self._metadata["lyr"] = lyr
        if version is not None:
            self._metadata["version"] = version
        if timestamp is not None:
            self._metadata["timestamp"] = timestamp

        for system in systems:
            self.systems[system.Name] = system

    @property
    def count(self) -> int:
        return len(self.systems)

    def save(self, out_filename: str):
        json_galaxy: dict[str, Any] = {}

        json_galaxy["Name"] = self.Name
        json_galaxy["Systems"] = {name: system.to_dict() for name, system in self.systems.items()}

        if self._metadata:
            json_galaxy["Metadata"] = {k: v for k, v in self._metadata.items()}

        io.write_text_json(json.dumps(json_galaxy, indent=2), out_filename)

    def add_systems(self, systems: list[System]):
        self.systems = self.systems | {system.Name: system for system in systems}

    def select(self, system_name: str) -> System | None:
        return self.systems.get(system_name)
