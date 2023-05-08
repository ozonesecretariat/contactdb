import django_tables2 as tables
from core.models import Record


class RecordTable(tables.Table):
    class Meta:
        model = Record
        template_name = "records_table.html"
        fields = (
            "id",
            "first_name",
            "last_name",
            "organization",
            "department",
            "designation",
        )
