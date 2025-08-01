# Generated by Django 5.2.1 on 2025-07-07 13:25

from django.db import migrations

from common.parsing import LOCALIZED_TITLE_TO_ENGLISH


def migrate_title(apps, schema_editor):
    Contact = apps.get_model("core", "Contact")

    for contact in Contact.objects.all():
        contact.title_localized = contact.title

        if contact.title in LOCALIZED_TITLE_TO_ENGLISH:
            contact.title = LOCALIZED_TITLE_TO_ENGLISH.get(contact.title, contact.title)

        contact.save(update_fields=["title", "title_localized"])


def migrate_title_reverse(apps, schema_editor):
    Contact = apps.get_model("core", "Contact")

    for contact in Contact.objects.all():
        if contact.title_localized:
            contact.title = contact.title_localized
            contact.title_localized = ""
            contact.save(update_fields=["title", "title_localized"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0029_contact_title_localized_and_more"),
    ]

    operations = [
        migrations.RunPython(
            migrate_title,
            reverse_code=migrate_title_reverse,
        ),
    ]
