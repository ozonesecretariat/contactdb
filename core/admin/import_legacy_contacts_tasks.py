from django.contrib import admin

from common.model_admin import TaskAdmin
from core.models import ImportLegacyContactsTask


@admin.register(ImportLegacyContactsTask)
class ImportLegacyContactsTaskAdmin(TaskAdmin):
    """Import legacy contacts from a json file."""
