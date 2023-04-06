import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(email="john.doe@example.com", password="foo")


@pytest.fixture
def superuser():
    return User.objects.create_superuser(email="super@example.com", password="foo")
