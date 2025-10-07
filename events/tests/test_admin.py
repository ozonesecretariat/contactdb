import unicodedata
from datetime import UTC, datetime, timedelta
from io import BytesIO
from unittest.mock import Mock

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms.models import inlineformset_factory
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from pdfminer.high_level import extract_text

from api.tests.factories import (
    ContactFactory,
    EventFactory,
    EventGroupFactory,
    EventInvitationFactory,
    OrganizationFactory,
    PriorityPassFactory,
    RegistrationFactory,
    RegistrationRoleFactory,
)
from core.models import Country, OrganizationType
from emails.models import SendEmailTask
from emails.tests.factories import InvitationEmailFactory
from events.admin import (
    EventInvitationAdmin,
    FutureEventFilter,
    HasUnregisteredFilter,
    PriorityPassAdmin,
    RegistrationAdmin,
    RegistrationInline,
    RegistrationInlineFormSet,
)
from events.models import EventInvitation, PriorityPass, Registration


class TestEventInvitationAdmin(TestCase):
    fixtures = [
        "initial/region",
        "initial/subregion",
        "initial/country",
        "initial/organizationtype",
        "initial/registrationrole",
    ]

    def setUp(self):
        self.site = AdminSite()
        self.admin = EventInvitationAdmin(EventInvitation, self.site)
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_superuser(
            email="admin@example.com", password="password"
        )

        now = timezone.now()
        self.future_date = now + timedelta(days=365)
        self.past_date = now - timedelta(days=365)

        self.gov_type = OrganizationType.objects.get(acronym="GOV")
        self.org_type = OrganizationType.objects.exclude(acronym="GOV").first()
        self.country = Country.objects.first()
        self.event = EventFactory(
            title="Test Event",
            start_date=self.future_date,
            end_date=self.future_date + timedelta(days=3),
            venue_country=self.country,
        )
        self.event_group = EventGroupFactory(name="Test Group")
        self.event_group.events.add(self.event)

        self.organization = OrganizationFactory(
            name="Test Org",
            organization_type=self.org_type,
            emails=["org@example.com"],
            government=None,
        )
        self.gov_org = OrganizationFactory(
            name="Gov Org",
            organization_type=self.gov_type,
            emails=["gov@example.com"],
            government=self.country,
        )

        self.contact = ContactFactory(
            organization=self.organization,
            emails=["contact@example.com"],
        )
        self.gov_contact = ContactFactory(
            organization=self.gov_org,
            emails=["gov-contact@example.com"],
        )

        self.invitation = EventInvitationFactory(
            event=self.event,
            event_group=None,
            organization=self.organization,
            country=None,
        )
        self.gov_invitation = EventInvitationFactory(
            event=self.event,
            event_group=None,
            organization=None,
            country=self.country,
        )

        self.email = InvitationEmailFactory(
            subject="Test Email",
            content="Test content",
        )

    def test_unregistered_organizations_display(self):
        """Test the unregistered_organizations_display method."""
        # Test using invitation that has no registrations (non-GOV org)
        html = self.admin.unregistered_organizations_display(self.invitation)
        self.assertIn(self.organization.name, html)
        self.assertIn(
            reverse("admin:core_organization_change", args=[self.organization.id]), html
        )

        # Add registration to make org "invited"; test that display changes
        RegistrationFactory(
            contact=self.contact,
            event=self.event,
        )
        html = self.admin.unregistered_organizations_display(self.invitation)
        self.assertIn("All organizations have registered", html)
        self.assertNotIn("Send Reminder Email to All", html)

        # Now test GOV invitation with no registrations
        html = self.admin.unregistered_organizations_display(self.gov_invitation)
        self.assertIn(self.gov_org.name, html)

        # Add registration for GOV org & re-test
        RegistrationFactory(
            contact=self.gov_contact,
            event=self.event,
        )
        html = self.admin.unregistered_organizations_display(self.gov_invitation)
        self.assertIn("All organizations have registered", html)

    def test_event_or_group_display(self):
        """Test the event_or_group display method."""
        self.assertEqual(self.admin.event_or_group(self.invitation), self.event)

        # Test using event group
        group_invitation = EventInvitationFactory(
            event=None,
            event_group=self.event_group,
            organization=self.organization,
        )
        self.assertEqual(self.admin.event_or_group(group_invitation), self.event_group)

    def test_invitation_link_display(self):
        """Test the invitation_link display method."""
        html = self.admin.invitation_link(self.invitation)
        self.assertIn(str(self.invitation.token), html)
        self.assertIn("View Invitation Link", html)

    def test_is_for_future_event_display(self):
        """Test the is_for_future_event_display method."""
        # Future event should return True
        self.assertTrue(self.admin.is_for_future_event_display(self.invitation))

        # Past event should return False
        past_event = EventFactory(
            title="Past Event",
            start_date=datetime(2020, 1, 1, tzinfo=UTC),
            end_date=datetime(2020, 1, 2, tzinfo=UTC),
        )
        past_invitation = EventInvitationFactory(
            event=past_event,
            organization=self.organization,
        )
        self.assertFalse(self.admin.is_for_future_event_display(past_invitation))

    def test_email_tasks_display(self):
        """Test the email_tasks_display method."""
        # Without any tasks
        self.assertEqual(self.admin.email_tasks_display(self.invitation), "-")

        # With tasks
        SendEmailTask.objects.create(
            invitation=self.invitation,
            organization=self.organization,
            email=self.email,
        )
        html = self.admin.email_tasks_display(self.invitation)
        self.assertIn("1 tasks", html)
        self.assertIn(f"invitation__id__exact={self.invitation.id}", html)

    def test_has_unregistered_filter(self):
        """Testing HasUnregisteredFilter."""
        request = self.factory.get("/fake-url/")
        list_filter = HasUnregisteredFilter(
            request, params={}, model=EventInvitation, model_admin=self.admin
        )
        list_filter.used_parameters = {list_filter.parameter_name: "yes"}

        # Test with "yes" value (has unregistered)
        queryset = EventInvitation.objects.all()
        filtered = list_filter.queryset(request, queryset)
        self.assertEqual(filtered.count(), 2)

        # Add registration for one invitation
        RegistrationFactory(
            contact=self.contact,
            event=self.event,
        )

        # Test that filter now excludes the invitation with registration
        filtered = list_filter.queryset(request, queryset)
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), self.gov_invitation)

        # Test with "no" value (all registered)
        no_filter = HasUnregisteredFilter(
            request, params={}, model=EventInvitation, model_admin=self.admin
        )
        no_filter.used_parameters = {no_filter.parameter_name: "no"}
        filtered = no_filter.queryset(request, queryset)
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), self.invitation)

        # Add registration for the other invitation
        RegistrationFactory(
            contact=self.gov_contact,
            event=self.event,
        )

        # Filter for "yes" should now return empty
        filtered = list_filter.queryset(request, queryset)
        self.assertEqual(filtered.count(), 0)

        # Filter for "no" should return both
        filtered = no_filter.queryset(request, queryset)
        self.assertEqual(filtered.count(), 2)

    def test_future_event_filter(self):
        """Test the FutureEventFilter."""
        # Create filter instance for future events
        request = self.factory.get("/fake-url/")
        future_params = {FutureEventFilter.parameter_name: "future"}

        for invitation in [self.invitation, self.gov_invitation]:
            self.assertTrue(invitation.is_for_future_event)

        future_filter = FutureEventFilter(
            request, future_params, model=EventInvitation, model_admin=self.admin
        )

        # Test with "future" value
        queryset = EventInvitation.objects.all()
        filtered = future_filter.queryset(request, queryset)
        self.assertEqual(filtered.count(), 2)

        # Add a past event and invitation
        past_event = EventFactory(
            title="Past Event",
            start_date=self.past_date,
            end_date=self.past_date + timedelta(days=3),
        )
        past_invitation = EventInvitationFactory(
            event=past_event,
            organization=self.organization,
            country=None,
        )
        self.assertFalse(past_invitation.is_for_future_event)

        queryset = EventInvitation.objects.all()
        self.assertEqual(queryset.count(), 3)

        # Past invitation should be excluded from "future" query
        future_filter = FutureEventFilter(
            request, params={}, model=EventInvitation, model_admin=self.admin
        )
        future_filter.used_parameters = {future_filter.parameter_name: "future"}
        filtered = future_filter.queryset(request, queryset)
        self.assertEqual(filtered.count(), 2)
        self.assertNotIn(past_invitation, filtered)

        # Filter should only include past invitation for "past" query
        past_filter = FutureEventFilter(
            request, params={}, model=EventInvitation, model_admin=self.admin
        )
        past_filter.used_parameters = {past_filter.parameter_name: "past"}
        filtered = past_filter.queryset(request, queryset)
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), past_invitation)


