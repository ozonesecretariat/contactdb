import html
import re
from email import message_from_string
from functools import cached_property

from ckeditor_uploader.fields import RichTextUploadingField
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db import models, transaction
from django.db.models import Exists, OuterRef, Q
from django.utils.html import strip_tags
from django_task.models import TaskRQ

from accounts.models import User
from common.array_field import ArrayField
from common.model import get_protected_storage
from core.models import (
    Contact,
    ContactGroup,
    Organization,
    OrganizationType,
)
from emails.placeholders import (
    replace_placeholders,
)
from emails.validators import validate_placeholders
from events.models import Event, EventGroup, EventInvitation, Registration


def get_relative_image_urls(email_body):
    img_tag_pattern = r'<img.*?src="(.*?)"'
    relative_image_urls = re.findall(img_tag_pattern, email_body)
    return list(set(relative_image_urls))


def replace_relative_image_urls(email_body):
    relative_urls = get_relative_image_urls(email_body)
    domain = settings.PROTOCOL + settings.MAIN_BACKEND_HOST
    for url in relative_urls:
        absolute_url = domain + url
        email_body = email_body.replace(url, absolute_url)

    return email_body


class EmailTemplate(models.Model):
    title = models.CharField(
        max_length=250,
        help_text=(
            "Name of the template, used to identify the template when selecting it."
        ),
        unique=True,
    )
    description = models.TextField(
        help_text=(
            "A short description for the template, displayed in the list when "
            "choosing a template for an email."
        )
    )
    content = RichTextUploadingField(validators=[validate_placeholders])

    def __str__(self):
        return self.title


