from django.contrib import admin

from common.model_admin import TaskAdmin
from core.models import ImportContactPhotosTask


@admin.register(ImportContactPhotosTask)
class ImportContactPhotosTaskAdmin(TaskAdmin):
    """Import contact photos task admin."""

    def has_add_permission(self, request):
        return False
