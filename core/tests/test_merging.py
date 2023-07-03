import pytest
from django.urls import reverse

pytestmark = [pytest.mark.django_db]


def test_first_step(login_user_can_edit, contact, other_contact, first_organization):
    client, user = login_user_can_edit
    first_organization.save()
    contact.save()
    other_contact.save()

    response = client.post(
        reverse("merge-first-step"),
        {"contacts": [contact.id, other_contact.id]},
        follow=False,
    )

    assert response.status_code == 302


def test_second_step(login_user_can_edit, contact, other_contact, first_organization):
    client, user = login_user_can_edit
    first_organization.save()
    contact.save()
    other_contact.save()

    response = client.post(
        reverse("merge-second-step") + f"?ids={contact.id},{other_contact.id}",
        {"contact": contact.id},
        follow=False,
    )

    assert response.status_code == 302

    other_contact.refresh_from_db()
    contact.refresh_from_db()
    assert other_contact.is_secondary
    assert other_contact.main_contact == contact
    assert contact.record_set.count() == 1
    assert contact.record_set.first() == other_contact
