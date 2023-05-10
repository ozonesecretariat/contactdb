import pytest
from django.urls import reverse

pytestmark = [pytest.mark.django_db]


def test_search_name(login_user_can_edit, contact, other_contact):
    client, user = login_user_can_edit
    contact.organization.save()
    contact.save()
    other_contact.organization.save()
    other_contact.save()

    url = reverse("contact-list")
    response = client.get(
        url,
        {
            "name": "Other",
        }
    )
    assert len(response.context["object_list"]) == 1
    assert response.context["object_list"][0] == other_contact


def test_search_wrong_name(login_user_can_edit, contact, other_contact):
    client, user = login_user_can_edit
    contact.organization.save()
    contact.first_name = "Gianluigi"
    contact.save()
    other_contact.organization.save()
    other_contact.save()

    url = reverse("contact-list")
    response = client.get(
        url,
        {
            "name": "Gianluigi",
        }
    )
    assert len(response.context["object_list"]) == 1
    assert response.context["object_list"][0] != other_contact


def test_search_department(login_user_can_edit, contact, other_contact):
    client, user = login_user_can_edit
    contact.organization.save()
    contact.save()
    other_contact.organization.save()
    other_contact.save()

    url = reverse("contact-list")
    response = client.get(
        url,
        {
            "department": "Agriculture",
        }
    )
    assert len(response.context["object_list"]) == 1
    assert response.context["object_list"][0] == other_contact


def test_search_designation(login_user_can_edit, contact, other_contact):
    client, user = login_user_can_edit
    contact.organization.save()
    contact.save()
    other_contact.organization.save()
    other_contact.save()

    url = reverse("contact-list")
    response = client.get(
        url,
        {
            "designation": "President",
        }
    )
    assert len(response.context["object_list"]) == 1
    assert response.context["object_list"][0] == other_contact


def test_search_email(login_user_can_edit, contact, other_contact):
    client, user = login_user_can_edit
    contact.organization.save()
    contact.save()
    other_contact.organization.save()
    other_contact.save()

    url = reverse("contact-list")
    response = client.get(
        url,
        {
            "emails": "other@test.com",
        }
    )
    assert len(response.context["object_list"]) == 1
    assert response.context["object_list"][0] == other_contact


def test_search_phone(login_user_can_edit, contact, other_contact):
    client, user = login_user_can_edit
    contact.organization.save()
    contact.save()
    other_contact.organization.save()
    other_contact.save()

    url = reverse("contact-list")
    response = client.get(
        url,
        {
            "phones_faxes": "+40987654321",
        }
    )
    assert len(response.context["object_list"]) == 1
    assert response.context["object_list"][0] == other_contact


def test_filter_mailing_list(login_user_can_edit, contact, other_contact):
    client, user = login_user_can_edit
    contact.organization.save()
    contact.save()
    other_contact.organization.save()
    other_contact.save()

    url = reverse("contact-list")
    response = client.get(
        url,
        {
            "is_in_mailing_list": True,
        }
    )
    assert len(response.context["object_list"]) == 1
    assert response.context["object_list"][0] == other_contact


def test_filter_organization_address(login_user_can_edit, contact, other_contact):
    client, user = login_user_can_edit
    contact.organization.save()
    contact.save()
    other_contact.organization.save()
    other_contact.save()

    url = reverse("contact-list")
    response = client.get(
        url,
        {
            "is_use_organization_address": True,
        }
    )
    assert len(response.context["object_list"]) == 1
    assert response.context["object_list"][0] == other_contact


def test_filter_organization(login_user_can_edit, contact, other_contact, snd_organization):
    client, user = login_user_can_edit
    contact.organization.save()
    contact.save()
    other_contact.organization = snd_organization
    other_contact.organization.save()
    other_contact.save()

    url = reverse("contact-list")
    response = client.get(
        url,
        {
            "organization": snd_organization.pk,
        }
    )
    assert len(response.context["object_list"]) == 1
    assert response.context["object_list"][0] == other_contact