class Email(models.Model):
    class EmailTypeChoices(models.TextChoices):
        EVENT_INVITE = "EVENT INVITE", "Event Invite"
        EVENT_NOTIFICATION = "EVENT_NOTIFICATION", "Event Notification"

    email_type = models.CharField(
        max_length=32,
        choices=EmailTypeChoices.choices,
        default=EmailTypeChoices.EVENT_NOTIFICATION,
    )

    is_reminder = models.BooleanField(
        default=False,
        help_text=(
            "Is this a reminder email for a previously sent invitation, "
            "for organizations that have not registered any contacts yet. "
            "This changes email behaviour: only sends mails to 'unregistered' orgs."
        ),
    )
    original_email = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reminder_emails",
        help_text="The original invitation email this is a reminder for.",
    )

    recipients = models.ManyToManyField(
        Contact,
        blank=True,
        help_text="Send the email to all the selected contacts.",
        limit_choices_to=~Q(emails=[]),
        related_name="sent_emails",
    )
    cc_recipients = models.ManyToManyField(
        Contact,
        blank=True,
        help_text="Add these recipients in the Cc for all sent emails.",
        limit_choices_to=~Q(emails=[]),
        related_name="sent_emails_cc",
    )
    bcc_recipients = models.ManyToManyField(
        Contact,
        blank=True,
        help_text="Add these recipients in the Bcc for all sent emails.",
        limit_choices_to=~Q(emails=[]),
        related_name="sent_emails_bcc",
    )
    groups = models.ManyToManyField(
        ContactGroup,
        blank=True,
        help_text="Send the email to all contacts in these selected groups.",
        limit_choices_to=~Q(contacts=None),
        related_name="sent_emails",
    )
    cc_groups = models.ManyToManyField(
        ContactGroup,
        blank=True,
        help_text="Add all contacts from this group in the Cc for all sent emails.",
        limit_choices_to=~Q(contacts=None),
        related_name="sent_emails_cc",
    )
    bcc_groups = models.ManyToManyField(
        ContactGroup,
        blank=True,
        help_text="Add all contacts from this group in the Bcc for all sent emails.",
        limit_choices_to=~Q(contacts=None),
        related_name="sent_emails_bcc",
    )
    events = models.ManyToManyField(
        Event,
        blank=True,
        help_text="Send the email to all participants of these selected events.",
        related_name="sent_emails",
    )
    event_group = models.ForeignKey(
        EventGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sent_emails",
        help_text="Send the email to all participants of the events in this event group.",
    )
    # `organizations` and `organization_types` are mutually exclusive
    organization_types = models.ManyToManyField(
        OrganizationType,
        blank=True,
        help_text="Send the email to primary contacts of these organization types.",
        related_name="sent_emails",
    )
    organizations = models.ManyToManyField(
        Organization,
        null=True,
        blank=True,
        help_text="Send the email to primary contacts of these organizations.",
        related_name="sent_emails",
    )
    subject = models.CharField(max_length=900, validators=[validate_placeholders])
    content = RichTextUploadingField(validators=[validate_placeholders])
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_emails",
    )

    def __str__(self):
        return self.subject

    def save(self, *args, **kwargs):
        with transaction.atomic():
            # Typically, validations would be performed before save(),
            # but since these are M2M fields, save is needed to have their values.
            # Wrapping this in a transaction so we don't commit "bad" data.
            super().save(*args, **kwargs)

            if self.organization_types.exists() and self.organizations.exists():
                raise ValidationError(
                    "Cannot specify both organization types and specific organizations."
                )

    def queue_emails(self):
        tasks = []
        for contact in self.all_to_contacts:
            task = SendEmailTask.objects.create(
                email=self, contact=contact, created_by=self.created_by
            )
            task.run(is_async=True)
            tasks.append(task)
        return tasks

    @property
    def all_to_contacts(self):
        all_recipients = set(self.recipients.all())
        for group in self.groups.prefetch_related("contacts"):
            all_recipients.update(group.contacts.all())
        for event in self.events.all().prefetch_related(
            "registrations", "registrations__contact"
        ):
            for registration in event.registrations.all():
                all_recipients.add(registration.contact)
        return all_recipients

    @property
    def all_cc_contacts(self):
        result = set(self.cc_recipients.all())
        for group in self.cc_groups.all().prefetch_related("contacts"):
            result.update(group.contacts.all())
        return result

    @property
    def all_bcc_contacts(self):
        result = set(self.bcc_recipients.all())
        for group in self.bcc_groups.all().prefetch_related("contacts"):
            result.update(group.contacts.all())
        return result

    def build_email(
        self, contact=None, to_list=None, cc_list=None, bcc_list=None, invitation=None
    ):
        subject = replace_placeholders([contact, invitation], self.subject)
        msg = EmailMultiAlternatives(
            subject=subject,
            from_email=settings.DEFAULT_FROM_EMAIL,
        )

        if contact:
            msg.to.extend(contact.emails or [])
            msg.cc.extend(contact.email_ccs or [])
            # Add "global" CCs and BCCs (will be included in *all* actual emails generated
            # for this Email instance).
            for cc_contact in self.all_cc_contacts:
                msg.cc.extend(cc_contact.emails or [])
            for bcc_contact in self.all_bcc_contacts:
                msg.bcc.extend(bcc_contact.emails or [])

        if to_list:
            msg.to.extend(to_list)
        if cc_list:
            msg.cc.extend(cc_list)
        if bcc_list:
            msg.bcc.extend(bcc_list)

        html_content = self.content.strip()
        html_content = replace_placeholders([contact, invitation], html_content)

        # Remove all HTML Tags, leaving only the plaintext
        text_content = strip_tags(html_content)
        # Unescape any HTML Entities such as &amp; or &nbsp;
        text_content = html.unescape(text_content).strip()
        # Remove all the empty lines, but keep any "paragraphs"
        text_content = re.sub(r"\n{3,}", "\n\n", text_content)

        msg.body = text_content
        msg.attach_alternative(
            replace_relative_image_urls(html_content),
            "text/html",
        )

        for attachment in self.attachments.all():
            with attachment.file.open("rb") as fp:
                msg.attach(
                    attachment.name or attachment.file.name,
                    fp.read(),
                )

        return msg


class EmailAttachment(models.Model):
    file = models.FileField(upload_to="email_files/", storage=get_protected_storage)
    name = models.CharField(
        max_length=255,
        blank=True,
        help_text=(
            "Name to use for the attachment, defaults to the uploaded filename "
            "if not specified."
        ),
    )
    email = models.ForeignKey(
        Email, on_delete=models.CASCADE, related_name="attachments"
    )

    class Meta:
        ordering = ("email", "name", "id")

    def __str__(self):
        return self.name or self.file.name

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.file.name
        super().save(*args, **kwargs)


