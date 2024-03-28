import io
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
from django_task.utils import get_object_by_uuid_or_404

from common.model_admin import ModelAdmin, TaskAdmin
from common.urls import reverse
from emails.models import (
    EmailAttachment,
    Email,
    EmailTemplate,
    SendEmailTask,
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
        ):
            msg = "At least one recipient or group must be specified"
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
class EmailAdmin(CKEditorTemplatesBase):
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
    autocomplete_fields = ("recipients", "groups")
    prefetch_related = ("email_history",)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

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
            f"{len(tasks)} tasks scheduled",
            level=messages.SUCCESS,
        )
        return redirect(self.get_admin_list_filter_link(obj, "email_history", "email"))

    def _get_count_link(self, obj, status):
        return self.get_related_link(
            obj,
            "email_history",
            "email",
            text=len(
                [task for task in obj.email_history.all() if task.status == status]
            ),
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
class SendEmailTaskAdmin(TaskAdmin):
    search_fields = (
        "email__title",
        "email__content",
        "contact__first_name",
        "contact__last_name",
        "contact__emails",
        "contact__email_ccs",
    )
    list_display = (
        "email",
        "contact",
        "contact_emails",
        "contact_email_ccs",
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
                    "download_email",
                )
            },
        ),
        (
            "Email content preview",
            {
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

    def get_fieldsets(self, request, obj=None):
        return self.fieldsets

    @admin.display(description="To")
    def contact_emails(self, obj):
        return obj.contact.emails

    @admin.display(description="Cc")
    def contact_email_ccs(self, obj):
        return obj.contact.email_ccs

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        urls = super().get_urls()
        return [
            path(
                "<uuid:object_id>/view-email/",
                self.admin_site.admin_view(self.sent_email_view),
                {},
                name="%s_%s_view_email" % self.opt_info,
            ),
            path(
                "<uuid:object_id>/download-email/",
                self.admin_site.admin_view(self.download_email_view),
                {},
                name="%s_%s_download_email" % self.opt_info,
            ),
        ] + urls

    @xframe_options_sameorigin
    def sent_email_view(self, request, object_id):
        obj = get_object_by_uuid_or_404(self.model, object_id)
        if not self.has_view_permission(request, obj):
            return HttpResponseForbidden()

        return TemplateResponse(
            request,
            self.get_admin_template("sent_email_view.html"),
            context={
                "opts": self.opts,
                "obj": obj,
            },
        )

    def download_email_view(self, request, object_id):
        obj = get_object_by_uuid_or_404(self.model, object_id)
        if not self.has_view_permission(request, obj):
            return HttpResponseForbidden()

        stream = io.BytesIO(obj.sent_email.encode())
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
        return format_html("<pre>{text}</pre>", text=obj.text_plain)

    @admin.display(description="Source")
    def email_source(self, obj):
        return format_html("<pre>{text}</pre>", text=obj.sent_email)

    @admin.display(description="Email attachments")
    def email_attachments(self, obj):
        return render_to_string(
            self.get_admin_template("attachments.html"),
            {
                "obj": obj,
            },
        )
