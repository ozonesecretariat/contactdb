# Generated by Django 5.2.1 on 2025-06-25 12:38

from django.db import migrations, models


def forwards_func(apps, schema_editor):
    klass = apps.get_model("events", "Registration")
    db_alias = schema_editor.connection.alias

    # Migrate registration status from separate model to enum
    reverse_map = {v: k for k, v in klass.status.field.choices}
    for obj in klass.objects.using(db_alias).all():
        obj.status = reverse_map[obj.old_status.name]
        obj.save()


class Migration(migrations.Migration):
    dependencies = [
        (
            "events",
            "0010_alter_registration_date_alter_registration_is_funded_and_more",
        ),
    ]

    operations = [
        migrations.RenameField(
            model_name="registration",
            old_name="status",
            new_name="old_status",
        ),
        migrations.AddField(
            model_name="registration",
            name="status",
            field=models.CharField(
                choices=[
                    ("Nominated", "Nominated"),
                    ("Accredited", "Accredited"),
                    ("Registered", "Registered"),
                    ("Revoked", "Revoked"),
                ],
                default="Nominated",
                max_length=20,
            ),
        ),
        migrations.RunPython(forwards_func, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="registration",
            name="old_status",
        ),
        migrations.DeleteModel(
            name="RegistrationStatus",
        ),
    ]
