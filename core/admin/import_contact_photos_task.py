from django.conf import settings
from django.contrib import admin

from common.model_admin import TaskAdmin
from core.models import ImportContactPhotosTask


class ImportContactPhotosTaskAdmin(TaskAdmin):
    """Import contact photos task admin."""

    def has_add_permission(self, request):
        return False


if settings.KRONOS_ENABLED:
    admin.site.register(ImportContactPhotosTask, ImportContactPhotosTaskAdmin)
