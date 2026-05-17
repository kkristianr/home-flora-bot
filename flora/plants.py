import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Plant:
    slug: str
    name: str
    plant_id: str
    sensor_address: str | None = None


class PlantRegistry:
    def __init__(self, config_path: Path):
        self.config_path = config_path

    def all(self) -> list[Plant]:
        with self.config_path.open() as config_file:
            data = json.load(config_file)
        return [Plant(**plant) for plant in data["plants"]]

    def get(self, slug: str) -> Plant:
        for plant in self.all():
            if plant.slug == slug:
                return plant
        raise KeyError(slug)
