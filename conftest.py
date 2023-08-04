import os
from datetime import datetime

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.timezone import make_aware

from core.models import (
    Record,
    Organization,
    Group,
    KronosEvent,
    TemporaryContact,
    Emails,
    EmailTag,
    EmailFile,
)


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
    user = create_user()
    client.login(username=user.get_username(), password=test_password)
    return client, user


@pytest.fixture
def login_user_can_edit(db, client, create_user, test_password):
    user = create_user(can_edit=True)
    client.login(username=user.get_username(), password=test_password)
    return client, user


@pytest.fixture
def login_user_can_import(db, client, create_user, test_password):
    user = create_user(can_import=True)
    client.login(username=user.get_username(), password=test_password)
    return client, user


@pytest.fixture
def login_user_can_send_mail(db, client, create_user, test_password):
    user = create_user(can_send_mail=True)
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
        emails=["contact@test.com"],
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


@pytest.fixture
def third_contact(db, snd_organization):
    return Record(
        first_name="Third",
        last_name="Record",
        department="Department",
        designation="Designation",
        organization=snd_organization,
        contact_id="89f9be1bb0590106f4b4e334",
        phones=["+50987666328"],
        mobiles=[],
        faxes=[],
        emails=["third@test.com"],
        email_ccs=[],
        is_in_mailing_list=True,
        is_use_organization_address=True,
    )


@pytest.fixture
def group(db):
    return Group(name="Group1", description="This is a test description")


@pytest.fixture
def other_group(db):
    return Group(name="Group2", description="This is a test description2")


@pytest.fixture
def kronos_event(db):
    return KronosEvent(
        event_id="520345543cbd0495c00001879",
        code="005639",
        title="Event title",
        start_date=make_aware(
            datetime.strptime("2017-11-18T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
        ),
        end_date=make_aware(
            datetime.strptime("2017-11-18T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
        ),
        venue_country="ca",
        venue_city="Montreal",
        dates="13 November 2010",
    )


@pytest.fixture
def temporary_contact(first_organization, other_contact):
    return TemporaryContact(
        record=other_contact,
        first_name=other_contact.first_name,
        last_name=other_contact.last_name,
        department="Minister of Defence",
        designation="Secretary",
        organization=first_organization,
        contact_id="59f9be9bb0590106f4b4e3b2",
        phones=["+40987654321"],
        mobiles=["+409876324567"],
        faxes=[],
        emails=other_contact.emails,
        email_ccs=["email@test.com"],
        is_in_mailing_list=True,
        is_use_organization_address=True,
    )


@pytest.fixture
def snd_temporary_contact(db, snd_organization, third_contact):
    return TemporaryContact(
        record=third_contact,
        first_name=third_contact.first_name,
        last_name=third_contact.last_name,
        department="New Department",
        designation="New Designation",
        organization=snd_organization,
        contact_id="89f9be1bb0590106f4b4e334",
        phones=["+50987666328"],
        mobiles=[],
        faxes=[],
        emails=third_contact.emails,
        email_ccs=["email2@test.com"],
        is_in_mailing_list=True,
        is_use_organization_address=True,
    )


@pytest.fixture
def email(db):
    return Emails(
        subject="Email subject",
        content="<h1>Email content</h1><p>Test </p>",
    )


@pytest.fixture
def email_tag_first_name(db):
    return EmailTag(name="First name", field_name="first_name")


@pytest.fixture
def email_file(db, email):
    email.save()
    email_file = EmailFile.objects.create(
        name="email_file.txt",
        email=email,
        file=SimpleUploadedFile("email_file.txt", b"these are the file contents!"),
    )

    yield email_file

    os.remove(email_file.path)
