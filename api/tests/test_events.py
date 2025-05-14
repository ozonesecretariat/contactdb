from api.tests.base import BaseAPITestCase


class TestEventsAPI(BaseAPITestCase):
    fixtures = [*BaseAPITestCase.fixtures, "initial/country", "test/event"]

    def test_get_events_admin(self):
        self.login_admin()
        response = self.client.get("/api/events/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 20)

    def test_get_events_email_user(self):
        self.login_emails_user()
        response = self.client.get("/api/events/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 20)

    def test_get_events_no_access(self):
        self.login_no_access_user()
        response = self.client.get("/api/events/")
        self.assertEqual(response.status_code, 403)
