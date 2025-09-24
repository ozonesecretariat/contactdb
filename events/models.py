import math
import uuid
from urllib.parse import urljoin

from ckeditor_uploader.fields import RichTextUploadingField
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import models
from django.db.models import Exists, Max, Min, OuterRef, Q
from django.utils import timezone
from django_extensions.db.fields import RandomCharField
from django_task.models import TaskRQ
from encrypted_fields import EncryptedJSONField

from common.array_field import ArrayField
from common.citext import CICharField
from common.model import KronosEnum, KronosId
from common.pdf import print_pdf
from core.models import Contact, Country, Organization
from emails.validators import validate_placeholders


class LoadEventsFromKronosTask(TaskRQ):
    DEFAULT_VERBOSITY = 2
    TASK_QUEUE = "default"
    TASK_TIMEOUT = 300
    LOG_TO_FIELD = True
    LOG_TO_FILE = False

    class Meta:
        get_latest_by = "created_on"

    @staticmethod
    def get_jobclass():
        from .jobs import LoadEventsFromKronos

        return LoadEventsFromKronos


class EventGroup(models.Model):
    name = CICharField(max_length=250, null=False, blank=False, unique=True)
    description = models.TextField(
        blank=True, help_text="Optional description of the event group"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "event group"
        verbose_name_plural = "event groups"

    def __str__(self):
        return self.name

    @property
    def group_start_date(self):
        return self.events.aggregate(Min("start_date"))["start_date__min"]

    @property
    def group_end_date(self):
        return self.events.aggregate(Max("end_date"))["end_date__max"]


class Event(models.Model):
    event_id = KronosId()
    code = models.CharField(max_length=50, blank=False, null=False, unique=True)
    title = models.CharField(max_length=255, blank=False, null=False)
    start_date = models.DateTimeField(null=False)
    end_date = models.DateTimeField(null=False)
    venue_country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    venue_city = models.CharField(max_length=150)
    dates = models.CharField(max_length=255)

    group = models.ForeignKey(
        EventGroup,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="events",
        help_text="Group linking related events",
    )
    hide_for_nomination = models.BooleanField(
        default=False,
        help_text="Do not allow direct nominations for this event",
    )

    attach_priority_pass = models.BooleanField(
        default=False,
        help_text="Automatically attach priority pass to the accredited confirmation email",
    )
    confirmation_subject = models.CharField(
        max_length=900, validators=[validate_placeholders], default="", blank=True
    )
    confirmation_content = RichTextUploadingField(
        validators=[validate_placeholders], default="", blank=True
    )
    refuse_subject = models.CharField(
        max_length=900, validators=[validate_placeholders], default="", blank=True
    )
    refuse_content = RichTextUploadingField(
        validators=[validate_placeholders], default="", blank=True
    )

    event_logo = models.ImageField(
        upload_to="event_logo/",
        null=True,
        blank=True,
        help_text="Event logo displayed on the badge",
    )
    wifi_name = models.CharField(max_length=255, blank=True)
    wifi_password = models.CharField(max_length=255, blank=True)

    app_store_url = models.CharField(max_length=1024, blank=True)
    play_store_url = models.CharField(max_length=1024, blank=True)
    # TODO: Allow choosing the badge template for the event

    lop_doc_symbols = ArrayField(
        null=True,
        base_field=models.TextField(),
        blank=True,
        help_text="Document symbols for the List of Participants document",
    )

    # DSA
    dsa = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    term_exp = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    event_id_number = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ("-start_date",)

    def __str__(self):
        return f"{self.code} {self.title}"

    @property
    def imported_participants(self):
        return self.import_tasks.exists()

    @property
    def latest_import(self):
        if self.imported_participants:
            return self.import_tasks.latest()
        return None

    @property
    def venue(self):
        if self.venue_country:
            return f"{self.venue_city}, {self.venue_country.name}"
        return self.venue_city

    @property
    def has_confirmation_email(self):
        return bool(self.confirmation_subject and self.confirmation_content)

    @property
    def has_refused_email(self):
        return bool(self.refuse_subject and self.refuse_content)

    def clean(self):
        if not self.start_date or not self.end_date:
            return

        if self.start_date > self.end_date:
            msg = "Start date must be before the end date"
            raise ValidationError(
                {
                    "start_date": msg,
                    "end_date": msg,
                }
            )

        if self.attach_priority_pass and (
            not self.confirmation_content or not self.confirmation_subject
        ):
            msg = "Cannot attach priority pass without confirmation email content and subject"
            raise ValidationError(
                {
                    "attach_priority_pass": msg,
                    "confirmation_subject": msg,
                    "confirmation_content": msg,
                }
            )


class EventInvitation(models.Model):
    event_group = models.ForeignKey(
        EventGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="invitations",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="invitations",
    )

    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="event_invitations",
        help_text="When country is set, all GOV organizations in country are invited",
    )
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="event_invitations",
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Unique token for invitation link",
    )
    link_accessed = models.BooleanField(
        default=False, help_text="Whether the invitation link has been accessed"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["event_group", "country"],
                condition=models.Q(
                    event_group__isnull=False,
                    country__isnull=False,
                ),
                name="unique_eventgroup_country",
            ),
            models.UniqueConstraint(
                fields=["event_group", "organization"],
                condition=models.Q(
                    event_group__isnull=False,
                    organization__isnull=False,
                ),
                name="unique_eventgroup_organization",
            ),
            models.UniqueConstraint(
                fields=["event", "country"],
                condition=models.Q(
                    event__isnull=False,
                    country__isnull=False,
                ),
                name="unique_event_country",
            ),
            models.UniqueConstraint(
                fields=["event", "organization"],
                condition=models.Q(
                    event__isnull=False,
                    organization__isnull=False,
                ),
                name="unique_event_organization",
            ),
        ]

    def __str__(self):
        invitee = self.country or self.organization
        target = self.event_group or self.event
        return f"Invitation for {invitee} to {target}"

    def clean(self):
        if not self.event_group and not self.event:
            raise ValidationError("Either event_group or event must be specified")
        if self.event_group and self.event:
            raise ValidationError("Cannot specify both event_group and event")

        if not self.country and not self.organization:
            raise ValidationError("Either country or organization must be specified")
        if self.country and self.organization:
            raise ValidationError("Cannot specify both country and organization")

    @property
    def invitation_link(self):
        # This will need to be updated if frontend path changes
        url_path = f"/token/{self.token}/nominations"
        domain = settings.PROTOCOL + settings.MAIN_FRONTEND_HOST

        return urljoin(domain, url_path)

    @property
    def invitation_link_html(self):
        return f'<a href="{self.invitation_link}" target="_blank">{self.invitation_link}</a>'

    @property
    def is_for_future_event(self):
        today = timezone.now()

        if self.event and self.event.start_date and self.event.start_date >= today:
            return True

        if self.event_group:
            future_events = self.event_group.events.filter(
                start_date__gte=today
            ).exists()
            if future_events:
                return True

        return False

    @property
    def unregistered_organizations(self):
        """
        Get organizations that haven't registered any contacts for this invitation.
        All types of registration (including Nomination) are taken into account.
        """
        # Get all events related to this invitation
        events = []
        if self.event:
            events = [self.event]
        elif self.event_group:
            events = list(self.event_group.events.all())

        if not events:
            return Organization.objects.none()

        # Get organizations that should have registered
        if self.organization:
            orgs_queryset = Organization.objects.filter(id=self.organization.id)
        elif self.country:
            # If invitation is for country, check all GOV orgs in that country
            # TODO: is this enough to properly take GOV into account?
            orgs_queryset = Organization.objects.filter(
                organization_type__acronym="GOV", government=self.country
            )
        else:
            return Organization.objects.none()

        return (
            orgs_queryset.annotate(
                has_registrations=Exists(
                    Registration.objects.filter(
                        event__in=events, contact__organization=OuterRef("pk")
                    )
                )
            )
            .filter(has_registrations=False)
            .order_by("name")
        )


