from datetime import datetime
import urllib

import pytest
from django.urls import reverse

from core.models import Record

pytestmark = [pytest.mark.django_db]


def test_edit_record_no_perm(login_user_no_perm, contact, snd_organization):
    client, user = login_user_no_perm()
    contact.organization.save()
    contact.save()

    data = {
        "contact_id": "5959ec2af439c413049fc55e",
        "organization": str(snd_organization.pk),
        "title": "Mr.",
        "first_name": "Alex",
        "last_name": "Alexandrovici",
        "designation": "Director",
        "department": "Department",
        "affiliation": "",
        "phones": "+37467818532",
        "mobiles": "+37499552026",
        "faxes": "",
        "emails": "alex.alexandrovici@gmail.com",
        "email_ccs": "",
        "notes": "Picture #324200106\r\n##E\r\n##R",
        "is_in_mailing_list": False,
        "is_use_organization_address": True,
        "address": "",
        "city": "Brasov",
        "state": "",
        "country": "ro",
        "postal_code": "6675",
        "birth_date": "1995-10-20",
    }

    url = reverse("contact-update", kwargs={"pk": contact.pk})
    response = client.post(
        url,
        urllib.parse.urlencode(data),
        content_type="application/x-www-form-urlencoded",
        follow=True,
    )
    assert response.status_code == 403


def test_edit_record_can_edit(login_user_can_edit, contact, snd_organization):
    client, user = login_user_can_edit
    assert user.can_edit is True
    contact.organization.save()
    contact.save()
    snd_organization.save()

    data = {
        "contact_id": "5959ec2af439c413049fc55e",
        "organization": str(snd_organization.pk),
        "title": "Mr.",
        "first_name": "Alex",
        "last_name": "Alexandrovici",
        "designation": "Director",
        "department": "Department",
        "affiliation": "",
        "phones": "+37467818532",
        "mobiles": "+37499552026",
        "faxes": "",
        "emails": "alex.alexandrovici@gmail.com",
        "email_ccs": "",
        "notes": "Picture #324200106\r\n##E\r\n##R",
        "is_in_mailing_list": False,
        "is_use_organization_address": True,
        "address": "",
        "city": "Brasov",
        "state": "",
        "country": "ro",
        "postal_code": "6675",
        "birth_date": "1995-10-20",
    }

    url = reverse("contact-update", kwargs={"pk": contact.pk})
    response = client.post(
        url,
        urllib.parse.urlencode(data),
        content_type="application/x-www-form-urlencoded",
        follow=True,
    )

    assert response.status_code == 200

    contact.refresh_from_db()

    assert contact.contact_id == data["contact_id"]
    assert contact.organization.pk == int(data["organization"])
    assert contact.title == data["title"]
    assert contact.first_name == data["first_name"]
    assert contact.last_name == data["last_name"]
    assert contact.designation == data["designation"]
    assert contact.department == data["department"]
    assert contact.affiliation == data["affiliation"]
    assert contact.phones[0] == data["phones"].split(",")[0]
    assert contact.mobiles[0] == data["mobiles"].split(",")[0]
    assert len(contact.faxes) == 0
    assert contact.emails[0] == data["emails"].split(",")[0]
    assert len(contact.email_ccs) == 0
    assert contact.notes == data["notes"]
    assert contact.is_use_organization_address == data["is_use_organization_address"]
    assert contact.is_in_mailing_list == data["is_in_mailing_list"]
    assert contact.address == data["address"]
    assert contact.city == data["city"]
    assert contact.state == data["state"]
    assert contact.country == data["country"]
    assert contact.postal_code == data["postal_code"]
    assert (
        contact.birth_date == datetime.strptime(data["birth_date"], "%Y-%m-%d").date()
    )


def test_delete_record_no_perms(login_user_no_perm, contact):
    client, user = login_user_no_perm()
    contact.organization.save()
    contact.save()
    data = {}
    found_contact = Record.objects.filter(pk=contact.pk).first()
    assert found_contact == contact
    url = reverse("contact-delete", kwargs={"pk": contact.pk})
    response = client.post(
        url,
        urllib.parse.urlencode(data),
        content_type="application/x-www-form-urlencoded",
        follow=True,
    )
    assert response.status_code == 403
    found_contact = Record.objects.filter(pk=contact.pk).first()
    assert found_contact == contact


def test_delete_record_can_edit(login_user_can_edit, contact):
    client, user = login_user_can_edit
    assert user.can_edit is True
    contact.organization.save()
    contact.save()

    data = {}

    found_contact = Record.objects.filter(pk=contact.pk).first()
    assert found_contact == contact

    url = reverse("contact-delete", kwargs={"pk": contact.pk})
    response = client.post(
        url,
        urllib.parse.urlencode(data),
        content_type="application/x-www-form-urlencoded",
        follow=True,
    )

    assert response.status_code == 200

    found_contact = Record.objects.filter(pk=contact.pk).first()
    assert found_contact is None
