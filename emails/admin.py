import abc
import io
import textwrap
from email import message_from_string

from admin_auto_filters.filters import AutocompleteFilter, AutocompleteFilterFactory
from django import forms
from django.contrib import admin, messages
from django.db.models import Q
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html
from django.views.decorators.clickjacking import xframe_options_sameorigin

from common.model_admin import ModelAdmin, TaskAdmin
from common.urls import reverse
from emails.models import (
    Email,
    EmailAttachment,
    EmailTemplate,
    SendEmailTask,
)


class ViewEmailMixIn:
    @abc.abstractmethod
    def get_email_object(self, obj) -> Email:
        raise NotImplementedError

    @abc.abstractmethod
    def get_msg_source(self, obj) -> str:
        raise NotImplementedError

    def get_msg(self, obj):
        return message_from_string(self.get_msg_source(obj))

    def get_msg_part(self, obj, content_type):
        msg = self.get_msg(obj)
        for part in msg.walk():
            if part.get_content_type() == content_type:
                return part.get_payload()
        return ""

    def get_urls(self):
        urls = super().get_urls()
        return [
            path(
                "<str:object_id>/view-email/",
                self.admin_site.admin_view(self.email_html_view),
                {},
                name="%s_%s_view_email" % self.opt_info,
            ),
            path(
                "<str:object_id>/download-email/",
                self.admin_site.admin_view(self.download_email_view),
                {},
                name="%s_%s_download_email" % self.opt_info,
            ),
        ] + urls

    @xframe_options_sameorigin
    def email_html_view(self, request, object_id):
        obj = self.get_object(request, object_id)
        if not self.has_view_permission(request, obj):
            return HttpResponseForbidden()

        return TemplateResponse(
            request,
            "admin/emails/email_html_view.html",
            context={
                "opts": self.opts,
                "html_content": self.get_msg_part(obj, "text/html"),
            },
        )

    def download_email_view(self, request, object_id):
        obj = self.get_object(request, object_id)
        if not self.has_view_permission(request, obj):
            return HttpResponseForbidden()

        msg_source = self.get_msg_source(obj)

        stream = io.BytesIO(msg_source.encode())
        return FileResponse(
            stream,
            as_attachment=True,
            filename=f"{object_id}.eml",
            content_type="message/rfc822",
        )

    @admin.display(description="Download")
    def download_email(self, obj):
        return format_html(
            "<a href={url} download>Download</a>",
            url=reverse(
                "admin:%s_%s_download_email" % self.opt_info,
                kwargs={"object_id": str(obj.id)},
            ),
        )

    @admin.display(description="Email preview")
    def email_preview(self, obj):
        return format_html(
            '<iframe src="{url}" referrerpolicy="no-referrer"></iframe>',
            url=reverse(
                "admin:%s_%s_view_email" % self.opt_info,
                kwargs={"object_id": str(obj.id)},
            )
            + "?iframe=true",
        )

    @admin.display(description="Email plaintext")
    def email_plaintext(self, obj):
        return format_html(
            "<pre>{text}</pre>",
            text=self.get_msg_part(obj, "text/plain"),
        )

    @admin.display(description="Source")
    def email_source(self, obj):
        return format_html(
            "<pre>{text}</pre>",
            text=self.get_msg_source(obj),
        )

    @admin.display(description="Email attachments")
    def email_attachments(self, obj):
        return render_to_string(
            "admin/emails/attachments.html",
            {
                "email": self.get_email_object(obj),
            },
        )


class CKEditorTemplatesBase(ModelAdmin):
    def get_extra_context(self, extra_context=None):
        templates = []
        for template in EmailTemplate.objects.all():
            templates.append(
                {
                    "title": template.title,
                    # TODO: Add image
                    # "image": "template1.gif",
                    "description": template.description,
                    "html": template.content,
                }
            )

        extra_context = extra_context or {}
        extra_context.setdefault("json_scripts", {"ckeditor-templates": templates})
        return extra_context

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return super().change_view(
            request,
            object_id,
            form_url=form_url,
            extra_context=self.get_extra_context(extra_context),
        )

    def add_view(self, request, form_url="", extra_context=None):
        return super().add_view(
            request,
            form_url=form_url,
            extra_context=self.get_extra_context(extra_context),
        )


@admin.register(EmailTemplate)
class EmailTemplateAdmin(CKEditorTemplatesBase):
    """Define email templates for later reuse when composing new emails."""

    list_display = ["title", "description"]
    search_fields = ["title", "description"]


class EmailAdminForm(forms.ModelForm):
    def full_clean(self):
        super().full_clean()
        if not self.is_bound:
            return

        if (
            not self.cleaned_data["recipients"].exists()
            and not self.cleaned_data["groups"].exists()
            and not self.cleaned_data["events"].exists()
        ):
            msg = "At least one recipient, group or event must be specified"
            self.add_error("events", msg)
            self.add_error("groups", msg)
            self.add_error("recipients", msg)


