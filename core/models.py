import contextlib
import textwrap
from uuid import uuid4

import pycountry
from django.core.exceptions import ValidationError
from django.db import models
from django_db_views.db_view import DBView
from django_task.models import TaskRQ
from encrypted_fields import EncryptedCharField, EncryptedDateField, EncryptedJSONField
from psycopg import sql

from common.array_field import ArrayField
from common.citext import CICharField, CIEmailField
from common.model import KronosId, get_protected_storage


class Country(models.Model):
    code = CICharField(max_length=2, primary_key=True)
    name = CICharField(max_length=255, blank=True)
    official_name = CICharField(max_length=255, blank=True)
    region = models.ForeignKey(
        "Region",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="countries",
    )
    subregion = models.ForeignKey(
        "Subregion",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="countries",
    )

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "countries"

    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        self.code = self.code.upper()
        if not self.name:
            with contextlib.suppress(AttributeError, LookupError):
                self.name = pycountry.countries.get(alpha_2=self.code).name
        if not self.official_name:
            with contextlib.suppress(AttributeError, LookupError):
                self.official_name = pycountry.countries.get(
                    alpha_2=self.code
                ).official_name


class OrganizationType(models.Model):
    organization_type_id = KronosId()
    acronym = CICharField(max_length=50, primary_key=True)
    title = CICharField(max_length=250, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("title",)

    def __str__(self):
        return f"{self.title} ({self.acronym})"


class Organization(models.Model):
    organization_id = KronosId()
    name = models.TextField()
    alt_names = ArrayField(
        base_field=models.TextField(),
        blank=True,
        null=True,
    )
    acronym = models.CharField(blank=True, max_length=30)
    organization_type = models.ForeignKey(
        OrganizationType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="organizations",
    )
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
    state = models.CharField(max_length=250, default="", blank=True)
    city = models.CharField(max_length=250, default="", blank=True)
    postal_code = models.CharField(max_length=250, default="", blank=True)
    address = models.TextField(default="", blank=True)

    phones = ArrayField(null=True, base_field=models.TextField(), blank=True)
    faxes = ArrayField(null=True, base_field=models.TextField(), blank=True)
    websites = ArrayField(null=True, base_field=models.TextField(), blank=True)
    emails = ArrayField(null=True, base_field=CIEmailField(), blank=True)
    email_ccs = ArrayField(null=True, base_field=CIEmailField(), blank=True)

    primary_contacts = models.ManyToManyField(
        "Contact", related_name="primary_for_orgs"
    )
    secondary_contacts = models.ManyToManyField(
        "Contact", related_name="secondary_for_orgs"
    )
    include_in_invitation = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "country__name"]

    def __str__(self):
        if self.government:
            return self.name + ", " + self.government.name
        if self.country:
            return self.name + ", " + self.country.name
        return self.name

    def filter_contacts_by_emails(self, emails: list[str]):
        return self.contacts.filter(
            models.Q(emails__overlap=emails) | models.Q(email_ccs__overlap=emails)
        )

    def get_related_invite_organizations(self):
        """
        Only applies to GOV organizations.

        Retrieves list of organizations that need to be invited from this specific
        country.
        """
        if self.organization_type.acronym != "GOV":
            return []
        return self.__class__.objects.filter(
            government=self.government, include_in_invitation=True
        )


