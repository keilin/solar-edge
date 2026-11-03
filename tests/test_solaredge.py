import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from app.solaredge import SolarEdgeClient, TOKEN_URL, BASE_URL


class SolarEdgeClientTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "SOLAREDGE_SITE_ID": "12345",
            "SOLAREDGE_CLIENT_ID": "client-id",
            "SOLAREDGE_CLIENT_SECRET": "client-secret",
            "SOLAREDGE_REFRESH_TOKEN": "refresh-old",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.session = Mock()
        self.client = SolarEdgeClient(session=self.session)

    def response(self, payload):
        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        return response

    def test_refresh_uses_basic_auth_and_rotates_refresh_token(self):
        with tempfile.NamedTemporaryFile() as token_file:
            os.environ["SOLAREDGE_REFRESH_TOKEN_FILE"] = token_file.name
            self.addCleanup(os.environ.pop, "SOLAREDGE_REFRESH_TOKEN_FILE", None)
            self.session.post.return_value = self.response({
                "access_token": "access-new",
                "refresh_token": "refresh-new",
                "expires_in": 3600,
            })

            self.client._refresh_access_token()

            self.session.post.assert_called_once_with(
                TOKEN_URL,
                auth=("client-id", "client-secret"),
                json={
                    "grant_type": "refresh_token",
                    "refresh_token": "refresh-old",
                },
                timeout=30,
            )
            self.assertEqual(self.client.access_token, "access-new")
            self.assertEqual(self.client.refresh_token, "refresh-new")
            self.assertEqual(open(token_file.name).read(), "refresh-new")

    def test_energy_uses_v2_path_bearer_token_and_preserves_response(self):
        self.client.access_token = "access-token"
        self.client.access_token_expires_at = 9999999999
        self.session.get.return_value = self.response({
            "timeUnit": "DAY",
            "unit": "Wh",
            "values": [{"date": "2026-11-02 00:00:00", "value": 1234}],
        })

        result = self.client.daily_energy("2026-11-02")

        self.session.get.assert_called_once_with(
            f"{BASE_URL}/sites/12345/energy",
            params={
                "timeUnit": "DAY",
                "startDate": "2026-11-02",
                "endDate": "2026-11-02",
            },
            headers={"Authorization": "Bearer access-token"},
            timeout=30,
        )
        self.assertEqual(result["values"][0]["value"], 1234)

    def test_unwraps_energy_envelope(self):
        self.client.access_token = "access-token"
        self.client.access_token_expires_at = 9999999999
        self.session.get.return_value = self.response({
            "energy": {"unit": "Wh", "values": [{"value": 42}]}
        })
        self.assertEqual(self.client.monthly_energy("2026-11-01", "2026-11-02")["values"][0]["value"], 42)

    def test_missing_access_token_in_refresh_response_fails(self):
        self.session.post.return_value = self.response({"refresh_token": "rotated"})
        with self.assertRaisesRegex(RuntimeError, "access_token"):
            self.client._refresh_access_token()


if __name__ == "__main__":
    unittest.main()
