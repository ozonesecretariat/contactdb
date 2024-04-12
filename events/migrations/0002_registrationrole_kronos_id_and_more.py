# Generated by Django 4.2.11 on 2024-04-12 05:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="registrationrole",
            name="kronos_id",
            field=models.IntegerField(
                blank=True, null=True, default=-1, editable=False
            ),
        ),
        migrations.AddField(
            model_name="registrationstatus",
            name="kronos_id",
            field=models.IntegerField(
                blank=True, null=True, default=-1, editable=False
            ),
        ),
    ]