class EmailAttachmentForm(forms.ModelForm):
    def save(self, commit=True):
        if not self.instance.name:
            self.instance.name = self.cleaned_data["file"].name

        return super().save(commit=True)


class EmailAttachmentAdmin(admin.TabularInline):
    model = EmailAttachment
    form = EmailAttachmentForm
    extra = 0


@admin.register(Email)
class EmailAdmin(ViewEmailMixIn, CKEditorTemplatesBase):
    """Send emails in bulk to a contact list, groups of contacts or all registered
    event participants.
    """

    form = EmailAdminForm
    inlines = (EmailAttachmentAdmin,)
    list_display = (
        "subject",
        "created_at",
        "sent_count",
        "success_count",
        "failed_count",
        "pending_count",
    )
    ordering = ("-created_at",)
    search_fields = ("subject", "content")
    autocomplete_fields = (
        "recipients",
        "cc_recipients",
        "bcc_recipients",
        "groups",
        "cc_groups",
        "bcc_groups",
        "events",
    )
    prefetch_related = ("email_logs",)
    fieldsets = (
        (
            "To",
            {
                "description": (
                    "One individual mail will be sent to each of the selected "
                    "contacts, contact group members and event participants. "
                    "Contacts will not see addresses from this list other than "
                    "their own."
                ),
                "fields": (
                    "recipients",
                    "groups",
                    "events",
                ),
            },
        ),
        (
            "Cc",
            {
                "description": (
                    "Include all the selected contacts and contact group members in "
                    "the CC of this email. All addresses will be included in all "
                    "emails and visible to all recipients."
                ),
                "fields": (
                    "cc_recipients",
                    "cc_groups",
                ),
            },
        ),
        (
            "Bcc",
            {
                "description": (
                    "Send a blind carbon copy for all the emails sent to the selected "
                    "contacts and contact group members. These addresses will not be "
                    "visible to any other recipients."
                ),
                "fields": (
                    "bcc_recipients",
                    "bcc_groups",
                ),
            },
        ),
        (
            "Email content",
            {
                "fields": (
                    "subject",
                    "content",
                )
            },
        ),
    )
    view_fieldsets = (
        (
            "To",
            {
                "fields": (
                    "recipients_links",
                    "groups_links",
                    "events_links",
                )
            },
        ),
        (
            "Cc",
            {
                "fields": (
                    "cc_recipients_links",
                    "cc_groups_links",
                )
            },
        ),
        (
            "Bcc",
            {
                "fields": (
                    "bcc_recipients_links",
                    "bcc_groups_links",
                )
            },
        ),
        (
            "Email preview",
            {
                "description": (
                    "Preview may differ depending on the email client used to "
                    "display the email."
                ),
                "fields": (
                    "subject",
                    "email_preview",
                    "email_plaintext",
                    "email_attachments",
                    "created_at",
                ),
            },
        ),
    )

    def get_email_object(self, obj: Email) -> Email:
        return obj

    def get_msg_source(self, obj: Email) -> str:
        return obj.build_email().message().as_string()

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_inlines(self, request, obj):
        if obj:
            return ()
        return super().get_inlines(request, obj)

    def response_post_save_add(self, request, obj):
        tasks = []
        for contact in obj.all_to_contacts:
            task = SendEmailTask.objects.create(
                email=obj, contact=contact, created_by=request.user
            )
            task.run(is_async=True)
            tasks.append(task)

        self.message_user(
            request,
            f"{len(tasks)} emails scheduled for sending",
            level=messages.SUCCESS,
        )
        return redirect(self.get_admin_list_filter_link(obj, "email_logs", "email"))

    def _get_count_link(self, obj, status=None):
        extra_filters = {}
        if status:
            extra_filters["status__exact"] = status
            count = len(
                [task for task in obj.email_logs.all() if task.status == status]
            )
        else:
            count = len(obj.email_logs.all())

        return self.get_related_link(
            obj,
            "email_logs",
            "email",
            text=f"{count} emails",
            extra_filters=extra_filters,
        )

    @admin.display(description="Total")
    def sent_count(self, obj):
        return self._get_count_link(obj)

    @admin.display(description="Success")
    def success_count(self, obj):
        return self._get_count_link(obj, "SUCCESS")

    @admin.display(description="Failed")
    def failed_count(self, obj):
        return self._get_count_link(obj, "FAILURE")

    @admin.display(description="Pending")
    def pending_count(self, obj):
        return self._get_count_link(obj, "PENDING")

    @admin.display(description="Recipients")
    def recipients_links(self, obj):
        return self.get_m2m_links(obj.recipients.all())

    @admin.display(description="Groups")
    def groups_links(self, obj):
        return self.get_m2m_links(obj.groups.all())

    @admin.display(description="Events")
    def events_links(self, obj):
        return self.get_m2m_links(obj.events.all())

    @admin.display(description="Cc recipients")
    def cc_recipients_links(self, obj):
        return self.get_m2m_links(obj.cc_recipients.all())

    @admin.display(description="Cc groups")
    def cc_groups_links(self, obj):
        return self.get_m2m_links(obj.cc_groups.all())

    @admin.display(description="Bcc recipients")
    def bcc_recipients_links(self, obj):
        return self.get_m2m_links(obj.bcc_recipients.all())

    @admin.display(description="Bcc groups")
    def bcc_groups_links(self, obj):
        return self.get_m2m_links(obj.bcc_groups.all())


