# Generated by Django 5.2.1 on 2025-07-18 11:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0014_prioritypass_remove_registration_priority_pass_code_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="registrationrole",
            name="hide_for_nomination",
            field=models.BooleanField(
                default=False, help_text="Hide this role in the nomination form."
            ),
        ),
        migrations.AlterField(
            model_name="registration",
            name="role",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="events.registrationrole",
            ),
        ),
    ]
