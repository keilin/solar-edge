import os
import time
from datetime import date, datetime, time as datetime_time
from zoneinfo import ZoneInfo
from pathlib import Path

import requests

BASE_URL = "https://monitoringapi.solaredge.com/v2"
TOKEN_URL = f"{BASE_URL}/oauth2/token"
SITE_TIMEZONE = ZoneInfo("America/Los_Angeles")


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
        # SolarEdge Monitoring API V2 expects OAuth token parameters as JSON.
        # Its token service can return transient 5xx errors; retry those
        # without changing the refresh token. Do not retry 4xx responses,
        # which usually indicate a credential or grant problem.
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                response = self.session.post(
                    TOKEN_URL,
                    json={
                        "grant_type": "refresh_token",
                        "refresh_token": self.refresh_token,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    headers={"Accept": "application/json"},
                    timeout=30,
                )
            except requests.RequestException as exc:
                # A timeout can occur after SolarEdge has already rotated the
                # refresh token. Retrying an ambiguous request could then
                # replay an invalidated token, so fail rather than risk that.
                raise RuntimeError(
                    f"SolarEdge OAuth token refresh request failed: {exc}"
                ) from exc

            if response.status_code in (500, 502, 503, 504, 429):
                if attempt == max_attempts - 1:
                    detail = getattr(response, "text", "")
                    raise RuntimeError(
                        f"SolarEdge OAuth token refresh failed after "
                        f"{max_attempts} attempts (HTTP "
                        f"{response.status_code}): {detail}"
                    )
                retry_after = getattr(response, "headers", {}).get("Retry-After")
                try:
                    delay = max(1, int(float(retry_after))) if retry_after else min(5 * (2 ** attempt), 60)
                except (TypeError, ValueError):
                    delay = min(5 * (2 ** attempt), 60)
                print(
                    f"SolarEdge OAuth endpoint returned HTTP "
                    f"{response.status_code}; retrying in {delay} seconds "
                    f"(attempt {attempt + 2}/{max_attempts}).",
                    flush=True,
                )
                time.sleep(delay)
                continue

            try:
                response.raise_for_status()
            except requests.HTTPError as exc:
                detail = getattr(response, "text", "")
                raise RuntimeError(
                    f"SolarEdge OAuth token refresh failed (HTTP "
                    f"{response.status_code}): {detail}"
                ) from exc
            break

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

        url = f"{BASE_URL}/sites/{self.site_id}/{endpoint}"
        # SolarEdge applies a burst rate limit. Backfills make many sequential
        # requests, so honor Retry-After when supplied and otherwise use
        # exponential backoff. Do not refresh OAuth credentials on a 429.
        for attempt in range(6):
            response = self.session.get(
                url,
                params=params or {},
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=30,
            )
            if response.status_code == 429:
                if attempt == 5:
                    detail = getattr(response, "text", "")
                    raise RuntimeError(
                        f"SolarEdge API rate limit persisted after 6 attempts "
                        f"for {endpoint}: {detail}"
                    )
                retry_after = getattr(response, "headers", {}).get("Retry-After")
                try:
                    delay = max(1, int(float(retry_after))) if retry_after else min(60 * (2 ** attempt), 900)
                except (TypeError, ValueError):
                    delay = min(60 * (2 ** attempt), 900)
                print(
                    f"SolarEdge rate limit (HTTP 429) for {endpoint}; "
                    f"retrying in {delay} seconds (attempt {attempt + 2}/6).",
                    flush=True,
                )
                time.sleep(delay)
                continue
            try:
                response.raise_for_status()
            except requests.HTTPError as exc:
                detail = getattr(response, "text", "")
                raise RuntimeError(
                    f"SolarEdge API request failed (HTTP {response.status_code}) "
                    f"for {endpoint}: {detail}"
                ) from exc
            return response.json()

    @staticmethod
    def _unwrap_energy(payload):
        # V2 returns the energy object; tolerate the V1-style envelope as well.
        return payload.get("energy", payload) if isinstance(payload, dict) else payload

    def energy(self, start_date, end_date, unit="DAY"):
        # V2 requires offset-aware local timestamps in "from" and "to".
        # Date-only V1 parameters are silently ignored by the V2 endpoint.
        start = datetime.combine(
            date.fromisoformat(start_date), datetime_time.min, SITE_TIMEZONE
        )
        end = datetime.combine(
            date.fromisoformat(end_date),
            datetime_time(23, 59, 59),
            SITE_TIMEZONE,
        )
        payload = self._get(
            "energy",
            {
                "resolution": unit,
                "unit": "WH",
                "from": start.isoformat(timespec="seconds"),
                "to": end.isoformat(timespec="seconds"),
            },
        )
        return self._unwrap_energy(payload)

    def daily_energy(self, day):
        return self.energy(day, day)

    def monthly_energy(self, start_date, end_date):
        return self.energy(start_date, end_date, "MONTH")
