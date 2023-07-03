import django_tables2 as tables
from core.models import Record, Group, LoadKronosEventsTask


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
            "is_secondary",
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


class LoadKronosEventsTable(tables.Table):
    class Meta:
        model = LoadKronosEventsTask
        template_name = "core/kronos_events_table.html"
        fields = (
            "job_id",
            "description",
            "created_by",
            "started_on",
            "completed_on",
            "status",
            "failure_reason",
        )


class LoadKronosParticipantsTable(tables.Table):
    class Meta:
        model = LoadKronosEventsTask
        template_name = "core/kronos_participants_table.html"
        fields = (
            "job_id",
            "description",
            "created_by",
            "started_on",
            "completed_on",
            "status",
            "failure_reason",
        )