class RegistrationTag(models.Model):
    name = CICharField(max_length=250, primary_key=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class RegistrationRole(models.Model):
    name = CICharField(max_length=250, unique=True)
    hide_for_nomination = models.BooleanField(
        default=False, help_text="Hide this role in the nomination form."
    )
    hide_in_lop = models.BooleanField(
        default=False, help_text="Hide in the List of Participants document"
    )
    sort_order = models.PositiveIntegerField(default=0)
    kronos_value = KronosEnum()

    class Meta:
        ordering = ("sort_order", "name")

    def __str__(self):
        return self.name


class PriorityPass(models.Model):
    code = RandomCharField(
        length=10, blank=True, uppercase=True, unique=True, keep_default=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "priority pass"
        verbose_name_plural = "priority passes"

    def __str__(self):
        return self.code

    def clean(self):
        super().clean()
        if len(self.contact_ids) > 1:
            raise ValidationError(
                "Priority pass can only be used for one contact at a time"
            )

    @property
    def qr_url(self):
        return (
            settings.PROTOCOL
            + settings.MAIN_FRONTEND_HOST
            + "/scan-pass"
            + f"?code={self.code}"
        )

    @property
    def priority_pass_template(self):
        return "admin/events/prioritypass/priority_pass.html"

    @property
    def badge_template(self):
        return "admin/events/prioritypass/badge/badge1.html"

    @property
    def priority_pass_context(self):
        return {
            "priority_pass": self,
            "qr_url": self.qr_url,
            "registrations": self.valid_registrations,
            "organization": self.organization,
            "organization_name": self.organization_name,
            "contact": self.contact,
            "country": self.country,
            "address_entity": self.address_entity,
            "main_event": self.main_event,
        }

    @property
    def valid_registrations(self):
        return [
            r
            for r in self.registrations.all()
            if r.status not in ("", Registration.Status.REVOKED)
        ]

    @property
    def contact(self):
        for registration in self.registrations.all():
            if registration.contact:
                return registration.contact

        return None

    @property
    def contact_ids(self):
        return {r.contact_id for r in self.registrations.all()}

    @property
    def organization(self):
        for registration in self.valid_registrations:
            if registration.organization:
                return registration.organization

        if self.contact:
            return self.contact.organization

        return None

    @property
    def organization_name(self):
        if not self.organization:
            return None
        return self.organization.name

    @property
    def is_gov(self):
        try:
            return self.organization.organization_type.acronym == "GOV"
        except AttributeError:
            return False

    @property
    def country(self):
        if self.organization:
            return self.organization.government or self.organization.country

        if self.contact:
            return self.contact.country

        return None

    @property
    def address_entity(self):
        if self.contact and self.contact.is_use_organization_address:
            return self.organization

        if self.contact:
            return self.contact

        return None

    @property
    def main_event(self):
        registrations = list(self.registrations.all())
        if not registrations:
            return None

        for registration in registrations:
            if registration.event.attach_priority_pass:
                return registration.event

        return registrations[0].event

    def _filter_registrations(self, status: "Registration.Status"):
        # Filter here instead of SQL to take advantage of prefetching.
        return [
            registration
            for registration in self.registrations.all()
            if registration.status == status
        ]

    @property
    def accredited_registrations(self):
        return self._filter_registrations(Registration.Status.ACCREDITED)

    @property
    def revoked_registrations(self):
        return self._filter_registrations(Registration.Status.REVOKED)

    @property
    def registered_registrations(self):
        return self._filter_registrations(Registration.Status.REGISTERED)

    @property
    def valid_from(self):
        try:
            return min(reg.event.start_date for reg in self.registered_registrations)
        except ValueError:
            return None

    @property
    def valid_to(self):
        try:
            return max(reg.event.end_date for reg in self.registered_registrations)
        except ValueError:
            return None

    @property
    def valid_date_range(self):
        date_fmt = "%-d %b %Y"
        start, end = self.valid_from, self.valid_to

        if not start and not end:
            return ""

        if start == end or (bool(start) ^ bool(end)):
            return (start or end).strftime(date_fmt)

        if end < start:
            start, end = end, start

        same_year = start.year == end.year
        same_month = start.month == end.month

        if same_year and same_month:
            return "{start_day}-{end_day} {month} {year}".format(
                month=start.strftime("%b"),
                start_day=start.day,
                end_day=end.day,
                year=start.year,
            )

        if same_year:
            return "{start_day} {start_month} - {end_day} {end_month} {year}".format(
                start_month=start.strftime("%b"),
                start_day=start.day,
                end_month=end.strftime("%b"),
                end_day=end.day,
                year=start.year,
            )

        return "{start_date} to {end_date}".format(
            start_date=start.strftime(date_fmt),
            end_date=end.strftime(date_fmt),
        )

    def send_confirmation_email(self):
        if not self.main_event or not self.main_event.has_confirmation_email:
            return
        if not self.accredited_registrations:
            return

        from emails.models import Email

        msg = Email.objects.create(
            subject=self.main_event.confirmation_subject,
            content=self.main_event.confirmation_content,
        )
        msg.recipients.add(self.contact)
        if self.main_event.attach_priority_pass:
            msg.attachments.create(
                file=File(
                    print_pdf(
                        template=self.priority_pass_template,
                        context=self.priority_pass_context,
                    ),
                    name=f"{self.code}.pdf",
                ),
            )
        msg.queue_emails()

    def send_refused_email(self):
        if not self.main_event or not self.main_event.has_refused_email:
            return
        if not self.revoked_registrations:
            return

        from emails.models import Email

        msg = Email.objects.create(
            subject=self.main_event.refuse_subject,
            content=self.main_event.refuse_content,
        )
        msg.recipients.add(self.contact)
        msg.queue_emails()


class Registration(models.Model):
    class Status(models.TextChoices):
        NOMINATED = "Nominated", "Nominated"
        ACCREDITED = "Accredited", "Accredited"
        REGISTERED = "Registered", "Registered"
        REVOKED = "Revoked", "Revoked"

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations",
    )

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NOMINATED, blank=True
    )
    role = models.ForeignKey(RegistrationRole, on_delete=models.SET_NULL, null=True)
    priority_pass = models.ForeignKey(
        PriorityPass,
        on_delete=models.SET_NULL,
        null=True,
        related_name="registrations",
    )
    date = models.DateTimeField(default=timezone.now)
    tags = models.ManyToManyField(RegistrationTag, blank=True)
    is_funded = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(
        default=None,
        null=True,
        blank=True,
        help_text="Override the role sort order for this registration.",
    )

    # Save the state of organization, designation, and department as it
    # was when the contact registered
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="registrations",
        verbose_name="Organization",
    )
    designation = models.TextField(default="", blank=True, verbose_name="Job title")
    department = models.TextField(default="", blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = ("contact", "event")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.event.code} - {self.contact.full_name} ({self.status})"

    def save(self, *args, **kwargs):
        """
        Overridden to reuse priority pass for same contact and event in the same group,
        or create a new priority pass if none can be reused
        """
        if not self.pk and not self.priority_pass and self.event and self.event.group:
            existing_registration = (
                Registration.objects.filter(
                    contact=self.contact,
                    event__group=self.event.group,
                    priority_pass__isnull=False,
                )
                .order_by("-created_at")
                .first()
            )

            if existing_registration:
                self.priority_pass = existing_registration.priority_pass

        # If one could not be reused, create a new priority pass
        if not self.priority_pass:
            self.priority_pass = PriorityPass.objects.create()

        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.priority_pass and {self.contact_id} != self.priority_pass.contact_ids:
            raise ValidationError(
                "Priority pass can only be used for one contact at a time"
            )

        # Do not allow status changes from non-blank to blank for existing Registrations.
        # This prevents possible future deletions of non-placeholder Registrations.
        if self.pk:
            try:
                original = Registration.objects.get(pk=self.pk)
                if original.status and original.status != "" and self.status == "":
                    raise ValidationError(
                        {"status": "Status cannot be cleared once it has been set."}
                    )
            except Registration.DoesNotExist:
                pass

    @property
    def usable_government(self) -> Country | None:
        return self.usable_organization and self.usable_organization.government

    @property
    def usable_organization(self) -> Organization | None:
        return self.organization or self.contact.organization

    @property
    def usable_organization_name(self) -> str | None:
        try:
            return self.organization.name
        except AttributeError:
            return None

    @property
    def usable_organization_sort_order(self) -> int | float:
        try:
            return self.usable_organization.sort_order
        except AttributeError:
            return math.inf

    @property
    def usable_organization_type_sort_order(self) -> int | float:
        try:
            return self.usable_organization.organization_type.sort_order
        except AttributeError:
            return math.inf

    @property
    def usable_organization_type_description(self) -> str | None:
        try:
            return self.usable_organization.organization_type.description
        except AttributeError:
            return None

    @property
    def is_gov(self):
        try:
            return self.usable_organization.is_gov
        except AttributeError:
            return False

    @property
    def is_ass_panel(self):
        try:
            return self.usable_organization.is_ass_panel
        except AttributeError:
            return False

    @property
    def is_secretariat(self):
        try:
            return self.usable_organization.is_secretariat
        except AttributeError:
            return False

    @property
    def dsa_country(self):
        if self.is_gov:
            return self.usable_government
        if self.usable_organization:
            return self.usable_organization.country
        return None


