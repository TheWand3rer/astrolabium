from astrolabium.creator import System, Star
from astrolabium import fileIO as io
import json
from typing import Any


class Galaxy:
    def __init__(self, systems: list[System]):
        self.Name = "Milky Way"
        self.systems: dict[str, System] = {}

        for system in systems:
            self.systems[system.Name] = system
        pass

    @property
    def count(self) -> int:
        return len(self.systems)

    def save(self, out_filename: str):
        json_galaxy = {}

        json_galaxy["Name"] = self.Name
        json_galaxy["Systems"] = {name: system.to_dict() for name, system in self.systems.items()}

        io.write_text_json(json.dumps(json_galaxy, indent=2), out_filename)

    def add_systems(self, systems: list[System]):
        self.systems = self.systems | {system.Name: system for system in systems}

    def select(self, system_name: str) -> System | None:
        return self.systems.get(system_name)
