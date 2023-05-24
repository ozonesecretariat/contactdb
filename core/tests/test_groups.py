import pytest
from django.urls import reverse

from core.models import Group

pytestmark = [pytest.mark.django_db]


def test_group_list_search(login_user_can_edit, group, other_group):
    client, user = login_user_can_edit
    group.save()
    other_group.save()

    url = reverse("group-list")
    response = client.get(
        url,
        {
            "name": "Group1",
        },
    )
    assert len(response.context["object_list"]) == 1
    assert response.context["object_list"][0] == group


def test_create_group_no_perm(login_user_no_perm):
    client, user = login_user_no_perm
    url = reverse("group-create")
    response = client.post(
        url, {"name": "New group", "description": "Description"}, follow=True
    )

    assert response.status_code == 403


def test_create_group_can_edit(login_user_can_edit):
    client, user = login_user_can_edit
    url = reverse("group-create")
    response = client.post(
        url, {"name": "New group", "description": "Description"}, follow=True
    )

    assert response.status_code == 200
    created_group = Group.objects.filter(
        name="New group", description="Description"
    ).all()
    assert len(created_group) == 1


def test_update_group_no_perm(login_user_no_perm, group):
    client, user = login_user_no_perm
    group.save()
    name_before = group.name
    description_before = group.description

    url = reverse("group-update", kwargs={"pk": group.pk})
    response = client.post(
        url,
        {"name": "Updated name", "description": "Updated description", "contacts": []},
        follow=True,
    )

    assert response.status_code == 403
    group.refresh_from_db()
    assert group.name == name_before
    assert group.description == description_before


def test_update_group_can_edit(
    login_user_can_edit, group, contact, other_contact, first_organization
):
    client, user = login_user_can_edit
    first_organization.save()
    contact.save()
    other_contact.save()
    group.save()

    group.contacts.set([contact, other_contact])

    url = reverse("group-update", kwargs={"pk": group.pk})
    response = client.post(
        url,
        {
            "name": "Updated name",
            "description": "Updated description",
            "contacts": [contact.pk],
        },
        follow=True,
    )

    assert response.status_code == 200
    group.refresh_from_db()
    assert group.name == "Updated name"
    assert group.description == "Updated description"
    assert len(group.contacts.all()) == 1
    assert group.contacts.all()[0].pk == contact.pk


def test_delete_group_no_perm(login_user_no_perm, group):
    client, user = login_user_no_perm
    group.save()

    url = reverse("group-delete", kwargs={"pk": group.pk})

    response = client.post(url, follow=True)

    assert response.status_code == 403
    assert len(Group.objects.filter(id=group.pk).all()) == 1


def test_delete_group_can_edit(login_user_can_edit, group):
    client, user = login_user_can_edit
    group.save()

    url = reverse("group-delete", kwargs={"pk": group.pk})

    response = client.post(url, follow=True)

    assert response.status_code == 200
    assert len(Group.objects.filter(id=group.pk).all()) == 0


def test_add_multiple_members_no_perms(
    login_user_no_perm, group, other_group, contact, other_contact, first_organization
):
    client, user = login_user_no_perm

    first_organization.save()
    group.save()
    other_group.save()
    contact.save()
    other_contact.save()

    url = reverse("groups-add-multiple-members")

    response = client.post(
        url,
        {
            "members": [contact.pk, other_contact.pk],
            "groups": [group.pk, other_group.pk],
        },
        follow=True,
    )

    assert response.status_code == 403

    assert len(Group.objects.filter(contacts__in=[contact.pk]).all()) == 0
    assert len(Group.objects.filter(contacts__in=[other_contact.pk]).all()) == 0


def test_add_multiple_members_can_edit(
    login_user_can_edit, group, other_group, contact, other_contact, first_organization
):
    client, user = login_user_can_edit

    first_organization.save()
    group.save()
    other_group.save()
    contact.save()
    other_contact.save()

    url = reverse("groups-add-multiple-members")

    response = client.post(
        url,
        {
            "members": [contact.pk, other_contact.pk],
            "groups": [group.pk, other_group.pk],
        },
        follow=True,
    )

    assert response.status_code == 200
    assert len(Group.objects.filter(contacts__in=[contact.pk]).all()) == 2
    assert len(Group.objects.filter(contacts__in=[other_contact.pk]).all()) == 2
