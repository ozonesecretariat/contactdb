from django.contrib import admin
from django_task.admin import TaskAdmin

from core.models import SendMailTask


@admin.register(SendMailTask)
class SendMailTaskAdmin(TaskAdmin):
    search_fields = [
        "subject",
        "recipient",
    ]
    list_display = [
        "__str__",
        "recipient",
        "subject",
        "created_on",
        "duration_display",
        "status_display",
    ]
    ordering = ("-created_on",)

    def get_list_display(self, request):
        fields = super().get_list_display(request)
        fields.remove("log_link_display")
        return fields
