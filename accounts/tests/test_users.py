import pytest

from django.contrib.auth import get_user_model


pytestmark = [pytest.mark.django_db]


def test_create_user():
    User = get_user_model()  # noqa
    user = User.objects.create_user(email="normal@user.com", password="foo")
    assert user.email == "normal@user.com"
    assert user.is_active
    assert not user.is_staff
    assert not user.is_superuser

    with pytest.raises(AttributeError):
        assert user.username is None

    with pytest.raises(TypeError):
        User.objects.create_user()

    with pytest.raises(TypeError):
        User.objects.create_user(email="")

    with pytest.raises(TypeError):
        User.objects.create_user(email="normal@user.com")

    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="foo")

    with pytest.raises(ValueError):
        User.objects.create_user(email="normal@user.com", password="")


def test_create_superuser():
    User = get_user_model()  # noqa
    user = User.objects.create_superuser(email="super@user.com", password="foo")
    assert user.email == "super@user.com"
    assert user.is_active
    assert user.is_staff
    assert user.is_superuser
