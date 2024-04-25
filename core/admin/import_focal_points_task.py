from django.contrib import admin
from common.model_admin import TaskAdmin
from core.models import ImportFocalPointsTask


@admin.register(ImportFocalPointsTask)
class ImportFocalPointsTaskAdmin(TaskAdmin):
    """Import focal points from ors.ozone.unep.org."""
