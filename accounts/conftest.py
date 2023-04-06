import pytest

from digital_agenda.apps.accounts.models import User


@pytest.fixture
def user():
    return User.objects.create_user(email="john.doe@example.com", password="foo")


@pytest.fixture
def superuser():
    return User.objects.create_superuser(email="super@example.com", password="foo")
