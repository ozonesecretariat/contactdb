import uuid
from urllib.parse import urljoin

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django_task.models import TaskRQ

from common.citext import CICharField
from common.model import KronosEnum, KronosId
from core.models import Contact, Country


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
        ordering = ("name",)
        verbose_name = "event group"
        verbose_name_plural = "event groups"

    def __str__(self):
        return self.name


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

    groups = models.ManyToManyField(
        EventGroup,
        blank=True,
        related_name="events",
        help_text="Groups linking related events",
    )

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
        url_path = f"/events/{self.token}/nominations"
        domain = settings.PROTOCOL + settings.MAIN_FRONTEND_HOST

        return urljoin(domain, url_path)


class RegistrationTag(models.Model):
    name = CICharField(max_length=250, primary_key=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class RegistrationStatus(models.Model):
    name = CICharField(max_length=250, unique=True)
    kronos_value = KronosEnum()

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "registration statuses"

    def __str__(self):
        return self.name


class RegistrationRole(models.Model):
    name = CICharField(max_length=250, unique=True)
    kronos_value = KronosEnum()

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Registration(models.Model):
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
    status = models.ForeignKey(RegistrationStatus, on_delete=models.CASCADE)
    role = models.ForeignKey(RegistrationRole, on_delete=models.CASCADE)
    priority_pass_code = models.CharField(max_length=150, blank=True)
    date = models.DateTimeField()
    tags = models.ManyToManyField(RegistrationTag, blank=True)
    is_funded = models.BooleanField()

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = (
            "contact",
            "event",
        )

    def __str__(self):
        return f"{self.event.code} - {self.contact.full_name}"


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
