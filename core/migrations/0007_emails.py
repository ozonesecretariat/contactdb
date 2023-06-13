# Generated by Django 4.2.1 on 2023-05-26 09:02

import ckeditor.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_record_focal_point_record_honorific_record_org_head_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Emails",
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
                ("title", models.TextField()),
                ("content", ckeditor.fields.RichTextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "cc",
                    models.ManyToManyField(
                        related_name="cc", to="core.record", verbose_name="CC"
                    ),
                ),
                (
                    "recipients",
                    models.ManyToManyField(related_name="recipients", to="core.record"),
                ),
            ],
            options={
                "verbose_name_plural": "e-mails",
            },
        ),
    ]