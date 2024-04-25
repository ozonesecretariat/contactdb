from django.contrib import admin, messages
from django.contrib.admin.utils import flatten_fieldsets
from django.db import IntegrityError, models
from django.db.models import ManyToManyRel, ManyToOneRel, Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.html import format_html
from common.array_field import ArrayField
from common.model_admin import ModelAdmin
from common.urls import reverse
from core.models import Contact, ResolveConflict

MERGE_FROM_PARAM = "merge_from_temp"


class ContactAdminBase(ModelAdmin):
    ordering = (
        "first_name",
        "last_name",
    )
    search_fields = (
        "first_name",
        "last_name",
        "designation",
        "department",
        "emails",
        "email_ccs",
        "organization__name",
        "organization__country__name",
    )
    autocomplete_fields = (
        "organization",
        "country",
    )
    prefetch_related = (
        "organization",
        "organization__country",
        "country",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "copy_widget",
    )

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        if temp_contact_pk := request.GET.get(MERGE_FROM_PARAM):
            extra_context["title"] = "Resolve contact conflict"
            get_object_or_404(ResolveConflict, pk=temp_contact_pk)

        return super().change_view(
            request,
            object_id,
            form_url=form_url,
            extra_context=extra_context,
        )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if temp_contact_pk := request.GET.get(MERGE_FROM_PARAM):
            get_object_or_404(ResolveConflict, pk=temp_contact_pk).delete()

    def get_queryset(self, request):
        query = super().get_queryset(request)
        if temp_contact_pk := request.GET.get(MERGE_FROM_PARAM):
            query = query.prefetch_related(
                Prefetch(
                    "conflicting_contacts",
                    ResolveConflict.objects.filter(pk=temp_contact_pk)[:1],
                    to_attr="incoming_contact",
                )
            )
        return query

    def get_readonly_fields(self, request, obj=None):
        result = super().get_readonly_fields(request, obj=obj)
        if not obj or MERGE_FROM_PARAM not in request.GET:
            return result

        return result + tuple(
            [
                "incoming_contact__" + field
                for field in flatten_fieldsets(self.get_fieldsets(request, obj))
            ]
        )

    def copy_widget(self, obj):
        return format_html(
            '<input type="button" class="copy-button" title="Copy value" value="←" />'
        )

    def __getattr__(self, name):
        if not name.startswith("incoming_contact__"):
            return super().__getattribute__(name)

        field_name = name.split("__", 1)[1]

        def wrapper(obj):
            value = getattr(obj.incoming_contact[0], field_name)
            if isinstance(value, list):
                return render_to_string(
                    "admin/widgets/array_widget_readonly.html",
                    {
                        "value": value,
                    },
                )

            if hasattr(value, "pk"):
                return format_html(
                    "<span data-pk={pk}>{value}</span>", pk=value.pk, value=value
                )

            if value is None or value == "":
                return self.get_empty_value_display()

            return value

        wrapper.short_description = field_name.replace("_", " ").title()

        return wrapper

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj=obj)
        if not obj or MERGE_FROM_PARAM not in request.GET:
            return fieldsets

        result = []
        for name, opts in fieldsets:
            # Flatten fieldset and add the copy widget and the incoming contact
            # readonly fields.
            fields = []
            for field_group in opts["fields"]:
                if not isinstance(field_group, tuple):
                    field_group = (field_group,)

                for field in field_group:
                    if field in self.readonly_fields:
                        continue
                    fields.append((field, "copy_widget", "incoming_contact__" + field))

            if not fields:
                continue

            result.append(
                (
                    name,
                    {
                        **opts,
                        "classes": ["compare"],
                        "fields": fields,
                    },
                )
            )
        return result

    def get_inlines(self, request, obj):
        if MERGE_FROM_PARAM in request.GET:
            return ()
        return super().get_inlines(request, obj)

    @admin.display(description="Sent emails")
    def email_logs(self, obj):
        return self.get_related_link(obj, "email_logs", "contact")


class MergeContacts:
    @staticmethod
    def merge_two_contacts(contact1, contact2):
        ignored_fields = {
            "id",
            "contact_id",
            "created_at",
            "updated_at",
            "possibleduplicate",
            "possibleduplicatecontact",
            "memberships",  # Through model, already cover by groups; can be ignored
            "conflicting_contacts",
        }

        has_conflict = False
        for field in Contact._meta.get_fields():
            if field.name in ignored_fields:
                continue

            if field.is_relation and getattr(field, "multiple", False):
                assert field.related_name, f"Missing related name: {field}"
                name = field.related_name
            else:
                name = field.name

            val1 = getattr(contact1, name)
            val2 = getattr(contact2, name)

            val1_empty = val1 == "" or val1 is None
            val2_empty = val2 == "" or val2 is None

            if isinstance(field, ManyToManyRel):
                for item in val2.all():
                    val1.add(item)
            elif isinstance(field, ManyToOneRel):
                rel_name = field.field.name
                for item in val2.all():
                    try:
                        setattr(item, rel_name, contact1)
                        item.save()
                    except IntegrityError:
                        continue
            elif isinstance(field, models.BooleanField):
                if val1 != val2:
                    has_conflict = True
            elif isinstance(field, ArrayField):
                if val1 is None:
                    setattr(contact1, name, [])
                    val1 = getattr(contact1, name)

                for item in val2 or []:
                    if item not in val1:
                        val1.append(item)

                setattr(contact2, name, [])
            elif isinstance(
                field,
                (
                    models.CharField,
                    models.TextField,
                    models.IntegerField,
                    models.FloatField,
                    models.DecimalField,
                    models.DateField,
                    models.ForeignKey,
                ),
            ):
                if val1 == val2:
                    # Values are equal nothing to do
                    continue
                elif val1_empty and val2_empty:
                    # Values are empty but different (e.g. "" vs None).
                    # No conflict.
                    continue
                elif val1_empty or val2_empty:
                    # Only one value is empty, use the non-empty one
                    setattr(contact1, name, val1 or val2)
                else:
                    # Values differ
                    has_conflict = True
            else:
                raise RuntimeError(f"Unexpected field type: {field}")
        contact1.save()
        contact2.save()

        conflict = None
        if has_conflict:
            conflict = ResolveConflict.create_from_contact(contact1, contact2)

        contact2.delete()

        return conflict

    def merge_action(self, request, queryset):
        all_contacts = list(queryset)
        if len(all_contacts) < 2:
            self.message_user(
                request,
                "Need at least 2 contacts to merge.",
                messages.ERROR,
            )
            return

        conflicts = []
        main_contact = all_contacts[0]
        for other_contact in all_contacts[1:]:
            if conflict := self.merge_two_contacts(main_contact, other_contact):
                conflicts.append(conflict)

        if not conflicts:
            self.message_user(
                request,
                f"{len(all_contacts)} merged successfully.",
                messages.SUCCESS,
            )
        elif len(conflicts) == 1:
            self.message_user(
                request,
                (
                    f"One contact could not be merged automatically. "
                    f"Please resolve the conflicts manually and click save."
                ),
                messages.WARNING,
            )
            return redirect(
                reverse(
                    "admin:core_contact_change",
                    kwargs={"object_id": main_contact.id},
                    query={
                        MERGE_FROM_PARAM: conflicts[0].id,
                    },
                )
            )
        else:
            self.message_user(
                request,
                (
                    f"{len(conflicts)} contacts could not be merged automatically. "
                    f"Please click below to resolve each conflict manually."
                ),
                messages.WARNING,
            )
            return redirect(
                self.get_admin_list_link(ResolveConflict, {"contact": main_contact.id})
            )
