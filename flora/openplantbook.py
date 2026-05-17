from datetime import timedelta
from typing import Any
from urllib.parse import quote

import requests

from .storage import Storage
from .time import parse_time, utc_now

CACHE_TTL = timedelta(days=7)


class OpenPlantbookClient:
    def __init__(self, base_url: str, api_key: str, storage: Storage):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.storage = storage

    def detail(self, plant_id: str) -> dict[str, Any]:
        cached = self.storage.get_cached_plant(plant_id)
        if cached:
            fetched_at, payload = cached
            if utc_now() - parse_time(fetched_at) < CACHE_TTL:
                return payload

        encoded_plant_id = quote(plant_id, safe="")
        url = f"{self.base_url}/plant/detail/{encoded_plant_id}"
        response = requests.get(url, headers=self._headers(), timeout=20)
        if response.status_code == 404:
            response = requests.get(f"{url}/", headers=self._headers(), timeout=20)
        response.raise_for_status()
        payload = response.json()
        self.storage.set_cached_plant(plant_id, payload)
        return payload

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Token {self.api_key}"
        return headers
