import django_tables2 as tables
from core.models import Record, Group


class RecordTable(tables.Table):
    class Meta:
        model = Record
        template_name = "table.html"
        fields = (
            "id",
            "first_name",
            "last_name",
            "organization",
            "department",
            "designation",
        )
        row_attrs = {
            "onClick": lambda record: "document.location.href='/contacts/{0}';".format(
                record.id
            ),
            "data-id": lambda record: record.id,
        }


class GroupMemberTable(tables.Table):
    class Meta:
        model = Record
        template_name = "core/group_members_table.html"
        fields = (
            "id",
            "first_name",
            "last_name",
            "organization",
        )
        row_attrs = {
            "onClick": lambda record: "document.location.href='/contacts/{0}';".format(
                record.id
            )
        }


class GroupTable(tables.Table):
    class Meta:
        model = Group
        template_name = "table.html"
        fields = (
            "id",
            "name",
        )
        row_attrs = {
            "onClick": lambda record: "document.location.href='/groups/{0}'".format(
                record.id
            )
        }
