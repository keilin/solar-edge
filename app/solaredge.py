import os
import requests

BASE_URL = "https://monitoringapi.solaredge.com"


class SolarEdgeClient:
    def __init__(self):
        self.site_id = os.environ["SOLAREDGE_SITE_ID"]
        self.api_key = os.environ["SOLAREDGE_API_KEY"]

    def _get(self, endpoint, params=None):
        params = params or {}
        params["api_key"] = self.api_key
        response = requests.get(
            f"{BASE_URL}/site/{self.site_id}/{endpoint}",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def overview(self):
        return self._get("overview")

    def energy(self, start_date, end_date, unit="DAY"):
        return self._get("energy", {
            "timeUnit": unit,
            "startDate": start_date,
            "endDate": end_date,
        })

    def daily_energy(self, day):
        result = self.energy(day, day)
        return result.get("energy", {})

    def monthly_energy(self, start_date, end_date):
        return self.energy(start_date, end_date, "MONTH")