class InvitationEmail(Email):
    """
    Proxy model for Email so we can have separate admin forms for different email types.
    """

    class Meta:
        proxy = True
        verbose_name = "Invitation Email"
        verbose_name_plural = "Invitation Emails"

    @property
    def unregistered_organizations(self):
        """
        Get all organizations that were invited by this email but haven't registered yet.
        Returns a queryset of organizations.
        """
        events = list(self.events.all())
        event_group = self.event_group

        if not (events or event_group):
            return Organization.objects.none()

        if events:
            invitations = EventInvitation.objects.filter(event__in=events)
        else:
            invitations = EventInvitation.objects.filter(event_group=event_group)
            events = list(event_group.events.all())

        if self.organizations.exists():
            # This is an organizations-list-based invitation
            # Not taking include_in_invitation into account in this case
            organizations_qs = self.organizations.all()
        elif self.organization_types.exists():
            organizations_qs = Organization.objects.filter(
                include_in_invitation=True,
                organization_type__in=self.organization_types.all(),
            )
        else:
            return Organization.objects.none()

        # These are ALL uregistered orgs, regardless of being invited directly/via GOV
        return (
            organizations_qs.filter(
                Q(
                    # Direct org-based invitations;
                    # include all orgs that have no registrations
                    id__in=invitations.filter(organization__isnull=False).values_list(
                        "organization_id", flat=True
                    ),
                )
                & ~Exists(
                    Registration.objects.filter(
                        event__in=events if events else [],
                        contact__organization=OuterRef("pk"),
                    )
                )
                | Q(
                    # Government/county invitations;
                    # only include orgs when no org from same country has registrations
                    government__in=invitations.filter(
                        country__isnull=False
                    ).values_list("country_id", flat=True),
                )
                & ~Exists(
                    Registration.objects.filter(
                        event__in=events if events else [],
                        contact__organization__government=OuterRef("government"),
                    )
                )
            )
            .distinct()
            .prefetch_related(
                "primary_contacts",
                "secondary_contacts",
                "government",
            )
        )


class SendEmailTask(TaskRQ):
    DEFAULT_VERBOSITY = 2
    TASK_QUEUE = "default"
    TASK_TIMEOUT = 60
    LOG_TO_FIELD = True
    LOG_TO_FILE = False

    email = models.ForeignKey(
        Email, on_delete=models.CASCADE, related_name="email_logs"
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        related_name="email_logs",
        null=True,
    )
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="email_tasks",
    )
    invitation = models.ForeignKey(
        "events.EventInvitation",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="email_tasks",
    )
    to_contacts = models.ManyToManyField(
        Contact,
        related_name="email_logs_to",
    )
    cc_contacts = models.ManyToManyField(
        Contact,
        related_name="email_logs_cc",
    )
    bcc_contacts = models.ManyToManyField(
        Contact,
        related_name="email_logs_bcc",
    )
    email_to = ArrayField(
        blank=True,
        null=True,
        base_field=models.EmailField(),
        help_text="List of email addresses this email was sent to.",
        editable=False,
    )
    email_cc = ArrayField(
        blank=True,
        null=True,
        base_field=models.EmailField(),
        help_text="List of email addresses this email was sent to in Cc.",
        editable=False,
    )
    email_bcc = ArrayField(
        blank=True,
        null=True,
        base_field=models.EmailField(),
        help_text="List of email addresses this email was sent to in Bcc.",
        editable=False,
    )
    sent_email = models.TextField(
        default="",
        blank=True,
        help_text="Complete copy of the sent email.",
    )

    class Meta:
        get_latest_by = "created_on"

    def __str__(self):
        result = []
        result.append(self.email.subject)
        result.append(f"Date: {self.created_on.strftime('%d %B %Y')}")
        if self.email_to:
            result.append("To:")
            result.append(", ".join(self.email_to))
        return " ".join(result)

    @staticmethod
    def get_jobclass():
        from .jobs import SendEmailJob

        return SendEmailJob

    @cached_property
    def msg(self):
        return message_from_string(self.sent_email)

    @cached_property
    def text_plain(self):
        for part in self.msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode()
        return ""

    @cached_property
    def text_html(self):
        for part in self.msg.walk():
            if part.get_content_type() == "text/html":
                return part.get_payload(decode=True).decode()
        return ""
