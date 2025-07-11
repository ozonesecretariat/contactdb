import abc
import io
import textwrap
from email import message_from_string
from urllib.parse import urlencode

from admin_auto_filters.filters import AutocompleteFilter, AutocompleteFilterFactory
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Count, Q
from django.http import FileResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html
from django.views.decorators.clickjacking import xframe_options_sameorigin

from common.auto_complete_multiple import AutocompleteFilterMultipleFactory
from common.model_admin import ModelAdmin, TaskAdmin
from common.urls import reverse
from emails.models import (
    Email,
    EmailAttachment,
    EmailTemplate,
    InvitationEmail,
    SendEmailTask,
)
from emails.services import get_organization_recipients
from emails.validators import find_placeholders
from events.models import EventInvitation


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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Overriding the CKEditor widget for the `content` field; this allows us
        # to use custom placeholders for different email types.
        if "content" in self.fields:
            self.fields["content"].widget = CKEditorUploadingWidget(
                config_name="email_editor"
            )

    def clean_content(self):
        """Validate that only specific placeholders are used in "normal" emails."""
        content = self.cleaned_data.get("content")
        if not content:
            return content

        # Check if any invalid placeholders are used
        used_placeholders = find_placeholders(content)
        valid_placeholders = set(settings.CKEDITOR_CONTACT_PLACEHOLDERS.keys())
        invalid_placeholders = used_placeholders - valid_placeholders

        if invalid_placeholders:
            raise forms.ValidationError(
                f"The following placeholders cannot be used in emails: "
                f"{', '.join(invalid_placeholders)}. "
                f"Valid placeholders are: {', '.join(valid_placeholders)}."
            )

        return content

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


class BaseEmailAdmin(ViewEmailMixIn, CKEditorTemplatesBase):
    """
    Base admin class for common functionality in all email-related admins
    (e.g. base emails and event invitations).
    """

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

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                sent_count=Count("email_logs"),
                success_count=Count("id", filter=Q(email_logs__status="SUCCESS")),
                failure_count=Count("id", filter=Q(email_logs__status="FAILURE")),
                pending_count=Count("id", filter=Q(email_logs__status="PENDING")),
            )
        )

    def get_email_object(self, obj: Email) -> Email:
        return obj

    def get_msg_source(self, obj: Email) -> str:
        return obj.build_email().message().as_string()

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def _get_count_link(self, obj, status=None):
        extra_filters = {}
        if status:
            extra_filters["status__exact"] = status
            count = getattr(obj, f"{status.lower()}_count", None)
        else:
            count = obj.sent_count

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


@admin.register(Email)
class EmailAdmin(BaseEmailAdmin):
    """
    Send emails in bulk to a contact list, groups of contacts or all registered
    event participants.
    """

    form = EmailAdminForm
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

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .exclude(email_type=Email.EmailTypeChoices.EVENT_INVITE)
        )

    def get_inlines(self, request, obj):
        if obj:
            return ()
        return super().get_inlines(request, obj)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def response_post_save_add(self, request, obj: Email):
        tasks = obj.queue_emails()
        self.message_user(
            request,
            f"{len(tasks)} emails scheduled for sending",
            level=messages.SUCCESS,
        )
        return redirect(self.get_admin_list_filter_link(obj, "email_logs", "email"))

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


