import pytest

from core.models import Record, Organization


@pytest.fixture
def test_password():
    return "parolA12!"


@pytest.fixture
def create_user(db, django_user_model, test_password):
    def make_user(**kwargs):
        kwargs["password"] = test_password
        if "email" not in kwargs:
            kwargs["email"] = "user@example.com"
        return django_user_model.objects.create_user(**kwargs)

    return make_user


@pytest.fixture
def login_user_no_perm(db, client, create_user, test_password):
    def make_auto_login():
        user = create_user()
        client.login(username=user.get_username(), password=test_password)
        return client, user

    return make_auto_login


@pytest.fixture
def login_user_can_edit(db, client, create_user, test_password):
    user = create_user(can_edit=True)
    client.login(username=user.get_username(), password=test_password)
    return client, user


@pytest.fixture
def first_organization(db):
    return Organization(
        organization_id="3baa33cc079ab1d4ff5e27be727613ef",
        name="Organization 1",
        organization_type_id="e6a17cabcbdd10e53f24e8bab0221af2",
        organization_type="BIZ",
    )


@pytest.fixture
def snd_organization(db):
    return Organization(
        organization_id="4baa53cc079ab1d4ff5e27be727613ef",
        name="Organization 2",
        organization_type_id="e6a17cabcbdd10e53f24e8bab0221af2",
        organization_type="BIZ",
    )


@pytest.fixture
def contact(db, first_organization):
    return Record(
        organization=first_organization,
        contact_id="500d0202abb6fba28c50d61fa4979a28",
        phones=[],
        mobiles=[],
        faxes=[],
        emails=[],
        email_ccs=[],
        is_in_mailing_list=False,
        is_use_organization_address=False,
    )


@pytest.fixture
def other_contact(db, first_organization):
    return Record(
        first_name="Other",
        last_name="Record",
        department="Minister of Agriculture",
        designation="President",
        organization=first_organization,
        contact_id="59f9be9bb0590106f4b4e3b2",
        phones=["+40987654321"],
        mobiles=[],
        faxes=[],
        emails=["other@test.com"],
        email_ccs=[],
        is_in_mailing_list=True,
        is_use_organization_address=True,
    )
