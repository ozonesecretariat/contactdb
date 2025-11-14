from api.tests.base import BaseAPITestCase


class TestPriorityPassAPI(BaseAPITestCase):
    url = "/api/priority-passes/"
    fixtures = [
        *BaseAPITestCase.fixtures,
        "initial/region",
        "initial/subregion",
        "initial/country",
        "initial/organizationtype",
        "initial/contactgroup",
        "initial/registrationtag",
        "initial/registrationrole",
        "test/contactgroup",
        "test/eventgroup",
        "test/event",
        "test/organization",
        "test/contact",
        "test/prioritypass",
        "test/registration",
    ]

    def check_permissions(self, url, check_func):
        for login_method, valid in (
            (self.login_admin, True),
            (self.login_security, True),
            (self.login_support, True),
            (self.login_dsa, False),
        ):
            with self.subTest(login_method=login_method.__name__):
                login_method()
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200 if valid else 403)
                if valid:
                    check_func(response)

    def test_list_passes(self):
        for login_method, valid in (
            (self.login_admin, True),
            (self.login_security, True),
            (self.login_support, True),
            (self.login_dsa, False),
        ):
            with self.subTest(login_method=login_method.__name__):
                login_method()
                resp = self.client.get(self.url)
                self.assertEqual(resp.status_code, 200 if valid else 403)
                if valid:
                    self.assertEqual(len(resp.json()), 519)

    def test_get_pass_by_code(self):
        for login_method, valid in (
            (self.login_admin, True),
            (self.login_security, True),
            (self.login_support, True),
            (self.login_dsa, False),
        ):
            with self.subTest(login_method=login_method.__name__):
                login_method()
                resp = self.client.get(self.url + "QGRCE9XD0W/")
                self.assertEqual(resp.status_code, 200 if valid else 403)
                if valid:
                    self.assertEqual(
                        resp.json()["contact"]["fullName"], "Luna-Infinity Hyperion"
                    )

    def test_print_pdf(self):
        for login_method, valid in (
            (self.login_admin, True),
            # Security cannot print badges even though they can list and view passes
            (self.login_security, False),
            (self.login_support, True),
            (self.login_dsa, False),
        ):
            with self.subTest(login_method=login_method.__name__):
                login_method()
                resp = self.client.get(self.url + "QGRCE9XD0W/print_badge/")
                self.assertEqual(resp.status_code, 200 if valid else 403)
                if valid:
                    self.assertTrue(next(resp.streaming_content).startswith(b"%PDF"))