class InvitationEmailForm(forms.ModelForm):
    class Meta:
        model = InvitationEmail
        fields = [
            "organization_types",
            "organizations",
            "events",
            "event_group",
            "cc_recipients",
            "bcc_recipients",
            "subject",
            "content",
            "is_reminder",
            "original_email",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Overriding the CKEditor widget for the `content` field; this allows us
        # to use custom placeholders for different email types.
        if "content" in self.fields:
            self.fields["content"].widget = CKEditorUploadingWidget(
                config_name="invitation_editor"
            )

    def clean(self):
        cleaned_data = super().clean()
        events = cleaned_data.get("events")
        event_group = cleaned_data.get("event_group")
        organization_types = cleaned_data.get("organization_types")
        organizations = cleaned_data.get("organizations")

        if events and event_group:
            raise forms.ValidationError("Cannot select both events and event groups")

        if not events and not event_group:
            raise forms.ValidationError("Must select either an event or an event group")

        if events and events.count() > 1:
            raise forms.ValidationError("Only one event can be selected")

        if (not organization_types or not organization_types.exists()) and (
            not organizations or not organizations.exists()
        ):
            raise forms.ValidationError(
                "Must select at lease one organization type or one organization "
                "(but not both)."
            )

        if (
            organization_types
            and organization_types.exists()
            and organizations
            and organizations.exists()
        ):
            raise forms.ValidationError(
                "Cannot choose both organization types and specific organizations"
            )

        return cleaned_data

    def clean_events(self):
        events = self.cleaned_data.get("events")
        if events and events.count() > 1:
            raise forms.ValidationError(
                "Only one event can be selected for invitation emails"
            )
        return events

    def clean_content(self):
        """Validate that only invitation placeholders are used in invitation emails."""
        content = self.cleaned_data.get("content")
        if not content:
            return content

        # Check if any invalid placeholders are used
        used_placeholders = find_placeholders(content)
        valid_placeholders = set(settings.CKEDITOR_INVITATION_PLACEHOLDERS.keys())
        invalid_placeholders = used_placeholders - valid_placeholders

        if invalid_placeholders:
            raise forms.ValidationError(
                f"The following placeholders cannot be used in invitation emails: "
                f"{', '.join(invalid_placeholders)}. "
                f"Valid placeholders are: {', '.join(valid_placeholders)}."
            )

        return content


@admin.register(InvitationEmail)
class InvitationEmailAdmin(BaseEmailAdmin):
    """
    Admin class for viewing and sending invitations emails.
    """

    form = InvitationEmailForm

    list_display = BaseEmailAdmin.list_display + (
        "is_reminder",
        "original_email_link",
        "reminder_count",
    )

    list_filter = (
        AutocompleteFilterFactory("events", "events"),
        AutocompleteFilterFactory("event group", "event_group"),
        AutocompleteFilterMultipleFactory("organization types", "organization_types"),
        "is_reminder",
        "original_email",
        "created_at",
    )

    # is_reminder and original_email should be readonly for both invitation and reminders
    # This ensures consistent behaviour and separation of concerns.
    readonly_fields = ("is_reminder_display", "original_email_display")

    autocomplete_fields = (
        "organization_types",
        "organizations",
        "events",
        "event_group",
        "cc_recipients",
        "bcc_recipients",
    )
    search_fields = BaseEmailAdmin.search_fields + (
        "cc_recipients__first_name__unaccent",
        "cc_recipients__last_name__unaccent",
        "bcc_recipients__first_name__unaccent",
        "bcc_recipients__last_name__unaccent",
        "event_group__name__unaccent",
        "events__title__unaccent",
    )
    fieldsets = (
        (
            "Recipients",
            {
                "description": (
                    "Select organization types or organizations to send invitations. "
                    "Only one of organization types or organizations can be selected. "
                    "Primary contacts will be set as To recipients, "
                    "secondary contacts as CC."
                ),
                "fields": ("organization_types", "organizations"),
            },
        ),
        (
            "Additional Recipients",
            {
                "description": (
                    "These contacts will be added to all invitation emails that are sent."
                ),
                "fields": (
                    "cc_recipients",
                    "bcc_recipients",
                ),
            },
        ),
        (
            "Events",
            {
                "description": ("Send invitation emails for this specific event."),
                "fields": (
                    "events",
                    "event_group",
                ),
            },
        ),
        (
            "Email content",
            {
                "description": (
                    "For event invitations, the [[invitation_link]] placeholder "
                    "will automatically insert the correct link for each "
                    "organization and event. "
                    "The [[party]] placeholder will automatically be replaced with "
                    "the party name."
                ),
                "fields": (
                    "is_reminder_display",
                    "original_email_display",
                    "subject",
                    "content",
                ),
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(email_type=Email.EmailTypeChoices.EVENT_INVITE)
            .select_related("original_email")
            .prefetch_related("reminder_emails")
        )

    def save_model(self, request, obj, form, change):
        obj.email_type = Email.EmailTypeChoices.EVENT_INVITE
        super().save_model(request, obj, form, change)

    def get_urls(self):
        urls = super().get_urls()
        return [
            path(
                "<path:object_id>/send-reminder/",
                self.admin_site.admin_view(self.send_reminder_view),
                name="%s_%s_send_reminder" % self.opt_info,
            ),
        ] + urls

    @admin.display(boolean=True, description="Is Reminder")
    def is_reminder_display(self, obj):
        if obj is None or obj.pk is None:
            return (
                "is_reminder" in self.request.GET
                and "original_email_id" in self.request.GET
            )
        return obj.is_reminder

    @admin.display(description="Original Email")
    def original_email_display(self, obj):
        original_email_id = None
        if obj is None or obj.pk is None:
            original_email_id = self.request.GET.get("original_email_id")
        elif obj.original_email:
            original_email_id = obj.original_email.pk
        original_email = InvitationEmail.objects.filter(id=original_email_id).first()
        if original_email:
            url = reverse(
                "admin:emails_invitationemail_change", args=[original_email.pk]
            )
            return format_html('<a href="{}">{}</a>', url, original_email.subject)
        return "-"

    def get_form(self, request, obj=None, **kwargs):
        """Store request for use in display methods"""
        self.request = request
        return super().get_form(request, obj, **kwargs)

    def get_changeform_initial_data(self, request):
        """
        Provides initial data for reminders in the changeform
        (basically pre-populating all fields that can be pre-populated).
        """
        initial = super().get_changeform_initial_data(request)

        # Check if this is a reminder being created
        if "is_reminder" in request.GET and "original_email_id" in request.GET:
            original_email_id = request.GET.get("original_email_id")

            try:
                original_email = InvitationEmail.objects.get(id=original_email_id)

                # Count reminders already sent for this invitation email
                reminder_count = original_email.reminder_emails.count()

                # Preserve initial organizations, organization types and events
                org_types = original_email.organization_types.all()
                initial["organization_types"] = [org_type.pk for org_type in org_types]

                organizations = original_email.organizations.all()
                initial["organizations"] = [org.pk for org in organizations]

                events = list(original_email.events.all())
                if events:
                    initial["events"] = [event.pk for event in events]
                if original_email.event_group:
                    initial["event_group"] = original_email.event_group.pk

                initial["is_reminder"] = True
                initial["original_email"] = original_email.pk

                # Show the number of reminders already sent out for this email
                reminder_prefix = (
                    f"Reminder {reminder_count + 1}"
                    if reminder_count > 0
                    else "Reminder"
                )
                initial["subject"] = f"{reminder_prefix}: {original_email.subject}"
                initial["content"] = original_email.content

            except InvitationEmail.DoesNotExist:
                pass

        # Is this an invitation email being created?
        else:
            initial["is_reminder"] = False
            initial["original_email"] = None

        return initial

    def send_reminder_view(self, request, object_id):
        """
        Handle the send reminder action from the InvitationEmail change view.

        This basically allows us to have a different behaviour for reminders.
        """
        obj = self.get_object(request, object_id)

        if not obj:
            self.message_user(
                request,
                "Cannot send reminder - invitation email not found.",
                messages.ERROR,
            )
            return HttpResponseRedirect(
                reverse("admin:emails_invitationemail_changelist")
            )

        add_url = reverse("admin:emails_invitationemail_add")
        params = {
            "original_email_id": str(
                obj.original_email.id if obj.is_reminder else obj.id
            ),
            "is_reminder": "1",
        }
        redirect_url = f"{add_url}?{urlencode(params)}"

        return HttpResponseRedirect(redirect_url)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}

        # Add reminder button invitation & reminder emails; pre-populate context
        obj = self.get_object(request, object_id)
        if obj:
            extra_context["show_reminder_button"] = True
            extra_context["reminder_url"] = reverse(
                "admin:emails_invitationemail_send_reminder", args=[object_id]
            )
            if obj.is_reminder:
                extra_context["original_email"] = obj.original_email
                extra_context["reminder_emails"] = (
                    obj.original_email.reminder_emails.all()
                )
            else:
                extra_context["original_email"] = None
                extra_context["reminder_emails"] = obj.reminder_emails.all()

        return super().change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url="", extra_context=None):
        """
        Overridden to implement separate behaviour for reminder emails.
        """
        extra_context = extra_context or {}

        # Always pop the reminder_original_email_id session key to avoid stale state
        request.session.pop("reminder_original_email_id", None)

        if "is_reminder" in request.GET and "original_email_id" in request.GET:
            original_email_id = request.GET.get("original_email_id")

            try:
                original_email = InvitationEmail.objects.get(id=original_email_id)
                unregistered_orgs = original_email.unregistered_organizations

                org_count = len(unregistered_orgs)
                events = list(original_email.events.all())
                event_group = original_email.event_group

                if events:
                    event_info = ", ".join(event.title for event in events)
                elif event_group:
                    event_info = event_group.name
                else:
                    event_info = "event"
                extra_context["title"] = (
                    f"Send Reminder Email for {event_info} ({org_count} "
                    f"unregistered organizations)"
                )

                # Store the original email ID for use in response_post_save_add()
                request.session["reminder_original_email_id"] = original_email_id

            except InvitationEmail.DoesNotExist:
                self.message_user(
                    request, "Original invitation email not found.", messages.ERROR
                )
                return redirect("admin:emails_invitationemail_changelist")

        return super().add_view(request, form_url, extra_context)

    def response_post_save_add(self, request, obj):
        # First check if this is a reminder
        original_email_id = request.session.pop("reminder_original_email_id", None)
        original_email = None
        if original_email_id:
            try:
                original_email = InvitationEmail.objects.get(id=original_email_id)
                if not obj.is_reminder:
                    obj.is_reminder = True
                obj.original_email = original_email
                obj.save(update_fields=["is_reminder", "original_email"])
            except InvitationEmail.DoesNotExist:
                self.message_user(
                    request,
                    f"Error: Original email (ID: {original_email_id}) not found, "
                    f"cannot create reminder email for it.",
                    messages.ERROR,
                )
                # Delete the created object and redirect back to list
                obj.delete()
                return redirect("admin:emails_invitationemail_changelist")

        tasks = []
        event = obj.events.first() if obj.events.exists() else None
        event_group = obj.event_group

        org_recipients = get_organization_recipients(
            obj.organization_types.all(),
            obj.organizations.all(),
            additional_cc_contacts=obj.cc_recipients.all(),
            additional_bcc_contacts=obj.bcc_recipients.all(),
            invitation_email=original_email,
        )

        for org, data in org_recipients.items():
            if data["to_emails"]:
                with transaction.atomic():
                    if (
                        org.organization_type
                        and org.organization_type.acronym == "GOV"
                        and org.government
                    ):
                        # Create or get country-level invitation
                        # If organization is missing the government field,
                        # it will be processed below and invited simply as org
                        invitation, _ = EventInvitation.objects.get_or_create(
                            country=org.government,
                            event=event,
                            event_group=event_group,
                            # This (together with setting the country) signifies we're
                            # inviting all GOV-related organizations from that country.
                            organization=None,
                        )
                    else:
                        # Regular organization-level invitation
                        invitation, _ = EventInvitation.objects.get_or_create(
                            country=None,
                            organization=org,
                            event=event,
                            event_group=event_group,
                        )
                    task = SendEmailTask.objects.create(
                        email=obj,
                        organization=org,
                        invitation=invitation,
                        created_by=request.user,
                        email_to=list(data["to_emails"]),
                        email_cc=list(data["cc_emails"]),
                        email_bcc=list(data["bcc_emails"]),
                    )

                    # Set contacts M2M as returned by get_organization_recipients()
                    task.to_contacts.set(data["to_contacts"])
                    task.cc_contacts.set(data["cc_contacts"])
                    task.bcc_contacts.set(data["bcc_contacts"])

                    task.run(is_async=True)
                    tasks.append(task)

        message_type = "reminder" if original_email else "invitation"
        self.message_user(
            request,
            f"{len(tasks)} {message_type} emails scheduled for sending",
            messages.SUCCESS,
        )
        return redirect(self.get_admin_list_filter_link(obj, "email_logs", "email"))

    @admin.display(description="Original Email")
    def original_email_link(self, obj):
        if obj.original_email:
            url = reverse(
                "admin:emails_invitationemail_change", args=[obj.original_email.pk]
            )
            return format_html('<a href="{}">{}</a>', url, obj.original_email.subject)
        return "-"

    @admin.display(description="Reminder Count")
    def reminder_count(self, obj):
        count = obj.reminder_emails.count()
        if count > 0:
            return format_html(
                '<a href="{}?original_email__id__exact={}">{} reminders</a>',
                reverse("admin:emails_invitationemail_changelist"),
                obj.pk,
                count,
            )
        return "0"


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
        "organization_link",
        "email_to_preview",
        "email_cc_preview",
        "created_on",
        "status_display",
    )
    list_display_links = ("email",)
    list_filter = (
        AutocompleteFilterFactory("organization", "organization"),
        AutocompleteFilterFactory("government", "organization__government"),
        AutocompleteFilterMultipleFactory(
            "organization types", "organization__organization_type"
        ),
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
        "contact__organization",
        "contact__organization__government",
        "contact__organization__country",
        "organization",
        "organization__government",
        "organization__country",
    )
    fieldsets = [
        (
            None,
            {
                "fields": (
                    "email_with_link",
                    "contact",
                    "organization",
                    "invitation",
                    "to_contacts_links",
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

    def get_email_link(self, email):
        """Generates correct admin URL based on email type."""
        if email.email_type == Email.EmailTypeChoices.EVENT_INVITE:
            return reverse("admin:emails_invitationemail_change", args=[email.pk])
        return reverse("admin:emails_email_change", args=[email.pk])

    @admin.display(description="Email", ordering="email")
    def email_with_link(self, obj):
        url = self.get_email_link(obj.email)
        return format_html('<a href="{}">{}</a>', url, obj.email)

    @admin.display(description="Contact", ordering="contact")
    def contact_link(self, obj):
        return self.get_object_display_link(obj.contact)

    @admin.display(description="Organization", ordering="organization")
    def organization_link(self, obj):
        return self.get_object_display_link(obj.organization)

    @admin.display(description="To contacts")
    def to_contacts_links(self, obj):
        return self.get_m2m_links(obj.to_contacts.all())

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
