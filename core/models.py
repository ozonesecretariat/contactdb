import textwrap

import pycountry
from django.core.exceptions import ValidationError
from django.db import models
from django_db_views.db_view import DBView
from django_task.models import TaskRQ

from common.array_field import ArrayField
from common.citext import CICharField
from common.model import KronosId


class Country(models.Model):
    code = CICharField(max_length=2, primary_key=True)
    name = CICharField(max_length=255, null=True, blank=True)
    official_name = CICharField(max_length=255, null=True, blank=True)

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
            except (AttributeError, LookupError):
                pass
        if not self.official_name:
            try:
                self.official_name = pycountry.countries.get(
                    alpha_2=self.code
                ).official_name
            except (AttributeError, LookupError):
                pass


class OrganizationType(models.Model):
    organization_type_id = KronosId()
    acronym = CICharField(max_length=50, primary_key=True)
    title = CICharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ("title",)

    def __str__(self):
        return f"{self.title} ({self.acronym})"


class Organization(models.Model):
    organization_id = KronosId()
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
    org_head = models.BooleanField(
        default=False, blank=True, verbose_name="head of organization"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        if self.organization:
            return f"{self.full_name} ({self.organization})"
        return self.full_name

    @property
    def full_name(self):
        return " ".join([self.title, self.first_name, self.last_name]).strip()

    def clean(self):
        if not self.first_name and not self.last_name:
            raise ValidationError(
                {
                    "first_name": "At least first name or last name must be provided",
                    "last_name": "At least first name or last name must be provided",
                }
            )


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
    )


class PossibleDuplicate(DBView):
    id = models.TextField(primary_key=True)
    duplicate_fields = ArrayField(base_field=models.TextField())
    duplicate_values = ArrayField(base_field=models.TextField())
    contact_ids = ArrayField(base_field=models.IntegerField())
    contacts = models.ManyToManyField(Contact, through="PossibleDuplicateContact")
    is_dismissed = models.BooleanField(default=False)

    @staticmethod
    def view_definition():
        fields = (
            {
                "field_name": "Name",
                "field": "concat(first_name, ' ', last_name)",
            },
            {
                "field_name": "Email",
                "field": "unnest(emails)",
            },
            {
                "field_name": "Email Cc",
                "field": "unnest(email_ccs)",
            },
            {
                "field_name": "Phone",
                "field": "unnest(phones)",
            },
            {
                "field_name": "Mobile",
                "field": "unnest(mobiles)",
            },
            {
                "field_name": "Fax",
                "field": "unnest(faxes)",
            },
        )
        query_template = """
            SELECT '%(field_name)s'                         AS duplicate_type, 
                   concat('%(field_name)s: ', %(field)s)    AS duplicate_value,
                   array_agg(id ORDER BY id)::int[]         AS contact_ids
            FROM core_contact
            GROUP BY duplicate_value
            HAVING count(1) > 1
        """
        union_query = " UNION ALL ".join([query_template % field for field in fields])

        return f"""
            SELECT 
                array_to_string(array_agg(duplicate_value), ',')    AS id,  
                array_agg(duplicate_value)                          AS duplicate_values,  
                array_agg(duplicate_type)                           AS duplicate_fields,  
                contact_ids                                         AS contact_ids,
                EXISTS(
                    SELECT 1 FROM core_dismissedduplicate 
                    WHERE core_dismissedduplicate.contact_ids = duplicate_groups.contact_ids
                )                                                   AS is_dismissed
            FROM ({union_query}) AS duplicate_groups
            GROUP BY contact_ids
            ORDER BY id, contact_ids
        """

    class Meta:
        managed = False


class PossibleDuplicateContact(DBView):
    contact = models.ForeignKey(Contact, on_delete=models.DO_NOTHING)
    duplicate_values = models.ForeignKey(PossibleDuplicate, on_delete=models.DO_NOTHING)

    @staticmethod
    def view_definition():
        return f"""
            SELECT 
                row_number() over ()    AS id,
                unnest(contact_ids)     AS contact_id,  
                subq.id                 AS duplicate_values_id
            FROM ({PossibleDuplicate.view_definition()}) AS subq
        """

    class Meta:
        managed = False


class DismissedDuplicate(models.Model):
    contact_ids = ArrayField(base_field=models.IntegerField(), unique=True)


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
    description = models.TextField(blank=True, null=True)
    contacts = models.ManyToManyField(
        Contact,
        blank=True,
        through="GroupMembership",
        related_name="groups",
    )
    predefined = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ContactGroupManager()

    def __str__(self):
        return self.name

    @property
    def description_preview(self):
        return textwrap.shorten(self.description or "", 150)

    def natural_key(self):
        return (self.name,)


class GroupMembership(models.Model):
    group = models.ForeignKey(ContactGroup, on_delete=models.CASCADE)
    contact = models.ForeignKey(
        Contact, on_delete=models.CASCADE, related_name="memberships"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("group", "contact")
