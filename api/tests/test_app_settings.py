from api.tests.base import BaseAPITestCase


class TestAppSettingsAPI(BaseAPITestCase):
    url = "/api/app-settings/"

    def test_get_app_settings_anon(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["require2fa"], False)

    def test_get_app_settings_admin(self):
        self.login_admin()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["require2fa"], False)

    def test_get_app_settings_user(self):
        self.login_view_user()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["require2fa"], False)
