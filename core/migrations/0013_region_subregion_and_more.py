# Generated by Django 5.2.1 on 2025-05-26 10:12


import django.core.files.storage
import django.db.models.deletion
from django.db import migrations, models

import common.citext


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0012_auto_20250523_0703"),
    ]

    operations = [
        migrations.CreateModel(
            name="Region",
            fields=[
                (
                    "code",
                    common.citext.CICharField(
                        help_text="Up to 4 characters",
                        max_length=4,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", common.citext.CICharField(blank=True, max_length=255)),
            ],
            options={
                "verbose_name_plural": "regions",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="Subregion",
            fields=[
                (
                    "code",
                    common.citext.CICharField(
                        help_text="Up to 4 characters",
                        max_length=4,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", common.citext.CICharField(blank=True, max_length=255)),
            ],
            options={
                "verbose_name_plural": "subregions",
                "ordering": ("name",),
            },
        ),
        migrations.AddField(
            model_name="country",
            name="region",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="countries",
                to="core.region",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="subregion",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="countries",
                to="core.subregion",
            ),
        ),
    ]
