# Generated by Django 5.2.1 on 2025-07-25 09:06
import uuid

from django.db import migrations


def update_contact_photo_uuids(apps, schema_editor):
    Contact = apps.get_model("core", "Contact")
    contacts = Contact.objects.filter(
        photo__isnull=False, photo_access_uuid__isnull=True
    )

    for contact in contacts:
        contact.photo_access_uuid = uuid.uuid4()
        contact.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0033_alter_importcontactphotostask_contact_ids"),
    ]

    operations = [
        migrations.RunPython(
            update_contact_photo_uuids,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
