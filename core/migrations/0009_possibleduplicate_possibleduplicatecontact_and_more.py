# Generated by Django 4.2.11 on 2024-04-24 07:49

import common.array_field
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_remove_contact_contact_id_contact_contact_ids_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="PossibleDuplicate",
            fields=[
                ("id", models.TextField(primary_key=True, serialize=False)),
                (
                    "duplicate_fields",
                    common.array_field.ArrayField(
                        base_field=models.TextField(), size=None
                    ),
                ),
                (
                    "duplicate_values",
                    common.array_field.ArrayField(
                        base_field=models.TextField(), size=None
                    ),
                ),
                (
                    "contact_ids",
                    common.array_field.ArrayField(
                        base_field=models.IntegerField(), size=None
                    ),
                ),
                ("is_dismissed", models.BooleanField(default=False)),
            ],
            options={
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="PossibleDuplicateContact",
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
            ],
            options={
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="DismissedDuplicate",
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
                    "contact_ids",
                    common.array_field.ArrayField(
                        base_field=models.IntegerField(), size=None, unique=True
                    ),
                ),
            ],
        ),
    ]
