from admin_auto_filters.filters import AutocompleteFilterFactory
from auditlog.admin import LogEntryAdmin
from auditlog.filters import ResourceTypeFilter
from auditlog.models import LogEntry
from django.contrib import admin
from django.contrib.admin import ShowFacets
from rangefilter.filters import DateRangeFilterBuilder

admin.site.unregister(LogEntry)


@admin.register(LogEntry)
class CustomLogEntryAdmin(LogEntryAdmin):
    list_per_page = 20
    show_facets = ShowFacets.NEVER

    search_fields = [
        "object_repr",
        "object_id",
    ]

    list_filter = [
        "action",
        ResourceTypeFilter,
        AutocompleteFilterFactory("user", "actor"),
        ("timestamp", DateRangeFilterBuilder()),
    ]
