import textwrap

import pycountry
from django.core.exceptions import ValidationError
from django.db import models
from django_task.models import TaskRQ

from common.array_field import ArrayField
from common.citext import CICharField
from common.utils import ConflictResolutionMethods


class Country(models.Model):
    code = CICharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "countries"

    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        self.code = self.code.upper()
        if not self.name:
            try:
                self.name = pycountry.countries.get(alpha_2=self.code).name
            except AttributeError:
                pass


class OrganizationType(models.Model):
    organization_type_id = models.CharField(max_length=250, unique=True)
    name = CICharField(max_length=250, primary_key=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Organization(models.Model):
    organization_id = models.CharField(max_length=250, unique=True)
    name = models.TextField()

    acronym = models.CharField(blank=True, max_length=30)
    organization_type = models.ForeignKey(OrganizationType, on_delete=models.CASCADE)
    government = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    def __str__(self):
        if self.country:
            return self.name + ", " + self.country.name
        return self.name

    class Meta:
        ordering = ["name", "country__name"]


class BaseContact(models.Model):
    organization = None
    contact_id = models.CharField(max_length=250, default="", blank=True)
    title = models.CharField(max_length=30, blank=True)
    honorific = models.CharField(max_length=30, default="", blank=True)
    respectful = models.CharField(max_length=30, default="", blank=True)
    first_name = models.CharField(max_length=250, default="", blank=True)
    last_name = models.CharField(max_length=250, default="", blank=True)
    designation = models.TextField(default="", blank=True)
    department = models.TextField(default="", blank=True)
    affiliation = models.TextField(default="", blank=True)
    primary_lang = models.CharField(
        max_length=100, default="", blank=True, verbose_name="primary language"
    )
    second_lang = models.CharField(
        max_length=100, default="", blank=True, verbose_name="second language"
    )
    third_lang = models.CharField(
        max_length=100, default="", blank=True, verbose_name="third language"
    )
    phones = ArrayField(null=True, base_field=models.TextField(), blank=True)
    mobiles = ArrayField(null=True, base_field=models.TextField(), blank=True)
    faxes = ArrayField(null=True, base_field=models.TextField(), blank=True)
    emails = ArrayField(null=True, base_field=models.EmailField(), blank=True)
    email_ccs = ArrayField(null=True, base_field=models.EmailField(), blank=True)
    notes = models.TextField(default="", blank=True)
    is_in_mailing_list = models.BooleanField(default=False, blank=True)
    is_use_organization_address = models.BooleanField(default=False, blank=True)
    address = models.TextField(default="", blank=True)
    city = models.CharField(max_length=250, default="", blank=True)
    state = models.CharField(max_length=250, default="", blank=True)
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    postal_code = models.CharField(max_length=250, default="", blank=True)
    birth_date = models.DateField(null=True, blank=True)
    focal_point = models.BooleanField(default=False, blank=True)
    org_head = models.BooleanField(
        default=False, blank=True, verbose_name="head of organization"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    main_contact = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="secondary_contacts",
        limit_choices_to={"main_contact": None},
    )

    class Meta:
        abstract = True

    def __str__(self):
        if self.organization:
            return f"{self.full_name} ({self.organization})"
        return self.full_name

    @property
    def full_name(self):
        return " ".join([self.title, self.first_name, self.last_name]).strip()

    @property
    def is_secondary(self):
        return self.main_contact is not None

    def clean(self):
        if not self.first_name and not self.last_name:
            raise ValidationError(
                {
                    "first_name": "At least first name or last name must be provided",
                    "last_name": "At least first name or last name must be provided",
                }
            )
        if self.main_contact == self:
            raise ValidationError(
                {"main_contact": "A contact cannot be the main contact for themself."}
            )

        if self.main_contact and self.main_contact.main_contact:
            raise ValidationError(
                {"main_contact": "Main contact must not be a secondary contact"}
            )


class Contact(BaseContact):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contacts",
    )


class ResolveConflict(BaseContact):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conflicting_contacts",
    )
    existing_contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="conflicting_contacts",
    )


class ContactGroup(models.Model):
    name = models.TextField(null=False, blank=False)
    description = models.TextField(blank=True, null=True)
    contacts = models.ManyToManyField(
        Contact,
        blank=True,
        through="GroupMembership",
        related_name="groups",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def members_count(self):
        return self.contacts.count()

    @property
    def description_preview(self):
        return textwrap.shorten(self.description or "", 150)


class GroupMembership(models.Model):
    group = models.ForeignKey(ContactGroup, on_delete=models.CASCADE)
    contact = models.ForeignKey(
        Contact, on_delete=models.CASCADE, related_name="memberships"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("group", "contact")


class ResolveAllConflictsTask(TaskRQ):
    DEFAULT_VERBOSITY = 2
    TASK_QUEUE = "default"
    TASK_TIMEOUT = 60
    LOG_TO_FIELD = True
    LOG_TO_FILE = False

    method = models.CharField(max_length=60, choices=ConflictResolutionMethods.choices)

    class Meta:
        get_latest_by = "created_on"

    @staticmethod
    def get_jobclass():
        from .jobs import ResolveAllConflicts

        return ResolveAllConflicts