class TestPriorityPassAdmin(TestCase):
    fixtures = ["initial/role", "test/user"]

    def setUp(self):
        self.site = AdminSite()
        self.admin = PriorityPassAdmin(PriorityPass, self.site)

        self.group = EventGroupFactory()
        self.event1 = EventFactory(group=self.group)
        self.event2 = EventFactory(group=self.group)
        self.contact = ContactFactory()
        self.priority_pass = PriorityPassFactory()
        self.registration1 = RegistrationFactory(
            contact=self.contact, event=self.event1, priority_pass=self.priority_pass
        )
        self.registration2 = RegistrationFactory(
            contact=self.contact, event=self.event2, priority_pass=self.priority_pass
        )

    def extract_pdf_text(self, resp):
        content = b"".join(resp.streaming_content)
        self.assertTrue(content.startswith(b"%PDF"))
        text = extract_text(BytesIO(content))
        return unicodedata.normalize("NFKD", text)

    def test_priority_pass_view(self):
        self.client.login(email="admin@example.com", password="admin")
        resp = self.client.get(
            reverse("admin:priority_pass_view", args=[self.priority_pass.id])
            + "?pdf=true"
        )
        self.assertEqual(resp.status_code, 200)
        text = self.extract_pdf_text(resp)

        self.assertIn(self.event1.title, text)
        self.assertIn(self.event2.title, text)
        self.assertIn(self.contact.full_name, text)

    def test_priority_pass_download(self):
        self.client.login(email="admin@example.com", password="admin")
        resp = self.client.get(
            reverse("admin:priority_pass_view", args=[self.priority_pass.id])
            + "?pdf=true&download=true"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("attachment", resp.headers["Content-Disposition"])
        text = self.extract_pdf_text(resp)

        self.assertIn(self.event1.title, text)
        self.assertIn(self.event2.title, text)
        self.assertIn(self.contact.full_name, text)

    def test_placeholder_registration_deletable_via_formset(self):
        """Test that only placeholder registrations can be deleted via admin formset."""

        # Create a placeholder registration
        hidden_event = EventFactory(hide_for_nomination=True, group=self.group)
        placeholder_registration = RegistrationFactory(
            contact=self.contact,
            event=hidden_event,
            priority_pass=self.priority_pass,
            status="",
        )

        formset_class = inlineformset_factory(
            parent_model=PriorityPass,
            model=Registration,
            formset=RegistrationInlineFormSet,
            fields=("contact", "event", "role", "status"),
            can_delete=True,
            extra=0,
        )

        # Deleting placeholder registration should lead to valid form
        placeholder_data = {
            "registrations-TOTAL_FORMS": "1",
            "registrations-INITIAL_FORMS": "1",
            "registrations-MIN_NUM_FORMS": "0",
            "registrations-MAX_NUM_FORMS": "1000",
            "registrations-0-id": str(placeholder_registration.id),
            "registrations-0-contact": str(placeholder_registration.contact.id),
            "registrations-0-event": str(placeholder_registration.event.id),
            "registrations-0-role": str(placeholder_registration.role.id)
            if placeholder_registration.role
            else "",
            "registrations-0-status": "",
            # Mark for deletion
            "registrations-0-DELETE": "on",
        }

        placeholder_formset = formset_class(
            data=placeholder_data, instance=self.priority_pass
        )
        self.assertTrue(placeholder_formset.is_valid())

        # But deleting "regular" registration should not work due to disabled checkbox
        self.registration1.status = Registration.Status.NOMINATED
        self.registration1.save()

        protected_data = {
            "registrations-TOTAL_FORMS": "1",
            "registrations-INITIAL_FORMS": "1",
            "registrations-MIN_NUM_FORMS": "0",
            "registrations-MAX_NUM_FORMS": "1000",
            "registrations-0-id": str(self.registration1.id),
            "registrations-0-contact": str(self.registration1.contact.id),
            "registrations-0-event": str(self.registration1.event.id),
            "registrations-0-role": str(self.registration1.role.id)
            if self.registration1.role
            else "",
            "registrations-0-status": Registration.Status.NOMINATED,
            "registrations-0-DELETE": "on",
        }

        protected_formset = formset_class(
            data=protected_data,
            instance=self.priority_pass,
            queryset=Registration.objects.filter(id=self.registration1.id),
        )

        self.assertTrue(protected_formset.is_valid())
        # The formset's DELETE field should be auto-set to False due to disabled checkbox
        self.assertFalse(protected_formset.forms[0].cleaned_data["DELETE"])


class TestRegistrationAdmin(TestCase):
    fixtures = ["initial/role", "test/user"]

    def setUp(self):
        self.site = AdminSite()
        self.admin = RegistrationAdmin(Registration, self.site)
        self.priority_pass_admin = PriorityPassAdmin(PriorityPass, self.site)
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_superuser(
            email="admin_registration@example.com", password="password"
        )

        self.group = EventGroupFactory()
        self.event = EventFactory(group=self.group)
        self.contact = ContactFactory()
        self.priority_pass = PriorityPassFactory()
        self.registration = RegistrationFactory(
            contact=self.contact,
            event=self.event,
            priority_pass=self.priority_pass,
            status=Registration.Status.NOMINATED,
        )

    def test_status_update_to_blank_not_allowed(self):
        """Test that the status can't be blanked once it's set to a non-blank value."""

        # Set status to a real value
        self.registration.status = Registration.Status.ACCREDITED
        self.registration.save()

        # Try to clear it back to blank
        self.registration.status = ""
        with self.assertRaises(ValidationError):
            self.registration.full_clean()
            self.registration.save()

    def test_allow_blank_status_for_new_registrations(self):
        """Test that new registrations can be created with blank status."""
        hidden_event = EventFactory(hide_for_nomination=True)
        registration = RegistrationFactory(
            contact=self.contact,
            event=hidden_event,
            status="",
        )
        registration.full_clean()
        registration.save()
        self.assertEqual(registration.status, "")

    def test_allow_placeholder_status_update(self):
        """Test that registrations with blank status can be updated to another status."""
        hidden_event = EventFactory(hide_for_nomination=True)
        reg = RegistrationFactory(
            contact=self.contact,
            event=hidden_event,
            status="",
        )

        reg.status = Registration.Status.NOMINATED
        reg.full_clean()
        reg.save()
        self.assertEqual(reg.status, Registration.Status.NOMINATED)

    def test_registration_inline_prevents_status_clearing(self):
        """Tests that the registration inline formset prevents clearing status"""
        request = self.factory.post("/fake-admin-url/")
        request.user = self.user
        inline = RegistrationInline(PriorityPass, self.site)

        # Form data that tries to set the status to blank - i.e. clear it
        form_data = {
            "registrations-TOTAL_FORMS": "1",
            "registrations-INITIAL_FORMS": "1",
            "registrations-MIN_NUM_FORMS": "0",
            "registrations-MAX_NUM_FORMS": "1000",
            "registrations-0-id": str(self.registration.id),
            "registrations-0-contact": str(self.registration.contact.id),
            "registrations-0-event": str(self.registration.event.id),
            "registrations-0-role": str(self.registration.role.id)
            if self.registration.role
            else "",
            "registrations-0-status": "",
        }

        formset_class = inline.get_formset(request, self.priority_pass)
        formset = formset_class(data=form_data, instance=self.priority_pass)

        # Formset should be invalid due to status validation
        self.assertFalse(formset.is_valid())

        # Check that the error is about status "clearing"
        has_status_error = any(
            "status" in form.errors
            and any(
                "cannot be cleared" in str(error).lower()
                for error in form.errors["status"]
            )
            for form in formset.forms
            if form.errors
        )
        self.assertTrue(has_status_error)

    def test_registration_inline_save_model_calls_full_clean(self):
        """Test that save_model in inline calls full_clean."""
        request = self.factory.post("/fake-admin-url/")
        request.user = self.user

        inline = RegistrationInline(PriorityPass, self.site)

        # Create a registration with invalid data that's gonna fail full_clean()
        invalid_registration = Registration(
            contact=self.contact,
            event=self.event,
            priority_pass=self.priority_pass,
            status="",
        )
        invalid_registration.pk = self.registration.pk

        form = Mock()
        form.errors = {}
        form.cleaned_data = {
            "contact": self.contact,
            "event": self.event,
            "status": "",
            "role": self.registration.role,
            "priority_pass": self.priority_pass,
            "organization": None,
            "designation": "",
            "department": "",
            "is_funded": False,
            "date": timezone.now(),
        }
        added_errors = []

        def mock_add_error(field, error):
            """
            Mock add_error method that will populate the added_errors list instead
            """
            added_errors.append((field, error))
            if field not in form.errors:
                form.errors[field] = []
            form.errors[field].append(error)

        form.add_error = mock_add_error

        self.registration.status = Registration.Status.NOMINATED
        self.registration.save()

        # The call to save_model should add status-related errors to the form
        inline.save_model(request, invalid_registration, form, change=True)

        self.assertTrue(form.errors)
        self.assertTrue(added_errors)
        status_errors = [error for field, error in added_errors if field == "status"]
        self.assertTrue(
            any("cannot be cleared" in str(error).lower() for error in status_errors)
        )

    def test_registration_admin_readonly_fields(self):
        """Tests that contact and event become read-only after creation."""
        request = self.factory.get("/fake-admin-url/")
        request.user = self.user

        # Chack that only model read-only fields are read-only for new Registrations
        readonly_fields_new = self.admin.get_readonly_fields(request, obj=None)
        expected_for_new = (
            "created_at",
            "updated_at",
            "priority_pass",
            "credentials_display",
        )
        self.assertEqual(set(readonly_fields_new), set(expected_for_new))

        # And that for existing Registrations, contact and event become RO
        readonly_fields_existing = self.admin.get_readonly_fields(
            request, obj=self.registration
        )
        expected_for_existing = (
            "created_at",
            "updated_at",
            "priority_pass",
            "contact",
            "event",
            "credentials_display",
        )
        self.assertEqual(set(readonly_fields_existing), set(expected_for_existing))

    def test_delete_field_disabled_for_normal_registrations(self):
        """
        Tests the DELETE field's disabled for normal (non-placeholder) registrations.
        """
        self.registration.status = Registration.Status.NOMINATED
        self.registration.save()

        request = self.factory.get("/fake-admin-url/")
        request.user = self.user

        inline = RegistrationInline(PriorityPass, self.site)
        formset_class = inline.get_formset(request, self.priority_pass)
        formset = formset_class(instance=self.priority_pass)

        # Find the form for our protected registration
        protected_form = None
        for form in formset.forms:
            if hasattr(form, "instance") and form.instance.pk == self.registration.pk:
                protected_form = form
                break

        self.assertIsNotNone(protected_form)

        # Check that the DELETE field is disabled
        if "DELETE" in protected_form.fields:
            self.assertTrue(getattr(protected_form.fields["DELETE"], "disabled", False))

    def test_delete_field_enabled_for_placeholder_registrations(self):
        """
        Tests the DELETE field is enabled for "placeholder" registrations.
        """

        hidden_event = EventFactory(hide_for_nomination=True, group=self.group)
        placeholder_registration = RegistrationFactory(
            contact=self.contact,
            event=hidden_event,
            priority_pass=self.priority_pass,
            status="",
        )

        request = self.factory.get("/fake-admin-url/")
        request.user = self.user

        inline = RegistrationInline(PriorityPass, self.site)
        formset_class = inline.get_formset(request, self.priority_pass)
        formset = formset_class(instance=self.priority_pass)

        # Find the form for the created placeholder registration
        placeholder_form = None
        for form in formset.forms:
            if (
                hasattr(form, "instance")
                and form.instance.pk == placeholder_registration.pk
            ):
                placeholder_form = form
                break
        self.assertIsNotNone(placeholder_form)

        # Check the good old DELETE field is not disabled
        if "DELETE" in placeholder_form.fields:
            self.assertFalse(
                getattr(placeholder_form.fields["DELETE"], "disabled", False)
            )


class TestRegistrationAdminPriorityPassReuse(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            email="admin_reutilizabil@example.com", password="password"
        )
        self.site = AdminSite()
        self.admin = RegistrationAdmin(Registration, self.site)

        self.event_group = EventGroupFactory(name="Test Group")
        self.event1 = EventFactory(
            code="EVENT1",
            title="Event 1",
            group=self.event_group,
        )
        self.event2 = EventFactory(
            code="EVENT2",
            title="Event 2",
            group=self.event_group,
        )
        self.event_group.events.add(self.event1)
        self.event_group.events.add(self.event2)
        self.contact = ContactFactory(
            first_name="John", last_name="Snow", emails=["john@thenorth.com"]
        )
        self.role = RegistrationRoleFactory(name="Delegate")

    def test_priority_pass_reuse_in_same_event_group(self):
        """Test that registrations in same event group reuse priority pass."""

        # Create first registration manually (simulating admin creation)
        registration1 = Registration(
            contact=self.contact, event=self.event1, role=self.role
        )
        registration1.save()

        original_priority_pass = registration1.priority_pass
        self.assertIsNotNone(original_priority_pass)

        # Create second registration in same event group
        registration2 = Registration(
            contact=self.contact, event=self.event2, role=self.role
        )
        registration2.save()

        # Should reuse the same priority pass
        self.assertEqual(registration2.priority_pass, original_priority_pass)

    def test_no_priority_pass_reuse_across_different_groups(self):
        """Test that registrations in different event groups get separate priority passes."""

        # Create another event group
        other_group = EventGroupFactory(name="Another one bites the Group")
        event_other = EventFactory(
            code="OTHER",
            title="Other Event",
        )
        other_group.events.add(event_other)

        registration1 = Registration(
            contact=self.contact, event=self.event1, role=self.role
        )
        registration1.save()

        # Create a registration in the new/different group
        registration2 = Registration(
            contact=self.contact, event=event_other, role=self.role
        )
        registration2.save()

        # These should have different priority passes
        self.assertNotEqual(
            registration1.priority_pass.id, registration2.priority_pass.id
        )
