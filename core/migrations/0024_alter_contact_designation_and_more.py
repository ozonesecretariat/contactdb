# Generated by Django 5.2.1 on 2025-06-27 13:21

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0023_contact_credentials_contact_has_credentials_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contact",
            name="designation",
            field=models.TextField(blank=True, default="", verbose_name="Job title"),
        ),
        migrations.AlterField(
            model_name="resolveconflict",
            name="designation",
            field=models.TextField(blank=True, default="", verbose_name="Job title"),
        ),
    ]
