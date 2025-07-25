import json

import requests
from django.conf import settings

ACCOUNTS_HOST = settings.ACCOUNTS_HOST
KRONOS_HOST = settings.KRONOS_HOST
KRONOS_USERNAME = settings.KRONOS_USERNAME
KRONOS_PASSWORD = settings.KRONOS_PASSWORD


class KronosClient:
    # TODO: at least part of this should be moved to core or common!
    def __init__(self):
        self.auth_token = None
        self.auth_token = self._login()

    def send_kronos(
        self, path, params=None, json_data=None, method="GET", host=KRONOS_HOST
    ):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.auth_token:
            headers["Authorization"] = f"Token {self.auth_token}"

        resp = requests.request(
            method=method,
            url=f"https://{host}{path}",
            headers=headers,
            json=json_data or {},
            params=params or {},
            timeout=60,
        )

        resp.raise_for_status()
        return resp.json()

    def _login(self):
        data = self.send_kronos(
            path="/api/v2013/authentication/token",
            host=ACCOUNTS_HOST,
            json_data={
                "email": f"{KRONOS_USERNAME}",
                "password": f"{KRONOS_PASSWORD}",
            },
            method="POST",
        )

        self.auth_token = data.get("authenticationToken")
        return self.auth_token

    def get_meetings(self):
        return self.send_kronos(path="/api/v2018/events")["records"]

    def get_participants(self, event_id: str):
        qparams = {
            "eventIds": [event_id],
            "registrationStatusForEventIds": [event_id],
        }
        return self.send_kronos(
            path="/api/v2018/contacts",
            params={
                "q": json.dumps(qparams),
            },
        )["records"]

    def get_org_types(self):
        return self.send_kronos("/api/v2018/organizations/types")

    def get_countries(self):
        return self.send_kronos("/api/v2018/countries")

    def get_organizations_for_event(self, event_id: str):
        limit = 1000
        total_count: int | None = None
        results = []
        post_data = {"eventIds": [event_id], "limit": limit, "skip": 0}

        while total_count is None or len(results) < total_count:
            page_result = self.send_kronos(
                "/api/v2018/organizations/query",
                json_data=post_data,
                method="POST",
            )
            total_count = page_result["totalRecordCount"]
            results.extend(page_result["records"])
            post_data["skip"] += limit

        return results

    def get_all_organizations(self):
        limit = 1000
        total_count: int | None = None
        results = []

        org_types = [
            org_type["organizationTypeId"] for org_type in self.get_org_types()
        ]
        post_data = {
            "organizationTypeIds": org_types,
            "limit": limit,
            "skip": 0,
        }

        while total_count is None or len(results) < total_count:
            page_result = self.send_kronos(
                "/api/v2018/organizations/query",
                json_data=post_data,
                method="POST",
            )
            total_count = page_result["totalRecordCount"]
            results.extend(page_result["records"])
            post_data["skip"] += limit
        return results

    def get_contact_photo(self, contact_kronos_id: str):
        """Get photo for a single specific contact Kronos id."""
        try:
            # TODO: check what response is received when contacts do not have photos.
            return self.send_kronos(f"/api/v2018/contacts/{contact_kronos_id}/photo")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def get_contact_data(self, contact_kronos_id: str):
        """Get Kronos data for a specific contact."""
        try:
            return self.send_kronos(f"/api/v2018/contacts/{contact_kronos_id}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def get_registrations_data(self, contact_kronos_ids: str):
        """Get Kronos data for contact registrations."""
        try:
            qparams = {
                "contactIds": [contact_kronos_ids],
            }
            return self.send_kronos(
                path="/api/v2018/event-participants",
                params={
                    "q": json.dumps(qparams),
                },
            ).get("records", [])
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