class LoadParticipantsFromKronosTask(TaskRQ):
    DEFAULT_VERBOSITY = 2
    TASK_QUEUE = "default"
    TASK_TIMEOUT = 300
    LOG_TO_FIELD = True
    LOG_TO_FILE = False

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="import_tasks",
        help_text="Event to import participants for in this task.",
        limit_choices_to=Q(event_id__isnull=False),
    )
    contacts_nr = models.PositiveIntegerField(
        default=0, editable=False, help_text="Number of newly created contacts."
    )
    registrations_nr = models.PositiveIntegerField(
        default=0, editable=False, help_text="Number of event registrations created."
    )
    conflicts_nr = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="Number of conflicts found and saved for manual resolution.",
    )
    skipped_nr = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="Number of contacts with no changes that were ignored.",
    )

    class Meta:
        get_latest_by = "created_on"

    def __str__(self):
        return self.event.code

    @staticmethod
    def get_jobclass():
        from .jobs import LoadParticipantsFromKronos

        return LoadParticipantsFromKronos


class LoadOrganizationsFromKronosTask(TaskRQ):
    """
    Task for loading Organizations not imported when Events were parsed.
    """

    DEFAULT_VERBOSITY = 2
    TASK_QUEUE = "default"
    TASK_TIMEOUT = 300
    LOG_TO_FIELD = True
    LOG_TO_FILE = False

    organizations_nr = models.PositiveIntegerField(
        default=0, editable=False, help_text="Number of new organizations created."
    )
    contacts_nr = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="Number of contacts added to new organizations.",
    )
    skipped_contacts_nr = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="Number of contacts skipped as they mathced new organization but belonged to another.",
    )

    class Meta:
        get_latest_by = "created_on"

    @staticmethod
    def get_jobclass():
        from .jobs import LoadOrganizationsFromKronos

        return LoadOrganizationsFromKronos


