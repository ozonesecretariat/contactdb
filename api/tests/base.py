from rest_framework.test import APITestCase


class BaseAPITestCase(APITestCase):
    fixtures = ["initial/role", "test/user"]

    def login_admin(self):
        self.client.login(email="admin@example.com", password="admin")

    def login_edit_user(self):
        self.client.login(email="test-edit@example.com", password="test")

    def login_emails_user(self):
        self.client.login(email="test-emails@example.com", password="test")

    def login_kronos_user(self):
        self.client.login(email="test-kronos@example.com", password="test")

    def login_no_access_user(self):
        self.client.login(email="test-no-access@example.com", password="test")

    def login_view_user(self):
        self.client.login(email="test-view@example.com", password="test")

    def login_non_staff_user(self):
        self.client.login(email="test-non-staff@example.com", password="test")

    def login_non_staff_view_user(self):
        self.client.login(email="test-non-staff-view@example.com", password="test")

    def login_non_staff_no_access_user(self):
        self.client.login(email="test-non-staff-no-access@example.com", password="test")

    def login_security(self):
        self.client.login(email="test-security@example.com", password="test")

    def login_support(self):
        self.client.login(email="test-support@example.com", password="test")

    def login_dsa(self):
        self.client.login(email="test-dsa@example.com", password="test")
