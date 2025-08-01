# Generated by Django 5.2.1 on 2025-07-21 09:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0015_registrationrole_hide_for_nomination_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="app_store_url",
            field=models.CharField(blank=True, max_length=1024),
        ),
        migrations.AddField(
            model_name="event",
            name="event_logo",
            field=models.ImageField(
                blank=True,
                help_text="Event logo displayed on the badge",
                null=True,
                upload_to="event_logo/",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="play_store_url",
            field=models.CharField(blank=True, max_length=1024),
        ),
        migrations.AddField(
            model_name="event",
            name="wifi_name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="event",
            name="wifi_password",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
