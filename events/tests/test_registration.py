from django.contrib.admin.sites import AdminSite
from django.core import mail
from django.test.testcases import TestCase
from django.test.utils import override_settings

from api.tests.factories import (
    ContactFactory,
    EventFactory,
    RegistrationFactory,
)
from emails.models import Email
from events.admin import RegistrationInline
from events.jobs import send_priority_pass_status_emails
from events.models import Registration


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class TestRegistrationStatus(TestCase):
    def setUp(self):
        self.event = EventFactory(
            confirmation_subject="Confirm [[full_name]]",
            confirmation_content="Yes [[full_name]]",
            refuse_subject="Refuse [[full_name]]",
            refuse_content="No [[full_name]]",
        )
        self.contact = ContactFactory()
        self.registration = RegistrationFactory(event=self.event, contact=self.contact)

    def test_change_to_accredited(self):
        mail.outbox = []
        self.registration.status = Registration.Status.ACCREDITED
        self.registration.save()

        send_priority_pass_status_emails(self.registration.priority_pass.id)

        email = Email.objects.get()
        task = email.email_logs.get()
        task.run(is_async=False)

        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]

        self.assertTrue(f"Confirm {self.contact.full_name}" in msg.subject)
        self.assertTrue(msg.body_contains(f"Yes {self.contact.full_name}"))

    def test_change_to_revoked(self):
        mail.outbox = []
        self.registration.status = Registration.Status.REVOKED
        self.registration.save()

        send_priority_pass_status_emails(self.registration.priority_pass.id)

        email = Email.objects.get()
        task = email.email_logs.get()
        task.run(is_async=False)

        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]

        self.assertTrue(f"Refuse {self.contact.full_name}" in msg.subject)
        self.assertTrue(msg.body_contains(f"No {self.contact.full_name}"))

    def test_placeholder_registration_deletable(self):
        """Test that only placeholder registrations can be deleted via admin."""

        hidden_event = EventFactory(hide_for_nomination=True)
        placeholder_registration = RegistrationFactory(
            contact=self.contact,
            event=hidden_event,
            status="",
        )

        admin_site = AdminSite()
        inline = RegistrationInline(Registration, admin_site)

        self.assertTrue(inline.has_delete_permission(None, placeholder_registration))

        self.assertFalse(inline.has_delete_permission(None, self.registration))
