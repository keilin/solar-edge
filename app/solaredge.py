import os
import time
from pathlib import Path

import requests

BASE_URL = "https://monitoringapi.solaredge.com/v2"
TOKEN_URL = f"{BASE_URL}/oauth2/token"


class SolarEdgeClient:
    """SolarEdge Monitoring API V2 client using OAuth 2.0 Site Access."""

    def __init__(self, session=None):
        self.site_id = os.environ["SOLAREDGE_SITE_ID"]
        self.client_id = os.environ["SOLAREDGE_CLIENT_ID"]
        self.client_secret = os.environ["SOLAREDGE_CLIENT_SECRET"]
        self.refresh_token = os.environ["SOLAREDGE_REFRESH_TOKEN"]
        self.session = session or requests
        self.access_token = None
        self.access_token_expires_at = 0

    def _persist_refresh_token(self, refresh_token):
        """Write the rotated token to a runner-local file for the workflow to save."""
        path = os.environ.get("SOLAREDGE_REFRESH_TOKEN_FILE")
        if path:
            Path(path).write_text(refresh_token)
        self.refresh_token = refresh_token

    def _refresh_access_token(self):
        response = self.session.post(
            TOKEN_URL,
            auth=(self.client_id, self.client_secret),
            json={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()

        access_token = payload.get("access_token")
        if not access_token:
            raise RuntimeError("SolarEdge OAuth response did not contain access_token")

        rotated_refresh_token = payload.get("refresh_token")
        if rotated_refresh_token:
            self._persist_refresh_token(rotated_refresh_token)

        self.access_token = access_token
        # Refresh a minute early to avoid using a token at its expiry boundary.
        self.access_token_expires_at = time.time() + int(payload.get("expires_in", 3600)) - 60

    def _get(self, endpoint, params=None):
        if not self.access_token or time.time() >= self.access_token_expires_at:
            self._refresh_access_token()

        response = self.session.get(
            f"{BASE_URL}/sites/{self.site_id}/{endpoint}",
            params=params or {},
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _unwrap_energy(payload):
        # V2 returns the energy object; tolerate the V1-style envelope as well.
        return payload.get("energy", payload) if isinstance(payload, dict) else payload

    def energy(self, start_date, end_date, unit="DAY"):
        payload = self._get(
            "energy",
            {
                "timeUnit": unit,
                "startDate": start_date,
                "endDate": end_date,
            },
        )
        return self._unwrap_energy(payload)

    def daily_energy(self, day):
        return self.energy(day, day)

    def monthly_energy(self, start_date, end_date):
        return self.energy(start_date, end_date, "MONTH")