class ContactAutocompleteFilter(AutocompleteFilter):
    title = "contact"
    field_name = "contact"
    parameter_name = "any_contact"

    def queryset(self, request, queryset):
        if val := self.value():
            return queryset.filter(
                Q(contact__pk__exact=val)
                | Q(cc_contacts__pk__exact=val)
                | Q(bcc_contacts__pk__exact=val)
            ).distinct()
        return queryset


@admin.register(SendEmailTask)
class SendEmailTaskAdmin(ViewEmailMixIn, TaskAdmin):
    """View sent email logs."""

    search_fields = (
        "email__subject",
        "email__content",
        "contact__first_name__unaccent",
        "contact__last_name__unaccent",
        "cc_contacts__first_name__unaccent",
        "bcc_contacts__first_name__unaccent",
        "email_to",
        "email_cc",
        "email_bcc",
    )
    list_display = (
        "email",
        "contact_link",
        "email_to_preview",
        "email_cc_preview",
        "email_bcc_preview",
        "created_on",
        "duration_display",
        "status_display",
    )
    list_display_links = ("email", "contact")
    list_filter = (
        AutocompleteFilterFactory("email", "email"),
        ContactAutocompleteFilter,
        AutocompleteFilterFactory("to", "contact"),
        AutocompleteFilterFactory("cc", "cc_contacts"),
        AutocompleteFilterFactory("bcc", "bcc_contacts"),
        "created_on",
        "status",
    )
    ordering = ("-created_on",)
    prefetch_related = (
        "email",
        "contact",
        "contact__organization",
        "cc_contacts__organization",
        "bcc_contacts__organization",
    )
    fieldsets = [
        (
            None,
            {
                "fields": (
                    "email",
                    "contact",
                    "cc_contacts_links",
                    "bcc_contacts_links",
                    "email_to",
                    "email_cc",
                    "email_bcc",
                    "download_email",
                )
            },
        ),
        (
            "Email preview",
            {
                "description": (
                    "Actual email may differ depending on the email client used to "
                    "display the email."
                ),
                "classes": ["collapse"],
                "fields": (
                    "email_preview",
                    "email_plaintext",
                    "email_attachments",
                ),
            },
        ),
        (
            "View email source",
            {
                "classes": ["collapse"],
                "fields": ("email_source",),
            },
        ),
        (
            "Task Details",
            {
                "fields": (
                    "description",
                    "created_on",
                    "created_by",
                    "started_on",
                    "completed_on",
                    "job_id",
                    "status",
                    "failure_reason",
                    "progress",
                    "mode",
                    "log_text",
                ),
            },
        ),
    ]

    def get_msg_source(self, obj) -> str:
        return obj.sent_email

    def get_email_object(self, obj) -> Email:
        return obj.email

    def get_fieldsets(self, request, obj=None):
        return self.fieldsets

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    @admin.display(description="Contact", ordering="contact")
    def contact_link(self, obj):
        return self.get_object_display_link(obj.contact)

    @admin.display(description="Cc contacts")
    def cc_contacts_links(self, obj):
        return self.get_m2m_links(obj.cc_contacts.all())

    @admin.display(description="Bcc contacts")
    def bcc_contacts_links(self, obj):
        return self.get_m2m_links(obj.bcc_contacts.all())

    @admin.display(description="Email To", ordering="email_to")
    def email_to_preview(self, obj):
        return textwrap.shorten(", ".join(obj.email_to or []), 100)

    @admin.display(description="Email Cc", ordering="email_cc")
    def email_cc_preview(self, obj):
        return textwrap.shorten(", ".join(obj.email_cc or []), 100)

    @admin.display(description="Email Bcc", ordering="email_bcc")
    def email_bcc_preview(self, obj):
        return textwrap.shorten(", ".join(obj.email_bcc or []), 100)
