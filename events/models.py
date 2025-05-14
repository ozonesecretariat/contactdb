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
        if self.start_date > self.end_date:
            msg = "Start date must be before the end date"
            raise ValidationError(
                {
                    "start_date": msg,
                    "end_date": msg,
                }
            )


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
    TASK_TIMEOUT = 60
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
