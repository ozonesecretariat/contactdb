from django.test import TestCase
from accounts.models import User


class TestUsers(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(email="normal@user.com", password="foo")
        self.assertEqual(user.email, "normal@user.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_superuser)
        self.assertIsNone(getattr(user, "username", None))

        with self.assertRaises(TypeError):
            User.objects.create_user()

        with self.assertRaises(TypeError):
            User.objects.create_user(email="")

        with self.assertRaises(TypeError):
            User.objects.create_user(email="normal@user.com")

        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="foo")

        with self.assertRaises(ValueError):
            User.objects.create_user(email="normal@user.com", password="")

    def test_create_superuser(self):
        user = User.objects.create_superuser(email="super@user.com", password="foo")
        self.assertEqual(user.email, "super@user.com")
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
