import abc
import io
from email import message_from_string
from admin_auto_filters.filters import AutocompleteFilterFactory
from django import forms
from django.contrib import admin, messages
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
    EmailAttachment,
    Email,
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
                return part.get_payload(decode=True).decode()
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
            '<iframe src="{url}" sandbox="" referrerpolicy="no-referrer"></iframe>',
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
    list_display = ["title", "description"]
    search_fields = ["title", "description"]


class EmailAdminForm(forms.ModelForm):
    def full_clean(self):
        super().full_clean()
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
    form = EmailAdminForm
    inlines = (EmailAttachmentAdmin,)
    list_display = (
        "subject",
        "created_at",
        "success_count",
        "failed_count",
        "pending_count",
    )
    ordering = ("-created_at",)
    search_fields = ("subject", "content")
    autocomplete_fields = ("recipients", "groups", "events")
    prefetch_related = ("email_history",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "recipients",
                    "groups",
                    "events",
                )
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
            None,
            {
                "fields": (
                    "recipients",
                    "groups",
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
        for contact in obj.all_recipients:
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
        return redirect(self.get_admin_list_filter_link(obj, "email_history", "email"))

    def _get_count_link(self, obj, status):
        count = len([task for task in obj.email_history.all() if task.status == status])
        return self.get_related_link(
            obj,
            "email_history",
            "email",
            text=f"{count} emails",
            extra_filters={"status__exact": status},
        )

    @admin.display(description="Success")
    def success_count(self, obj):
        return self._get_count_link(obj, "SUCCESS")

    @admin.display(description="Failed")
    def failed_count(self, obj):
        return self._get_count_link(obj, "FAILURE")

    @admin.display(description="Pending")
    def pending_count(self, obj):
        return self._get_count_link(obj, "PENDING")


@admin.register(SendEmailTask)
class SendEmailTaskAdmin(ViewEmailMixIn, TaskAdmin):
    search_fields = (
        "email__subject",
        "email__content",
        "contact__first_name",
        "contact__last_name",
        "email_to",
        "email_cc",
    )
    list_display = (
        "email",
        "contact",
        "email_to",
        "email_cc",
        "created_on",
        "duration_display",
        "status_display",
    )
    list_display_links = ("email", "contact")
    list_filter = (
        AutocompleteFilterFactory("email", "email"),
        AutocompleteFilterFactory("contact", "contact"),
        "created_on",
        "status",
    )
    ordering = ("-created_on",)
    prefetch_related = ("email", "contact", "contact__organization")
    fieldsets = [
        (
            None,
            {
                "fields": (
                    "email",
                    "contact",
                    "email_to",
                    "email_cc",
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
