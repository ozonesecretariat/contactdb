import json

from django.conf import settings
import requests

ACCOUNTS_HOST = settings.ACCOUNTS_HOST
KRONOS_HOST = settings.KRONOS_HOST
KRONOS_USERNAME = settings.KRONOS_USERNAME
KRONOS_PASSWORD = settings.KRONOS_PASSWORD


class Client:
    auth_token = None

    def _send_kronos(
        self, path, params=None, json_data=None, method=requests.get, host=KRONOS_HOST
    ):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.auth_token:
            headers["Authorization"] = f"Token {self.auth_token}"
        resp = method(
            url=f"https://{host}{path}",
            headers=headers,
            json=json_data or {},
            params=params or {},
        )

        resp.raise_for_status()
        return resp.json()

    def login(self):
        data = self._send_kronos(
            path="/api/v2013/authentication/token",
            host=ACCOUNTS_HOST,
            json_data={
                "email": f"{KRONOS_USERNAME}",
                "password": f"{KRONOS_PASSWORD}",
            },
            method=requests.post,
        )
        self.auth_token = data.get("authenticationToken")
        return self.auth_token

    def get_meetings(self):
        return self._send_kronos(path="/api/v2018/events")

    def get_participants(self, event_ids):
        qparams = {
            "eventIds": [f"{event_id}" for event_id in event_ids],
            "registrationStatusForEventIds": [f"{event_id}" for event_id in event_ids],
        }
        return self._send_kronos(
            path="/api/v2018/contacts",
            params={
                "q": json.dumps(qparams),
            },
        )
