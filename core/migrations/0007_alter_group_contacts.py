# Generated by Django 4.2 on 2023-05-11 15:50

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_alter_group_contacts"),
    ]

    operations = [
        migrations.AlterField(
            model_name="group",
            name="contacts",
            field=models.ManyToManyField(blank=True, null=True, to="core.record"),
        ),
    ]
