from functools import cached_property
from django.core.exceptions import ValidationError
from django.db import models
from django_task.models import TaskRQ
from common.citext import CICharField
from core.models import Contact, Country, ContactGroup


class LoadEventsFromKronosTask(TaskRQ):
    DEFAULT_VERBOSITY = 2
    TASK_QUEUE = "default"
    TASK_TIMEOUT = 60
    LOG_TO_FIELD = True
    LOG_TO_FILE = False

    class Meta:
        get_latest_by = "created_on"

    @staticmethod
    def get_jobclass():
        from .jobs import LoadEventsFromKronos

        return LoadEventsFromKronos


class Event(models.Model):
    event_id = models.CharField(max_length=150, blank=True, null=True, unique=True)
    code = models.CharField(max_length=50, blank=False, null=False)
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
        ContactGroup, on_delete=models.SET_NULL, default=None, null=True, blank=True
    )

    def __str__(self):
        return self.title

    @property
    def imported_participants(self):
        return self.import_tasks.exists()

    @property
    def latest_import(self):
        if self.imported_participants:
            return self.import_tasks.latest()
        return None


class RegistrationTag(models.Model):
    name = CICharField(max_length=250, primary_key=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class RegistrationStatus(models.Model):
    name = CICharField(max_length=250, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "registration statuses"

    def __str__(self):
        return self.name


class RegistrationRole(models.Model):
    name = CICharField(max_length=250, unique=True)

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
    role = models.ForeignKey(
        RegistrationRole,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    priority_pass_code = models.CharField(
        max_length=150,
        blank=True,
        null=True,
    )
    date = models.DateTimeField()
    tags = models.ManyToManyField(RegistrationTag, blank=True)
    is_funded = models.BooleanField()

    class Meta:
        unique_together = (
            "contact",
            "event",
        )


class LoadParticipantsFromKronosTask(TaskRQ):
    DEFAULT_VERBOSITY = 2
    TASK_QUEUE = "default"
    TASK_TIMEOUT = 60
    LOG_TO_FIELD = True
    LOG_TO_FILE = False

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="import_tasks",
        help_text="Event to import participants for in this task.",
    )
    create_groups = models.BooleanField(
        default=True,
        help_text="Automatically create a group with the event title as the name.",
    )
    contacts_nr = models.PositiveIntegerField(
        default=0, editable=False, help_text="Number of newly created contacts created,"
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

    @staticmethod
    def get_jobclass():
        from .jobs import LoadParticipantsFromKronos

        return LoadParticipantsFromKronos
