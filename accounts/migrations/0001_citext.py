from django.db import migrations
from django.contrib.postgres.operations import CITextExtension


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        CITextExtension(),
    ]
