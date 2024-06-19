import html
import re
from email import message_from_string
from functools import cached_property
from ckeditor_uploader.fields import RichTextUploadingField
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.db.models import Q
from django.utils.html import strip_tags
from django_task.models import TaskRQ
from common.array_field import ArrayField
from core.models import Contact, ContactGroup
from events.models import Event


def get_relative_image_urls(email_body):
    img_tag_pattern = r'<img.*?src="(.*?)"'
    relative_image_urls = re.findall(img_tag_pattern, email_body)
    return list(set(relative_image_urls))


def replace_relative_image_urls(email_body):
    relative_urls = get_relative_image_urls(email_body)
    domain = settings.PROTOCOL + settings.MAIN_HOST
    for url in relative_urls:
        absolute_url = domain + url
        email_body = email_body.replace(url, absolute_url)

    return email_body


def validate_placeholders(value):
    placeholders = set(re.findall(r"\[\[(.*?)\]\]", value or ""))
    if invalid := placeholders.difference(settings.CKEDITOR_PLACEHOLDERS):
        msg = ", ".join([f"[[{item}]]" for item in invalid])
        raise ValidationError(f"Invalid placeholders: {msg}")


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
        limit_choices_to=~Q(registrations=None),
        related_name="sent_emails",
    )
    subject = models.CharField(max_length=900)
    content = RichTextUploadingField(validators=[validate_placeholders])
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return self.subject

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

    def build_email(self, contact=None):
        msg = EmailMultiAlternatives(
            subject=self.subject, from_email=settings.DEFAULT_FROM_EMAIL
        )

        html_content = self.content.strip()
        if contact:
            msg.to.extend(contact.emails)
            msg.cc.extend(contact.email_ccs)

            for placeholder in settings.CKEDITOR_PLACEHOLDERS:
                html_content = html_content.replace(
                    f"[[{placeholder}]]", getattr(contact, placeholder)
                )

        for contact in self.all_cc_contacts:
            msg.cc.extend(contact.emails)
        for contact in self.all_bcc_contacts:
            msg.bcc.extend(contact.emails)

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
    file = models.FileField(upload_to="email_files/", storage=storages["protected"])
    name = models.CharField(
        max_length=255,
        null=True,
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
        null=True,
        help_text="Complete copy of the sent email.",
    )

    class Meta:
        get_latest_by = "created_on"

    def __str__(self):
        result = []
        if self.email_to:
            result.append("To:")
            result.append(", ".join(self.email_to))
        result.append(self.email.subject)
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