class BaseContact(models.Model):
    organization = None

    class Title(models.TextChoices):
        MR = "Mr.", "Mr."
        MS = "Ms.", "Ms."
        HE_MR = "H.E. Mr.", "H.E. Mr."
        HE_MS = "H.E. Ms.", "H.E. Ms."
        HON_MR = "Hon. Mr.", "Hon. Mr."
        HON_MS = "Hon. Ms.", "Hon. Ms."

    title = models.CharField(max_length=30, choices=Title.choices, blank=True)

    class LocalizedTitle(models.TextChoices):
        # English
        MR = "Mr.", "Mr."
        MS = "Ms.", "Ms."
        HE_MR = "H.E. Mr.", "H.E. Mr."
        HE_MS = "H.E. Ms.", "H.E. Ms."
        HON_MR = "Hon. Mr.", "Hon. Mr."
        HON_MS = "Hon. Ms.", "Hon. Ms."
        # French
        M = "M.", "M."
        MME = "Mme.", "Mme."
        HE_M = "H.E. M.", "H.E. M."
        HE_MME = "H.E. Mme.", "H.E. Mme."
        HON_M = "Hon. M.", "Hon. M."
        HON_MME = "Hon. Mme.", "Hon. Mme."
        # Spanish
        SR = "Sr.", "Sr."
        SRA = "Sra.", "Sra."
        HE_SR = "H.E. Sr.", "H.E. Sr."
        HE_SRA = "H.E. Sra.", "H.E. Sra."
        HON_SR = "Hon. Sr.", "Hon. Sr."
        HON_SRA = "Hon. Sra.", "Hon. Sra."

    title_localized = models.CharField(
        max_length=30,
        choices=LocalizedTitle.choices,
        blank=True,
        help_text="Localized title in French or Spanish.",
    )

    class GenderChoices(models.TextChoices):
        MALE = "Male", "Male"
        FEMALE = "Female", "Female"
        OTHER = "Other", "Other"
        NOT_DISCLOSED = "Choose not to disclose", "Choose not to disclose"

    gender = models.CharField(
        max_length=30,
        choices=GenderChoices.choices,
        blank=True,
        help_text="Contact gender.",
    )

    honorific = models.CharField(max_length=30, default="", blank=True)
    first_name = models.CharField(max_length=250, default="", blank=True)
    last_name = models.CharField(max_length=250, default="", blank=True)
    designation = models.TextField(default="", blank=True, verbose_name="Job title")
    department = models.TextField(default="", blank=True)

    class UNLanguage(models.TextChoices):
        ENGLISH = "E", "English"
        FRENCH = "F", "French"
        SPANISH = "S", "Spanish"
        ARABIC = "A", "Arabic"
        CHINESE = "C", "Chinese"
        RUSSIAN = "R", "Russian"

    primary_lang = models.CharField(
        choices=UNLanguage.choices,
        max_length=2,
        blank=True,
        default="",
        verbose_name="primary language",
    )
    second_lang = models.CharField(
        choices=UNLanguage.choices,
        max_length=2,
        blank=True,
        default="",
        verbose_name="second language",
    )
    third_lang = models.CharField(
        choices=UNLanguage.choices,
        max_length=2,
        blank=True,
        default="",
        verbose_name="third language",
    )

    phones = ArrayField(null=True, base_field=models.TextField(), blank=True)
    mobiles = ArrayField(null=True, base_field=models.TextField(), blank=True)
    faxes = ArrayField(null=True, base_field=models.TextField(), blank=True)
    emails = ArrayField(null=True, base_field=CIEmailField(), blank=True)
    email_ccs = ArrayField(null=True, base_field=CIEmailField(), blank=True)
    notes = models.TextField(default="", blank=True)
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
    org_head = models.BooleanField(
        default=False, blank=True, verbose_name="head of organization"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    has_credentials = models.BooleanField(default=False)
    credentials = EncryptedJSONField(blank=True, null=True)
    needs_visa_letter = models.BooleanField(default=False)
    passport = EncryptedJSONField(blank=True, null=True)
    passport_number = EncryptedCharField(max_length=20, blank=True, null=True)
    nationality = EncryptedCharField(max_length=50, blank=True, null=True)
    passport_date_of_issue = EncryptedDateField(blank=True, null=True)
    passport_date_of_expiry = EncryptedDateField(blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.display_name_with_org

    def _get_possible_names(self):
        yield self.full_name
        yield from self.emails or []
        yield from self.email_ccs or []
        yield from self.phones or []
        yield from self.mobiles or []
        yield from self.faxes or []

    @property
    def full_name(self):
        parts = []
        for part in (self.title, self.first_name, self.last_name):
            if part := (part or "").strip():
                parts.append(part)

        return " ".join(parts).strip()

    @property
    def display_name(self):
        name = f"(no name) ({self.pk})"
        for val in self._get_possible_names():
            if val := val.strip():
                name = val
                break
        return name

    @property
    def display_name_with_org(self):
        if self.organization:
            return f"{self.display_name} ({self.organization})"
        return self.display_name

    def clean(self):
        if not self.first_name and not self.last_name:
            raise ValidationError(
                {
                    "first_name": "At least first name or last name must be provided",
                    "last_name": "At least first name or last name must be provided",
                }
            )

        if self.has_credentials and not self.credentials:
            raise ValidationError({"credentials": "This field is required."})

        if self.needs_visa_letter:
            errors = {}
            for field in [
                "nationality",
                "passport_number",
                "passport_date_of_issue",
                "passport_date_of_expiry",
                "passport",
            ]:
                if not getattr(self, field):
                    errors[field] = "This field is required."
            if errors:
                raise ValidationError(errors)

    def clean_for_nomination(self):
        required_fields = [
            "first_name",
            "last_name",
            "designation",
            "emails",
            "organization",
        ]
        if not self.is_use_organization_address:
            required_fields.extend(["country", "city"])

        errors = {}
        for field in required_fields:
            if not getattr(self, field):
                errors[field] = "This field is required."

        if errors:
            raise ValidationError(errors)


class Contact(BaseContact):
    contact_ids = ArrayField(
        base_field=models.TextField(), null=True, blank=True, editable=False
    )
    focal_point_ids = ArrayField(
        base_field=models.IntegerField(), null=True, blank=True, editable=False
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contacts",
        verbose_name="Organization",
    )

    photo = models.ImageField(
        upload_to="contact_photos/",
        null=True,
        blank=True,
        help_text="Contact photo; initially imported from Kronos",
        storage=get_protected_storage,
    )
    photo_access_uuid = models.UUIDField(default=uuid4, null=True, editable=False)

    groups = models.ManyToManyField(
        "ContactGroup",
        blank=True,
        related_name="contacts",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["photo_access_uuid"],
                name="unique_photo_access_uuid_not_null",
                condition=models.Q(photo_access_uuid__isnull=False),
            )
        ]

    def add_to_group(self, name):
        return self.groups.add(ContactGroup.objects.get(name=name))


class PossibleDuplicateContact(DBView):
    id = models.TextField(primary_key=True)
    duplicate_fields = ArrayField(base_field=models.TextField())
    duplicate_values = ArrayField(base_field=models.TextField())
    contact_ids = ArrayField(base_field=models.IntegerField())
    contacts = models.ManyToManyField(
        Contact, through="PossibleDuplicateContactRelationship"
    )
    is_dismissed = models.BooleanField(default=False)

    @staticmethod
    def view_definition():
        fields = (
            {
                "field_name": "Name",
                "field": "concat(TRIM(LOWER(first_name)), ' ', TRIM(LOWER(last_name)))",
            },
            {
                "field_name": "Email",
                "field": "TRIM(LOWER(unnest(emails)))",
            },
        )
        query_template = """
            SELECT '%(field_name)s'                         AS duplicate_type,
                   concat('%(field_name)s: ', %(field)s)    AS duplicate_value,
                   array_agg(id ORDER BY id)::int[]         AS contact_ids
            FROM core_contact
            GROUP BY duplicate_value
            HAVING count(DISTINCT id) > 1
        """
        union_query = " UNION ALL ".join([query_template % field for field in fields])

        return (
            sql.SQL(
                """
            SELECT
                array_to_string(
                    array_agg(duplicate_value ORDER BY duplicate_value), ','
                ) AS id,
                array_agg(
                    duplicate_value ORDER BY duplicate_value
                ) AS duplicate_values,
                array_agg(
                    duplicate_type ORDER BY duplicate_type
                ) AS duplicate_fields,
                contact_ids,
                EXISTS(
                    SELECT 1 FROM core_dismissedduplicatecontact as dd
                    WHERE dd.contact_ids = duplicate_groups.contact_ids
                ) AS is_dismissed
            FROM ({}) AS duplicate_groups
            GROUP BY contact_ids
            ORDER BY id, contact_ids
        """
            )
            .format(sql.SQL(union_query))
            .as_string()
        )

    class Meta:
        managed = False


class PossibleDuplicateContactRelationship(DBView):
    contact = models.ForeignKey(Contact, on_delete=models.DO_NOTHING)
    duplicate_values = models.ForeignKey(
        PossibleDuplicateContact, on_delete=models.DO_NOTHING
    )

    @staticmethod
    def view_definition():
        return (
            sql.SQL(
                """
            SELECT
                row_number() over ()    AS id,
                unnest(contact_ids)     AS contact_id,
                subq.id                 AS duplicate_values_id
            FROM ({}) AS subq
        """
            )
            .format(sql.SQL(PossibleDuplicateContact.view_definition()))
            .as_string()
        )

    class Meta:
        managed = False


class DismissedDuplicateContact(models.Model):
    contact_ids = ArrayField(base_field=models.IntegerField(), unique=True)

    def __str__(self):
        return f"Dismissed duplicates: {self.contact_ids}"


class PossibleDuplicateOrganization(DBView):
    id = models.TextField(primary_key=True)
    duplicate_fields = ArrayField(base_field=models.TextField())
    duplicate_values = ArrayField(base_field=models.TextField())
    organization_ids = ArrayField(base_field=models.IntegerField())
    organizations = models.ManyToManyField(
        Organization, through="PossibleDuplicateOrganizationRelationship"
    )
    is_dismissed = models.BooleanField(default=False)

    @staticmethod
    def view_definition():
        fields = (
            {
                "field_name": "Name and government",
                "field": "concat(TRIM(LOWER(organization.name)), ', ', TRIM(LOWER(government.name)))",
            },
        )
        query_template = """
            SELECT '%(field_name)s'                         AS duplicate_type,
                   concat('%(field_name)s: ', %(field)s)    AS duplicate_value,
                   array_agg(id ORDER BY id)::int[]         AS organization_ids
            FROM core_organization organization
            LEFT JOIN public.core_country government
                ON organization.government_id = government.code
            LEFT JOIN public.core_country country
                ON organization.country_id = country.code
            GROUP BY duplicate_value
            HAVING count(1) > 1
        """
        union_query = " UNION ALL ".join([query_template % field for field in fields])

        return (
            sql.SQL(
                """
            SELECT
                array_to_string(
                    array_agg(duplicate_value ORDER BY duplicate_value), ','
                ) AS id,
                array_agg(
                    duplicate_value ORDER BY duplicate_value
                ) AS duplicate_values,
                array_agg(
                    duplicate_type ORDER BY duplicate_type
                ) AS duplicate_fields,
                organization_ids,
                EXISTS(
                    SELECT 1 FROM core_dismissedduplicateorganization as dd
                    WHERE dd.organization_ids = duplicate_groups.organization_ids
                ) AS is_dismissed
            FROM ({}) AS duplicate_groups
            GROUP BY organization_ids
            ORDER BY id, organization_ids
        """
            )
            .format(sql.SQL(union_query))
            .as_string()
        )

    class Meta:
        managed = False


class PossibleDuplicateOrganizationRelationship(DBView):
    organization = models.ForeignKey(Organization, on_delete=models.DO_NOTHING)
    duplicate_values = models.ForeignKey(
        PossibleDuplicateOrganization, on_delete=models.DO_NOTHING
    )

    @staticmethod
    def view_definition():
        return (
            sql.SQL(
                """
            SELECT
                row_number() over ()        AS id,
                unnest(organization_ids)    AS organization_id,
                subq.id                     AS duplicate_values_id
            FROM ({}) AS subq
        """
            )
            .format(sql.SQL(PossibleDuplicateOrganization.view_definition()))
            .as_string()
        )

    class Meta:
        managed = False


class DismissedDuplicateOrganization(models.Model):
    organization_ids = ArrayField(base_field=models.IntegerField(), unique=True)

    def __str__(self):
        return f"Dismissed duplicate organizations: {self.organization_ids}"


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

    @classmethod
    def create_from_contact(cls, main_contact: Contact, other_contact):
        obj = cls(existing_contact=main_contact)
        for field in cls._meta.get_fields():
            if field.auto_created:
                continue
            if field.name == "existing_contact":
                continue

            setattr(obj, field.name, getattr(other_contact, field.name))
        obj.save()
        return obj


class ContactGroupManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class ContactGroup(models.Model):
    name = CICharField(max_length=255, null=False, blank=False, unique=True)
    description = models.TextField(blank=True)
    predefined = models.BooleanField(default=False, editable=False)

    objects = ContactGroupManager()

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    @property
    def description_preview(self):
        return textwrap.shorten(self.description or "", 150)

    def natural_key(self):
        return (self.name,)


class ImportFocalPointsTask(TaskRQ):
    DEFAULT_VERBOSITY = 2
    TASK_QUEUE = "default"
    TASK_TIMEOUT = 300
    LOG_TO_FIELD = True
    LOG_TO_FILE = False

    @staticmethod
    def get_jobclass():
        from .jobs import ImportFocalPoints

        return ImportFocalPoints


class ImportLegacyContactsTask(TaskRQ):
    DEFAULT_VERBOSITY = 2
    TASK_QUEUE = "default"
    TASK_TIMEOUT = 300
    LOG_TO_FIELD = True
    LOG_TO_FILE = False

    clear_previous = models.BooleanField(
        default=False,
        help_text=(
            "Delete all contacts from the 'Legacy contacts' group before importing."
        ),
    )
    json_file = models.FileField(
        upload_to="import_legacy_contact_files/", storage=get_protected_storage
    )

    @staticmethod
    def get_jobclass():
        from .jobs import ImportLegacyContacts

        return ImportLegacyContacts


class ImportContactPhotosTask(TaskRQ):
    DEFAULT_VERBOSITY = 2
    TASK_QUEUE = "default"
    TASK_TIMEOUT = 1800
    LOG_TO_FIELD = True
    LOG_TO_FILE = False

    contact_ids = ArrayField(
        base_field=models.BigIntegerField(),
        null=True,
        blank=True,
        help_text=(
            "Specific Contact ids (internal, not Kronos ids) to process. "
            "Null value means all contacts are processed."
        ),
    )
    overwrite_existing = models.BooleanField(
        default=True, help_text="Overwrite any existing photos."
    )

    @staticmethod
    def get_jobclass():
        from core.jobs.contact_photos import ImportContactPhotos

        return ImportContactPhotos


class Region(models.Model):
    code = CICharField(max_length=4, primary_key=True, help_text="Up to 4 characters")
    name = CICharField(max_length=255, blank=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "regions"

    def __str__(self):
        return self.name


class Subregion(models.Model):
    code = CICharField(max_length=4, primary_key=True, help_text="Up to 4 characters")
    name = CICharField(max_length=255, blank=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "subregions"

    def __str__(self):
        return self.name
