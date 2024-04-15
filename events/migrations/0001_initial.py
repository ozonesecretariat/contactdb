# Generated by Django 4.2.11 on 2024-04-15 06:53

import common.citext
import common.model
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0002_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "event_id",
                    common.model.KronosId(
                        blank=True,
                        editable=False,
                        help_text="Unique Kronos ID. Will not be available if record was not imported from Kronos.",
                        max_length=24,
                        null=True,
                        unique=True,
                    ),
                ),
                ("code", models.CharField(max_length=50)),
                ("title", models.CharField(max_length=255)),
                ("start_date", models.DateTimeField()),
                ("end_date", models.DateTimeField()),
                ("venue_city", models.CharField(max_length=150)),
                ("dates", models.CharField(max_length=255)),
                (
                    "venue_country",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.country",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RegistrationRole",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", common.citext.CICharField(max_length=250, unique=True)),
                (
                    "kronos_value",
                    common.model.KronosEnum(
                        blank=True,
                        default=-1,
                        editable=False,
                        help_text="Unique Kronos Enum value. Will not be available if record was not imported from Kronos.",
                        null=True,
                    ),
                ),
            ],
            options={
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="RegistrationStatus",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", common.citext.CICharField(max_length=250, unique=True)),
                (
                    "kronos_value",
                    common.model.KronosEnum(
                        blank=True,
                        default=-1,
                        editable=False,
                        help_text="Unique Kronos Enum value. Will not be available if record was not imported from Kronos.",
                        null=True,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "registration statuses",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="RegistrationTag",
            fields=[
                (
                    "name",
                    common.citext.CICharField(
                        max_length=250, primary_key=True, serialize=False
                    ),
                ),
            ],
            options={
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="LoadParticipantsFromKronosTask",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                        verbose_name="id",
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True, max_length=256, verbose_name="description"
                    ),
                ),
                (
                    "created_on",
                    models.DateTimeField(auto_now_add=True, verbose_name="created on"),
                ),
                (
                    "started_on",
                    models.DateTimeField(null=True, verbose_name="started on"),
                ),
                (
                    "completed_on",
                    models.DateTimeField(null=True, verbose_name="completed on"),
                ),
                (
                    "progress",
                    models.IntegerField(blank=True, null=True, verbose_name="progress"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "PENDING"),
                            ("RECEIVED", "RECEIVED"),
                            ("STARTED", "STARTED"),
                            ("PROGESS", "PROGESS"),
                            ("SUCCESS", "SUCCESS"),
                            ("FAILURE", "FAILURE"),
                            ("REVOKED", "REVOKED"),
                            ("REJECTED", "REJECTED"),
                            ("RETRY", "RETRY"),
                            ("IGNORED", "IGNORED"),
                        ],
                        db_index=True,
                        default="PENDING",
                        max_length=128,
                        verbose_name="status",
                    ),
                ),
                (
                    "job_id",
                    models.CharField(blank=True, max_length=128, verbose_name="job id"),
                ),
                (
                    "mode",
                    models.CharField(
                        choices=[
                            ("UNKNOWN", "UNKNOWN"),
                            ("SYNC", "SYNC"),
                            ("ASYNC", "ASYNC"),
                        ],
                        db_index=True,
                        default="UNKNOWN",
                        max_length=128,
                        verbose_name="mode",
                    ),
                ),
                (
                    "failure_reason",
                    models.CharField(
                        blank=True, max_length=256, verbose_name="failure reason"
                    ),
                ),
                ("log_text", models.TextField(blank=True, verbose_name="log text")),
                (
                    "contacts_nr",
                    models.PositiveIntegerField(
                        default=0,
                        editable=False,
                        help_text="Number of newly created contacts created,",
                    ),
                ),
                (
                    "registrations_nr",
                    models.PositiveIntegerField(
                        default=0,
                        editable=False,
                        help_text="Number of event registrations created.",
                    ),
                ),
                (
                    "conflicts_nr",
                    models.PositiveIntegerField(
                        default=0,
                        editable=False,
                        help_text="Number of conflicts found and saved for manual resolution.",
                    ),
                ),
                (
                    "skipped_nr",
                    models.PositiveIntegerField(
                        default=0,
                        editable=False,
                        help_text="Number of contacts with no changes that were ignored.",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        help_text="Event to import participants for in this task.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="import_tasks",
                        to="events.event",
                    ),
                ),
            ],
            options={
                "get_latest_by": "created_on",
            },
        ),
        migrations.CreateModel(
            name="LoadEventsFromKronosTask",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                        verbose_name="id",
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True, max_length=256, verbose_name="description"
                    ),
                ),
                (
                    "created_on",
                    models.DateTimeField(auto_now_add=True, verbose_name="created on"),
                ),
                (
                    "started_on",
                    models.DateTimeField(null=True, verbose_name="started on"),
                ),
                (
                    "completed_on",
                    models.DateTimeField(null=True, verbose_name="completed on"),
                ),
                (
                    "progress",
                    models.IntegerField(blank=True, null=True, verbose_name="progress"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "PENDING"),
                            ("RECEIVED", "RECEIVED"),
                            ("STARTED", "STARTED"),
                            ("PROGESS", "PROGESS"),
                            ("SUCCESS", "SUCCESS"),
                            ("FAILURE", "FAILURE"),
                            ("REVOKED", "REVOKED"),
                            ("REJECTED", "REJECTED"),
                            ("RETRY", "RETRY"),
                            ("IGNORED", "IGNORED"),
                        ],
                        db_index=True,
                        default="PENDING",
                        max_length=128,
                        verbose_name="status",
                    ),
                ),
                (
                    "job_id",
                    models.CharField(blank=True, max_length=128, verbose_name="job id"),
                ),
                (
                    "mode",
                    models.CharField(
                        choices=[
                            ("UNKNOWN", "UNKNOWN"),
                            ("SYNC", "SYNC"),
                            ("ASYNC", "ASYNC"),
                        ],
                        db_index=True,
                        default="UNKNOWN",
                        max_length=128,
                        verbose_name="mode",
                    ),
                ),
                (
                    "failure_reason",
                    models.CharField(
                        blank=True, max_length=256, verbose_name="failure reason"
                    ),
                ),
                ("log_text", models.TextField(blank=True, verbose_name="log text")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "get_latest_by": "created_on",
            },
        ),
        migrations.CreateModel(
            name="Registration",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "priority_pass_code",
                    models.CharField(blank=True, max_length=150, null=True),
                ),
                ("date", models.DateTimeField()),
                ("is_funded", models.BooleanField()),
                (
                    "contact",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="registrations",
                        to="core.contact",
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="registrations",
                        to="events.event",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="events.registrationrole",
                    ),
                ),
                (
                    "status",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="events.registrationstatus",
                    ),
                ),
                (
                    "tags",
                    models.ManyToManyField(blank=True, to="events.registrationtag"),
                ),
            ],
            options={
                "unique_together": {("contact", "event")},
            },
        ),
    ]
