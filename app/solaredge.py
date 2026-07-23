import os
import requests
from datetime import date

BASE_URL = "https://monitoringapi.solaredge.com"


class SolarEdgeClient:
    def __init__(self):
        self.site_id = os.environ["SOLAREDGE_SITE_ID"]
        self.api_key = os.environ["SOLAREDGE_API_KEY"]

    def _get(self, path, params=None):
        params = params or {}
        params["api_key"] = self.api_key
        response = requests.get(
            f"{BASE_URL}/site/{self.site_id}/{path}",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def monthly_energy(self, year, month):
        data = self._get("energy", {
            "timeUnit": "MONTH",
            "startTime": f"{year}-{month:02d}-01",
        })
        return data

    def overview(self):
        return self._get("overview")