class DSA(models.Model):
    registration = models.OneToOneField(
        Registration, on_delete=models.CASCADE, related_name="dsa"
    )
    umoja_travel = models.CharField(max_length=255, blank=True)
    bp = models.CharField(max_length=255, blank=True)
    arrival_date = models.DateField(blank=True, null=True)
    departure_date = models.DateField(blank=True, null=True)
    cash_card = models.CharField(max_length=255, blank=True)
    paid_dsa = models.BooleanField(default=False)

    boarding_pass = EncryptedJSONField(blank=True, null=True)
    passport = EncryptedJSONField(blank=True, null=True)
    signature = EncryptedJSONField(blank=True, null=True)

    class Meta:
        verbose_name = "DSA"
        verbose_name_plural = "DSAs"

    def __str__(self):
        return f"DSA - {self.registration}"

    def clean(self):
        if self.departure_date and not self.arrival_date:
            raise ValidationError(
                {"arrival_date": "Cannot specify departure date without arrival date."}
            )

        if (
            self.departure_date
            and self.arrival_date
            and self.departure_date < self.arrival_date
        ):
            msg = "Departure date cannot be before arrival date."
            raise ValidationError(
                {
                    "arrival_date": msg,
                    "departure_date": msg,
                }
            )

    @property
    def number_of_days(self):
        if not self.arrival_date or not self.departure_date:
            return 0

        return (self.departure_date - self.arrival_date).days + 1

    @property
    def dsa_on_arrival(self):
        return self.number_of_days * (self.registration.event.dsa or 0)

    @property
    def total_dsa(self):
        return self.dsa_on_arrival + (self.registration.event.term_exp or 0)
