from api.tests.base import BaseAPITestCase
from api.tests.factories import ContactFactory
from core.admin.contact_base import MergeContacts
from core.models import Contact, Organization, ResolveConflict


class TestResolveConflictAdmin(BaseAPITestCase):
    url = "/admin/core/resolveconflict/"
    fixtures = [
        "initial/organizationtype",
        "test/organization",
        "initial/role",
        "test/user",
    ]

    def setUp(self):
        organization = Organization.objects.first()
        self.contact1 = ContactFactory(
            organization=organization,
            first_name="Jane",
            last_name="Eyre",
            emails=["janeeyre@example.com", "JaneEyre@example.com"],
        )
        self.contact2 = ContactFactory(
            organization=organization,
            first_name="Janette",
            last_name="Yre",
            emails=["janeeyre@example.com", "jannete@example.com"],
        )

    def test_create_contact_from_conflict(self):
        """
        When selected, create_contact_from_conflict action should
        create a new contact from the ResolveConflict object, then
        delete the ResolveConflict object.
        """
        self.assertEqual(Contact.objects.count(), 2)
        conflict = MergeContacts.merge_two_contacts(self.contact1, self.contact2)
        self.assertIsNotNone(conflict)
        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(ResolveConflict.objects.count(), 1)

        self.login_admin()

        response = self.client.post(
            self.url,
            data={
                "action": "create_contact_from_conflict",
                "_selected_action": [conflict.id],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Contact.objects.count(), 2)
        self.assertEqual(ResolveConflict.objects.count(), 0)
