from django.contrib.postgres.fields import ArrayField
from django.db import connection, models

from core.models import Organization


class TemporaryContact(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True)
    contact_id = models.CharField(max_length=250, default="", blank=True)
    title = models.CharField(max_length=30, blank=True)
    honorific = models.CharField(max_length=30, default="", blank=True)
    respectful = models.CharField(max_length=30, default="", blank=True)
    first_name = models.CharField(max_length=250, default="", blank=True)
    last_name = models.CharField(max_length=250, default="", blank=True)
    designation = models.CharField(max_length=250, default="", blank=True)
    department = models.CharField(max_length=250, default="", blank=True)
    affiliation = models.CharField(max_length=250, default="", blank=True)
    primary_lang = models.CharField(
        max_length=100, default="", blank=True, verbose_name="Primary language"
    )
    second_lang = models.CharField(
        max_length=100, default="", blank=True, verbose_name="Second language"
    )
    third_lang = models.CharField(
        max_length=100, default="", blank=True, verbose_name="Third language"
    )
    phones = ArrayField(null=True, base_field=models.TextField(), blank=True)
    mobiles = ArrayField(null=True, base_field=models.TextField(), blank=True)
    faxes = ArrayField(null=True, base_field=models.TextField(), blank=True)
    emails = ArrayField(null=True, base_field=models.TextField(), blank=True)
    email_ccs = ArrayField(null=True, base_field=models.TextField(), blank=True)
    notes = models.TextField(default="", blank=True)
    is_in_mailing_list = models.BooleanField(default=False, blank=True)
    is_use_organization_address = models.BooleanField(default=False, blank=True)
    address = models.TextField(default="", blank=True)
    city = models.CharField(max_length=250, default="", blank=True)
    state = models.CharField(max_length=250, default="", blank=True)
    country = models.CharField(max_length=250, default="", blank=True)
    postal_code = models.CharField(max_length=250, default="", blank=True)
    birth_date = models.DateField(null=True, blank=True)
    focal_point = models.BooleanField(default=False, blank=True)
    org_head = models.BooleanField(
        default=False, blank=True, verbose_name="Head of organization"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.first_name + " " + self.last_name


def db_table_exists(table_name):
    return table_name in connection.introspection.table_names()


def create_temporary_table():
    if not db_table_exists("core_temporarycontact"):
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(TemporaryContact)
