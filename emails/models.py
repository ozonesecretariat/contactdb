import re
from email import message_from_string
from functools import cached_property
from ckeditor_uploader.fields import RichTextUploadingField
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.utils.html import strip_tags
from django_task.models import TaskRQ
from common.array_field import ArrayField
from common.utils import replace_relative_image_urls
from core.models import Contact, ContactGroup


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
    )
    groups = models.ManyToManyField(
        ContactGroup,
        blank=True,
        help_text="Send the email to all contacts in these selected groups.",
    )
    subject = models.CharField(max_length=900)
    content = RichTextUploadingField(validators=[validate_placeholders])
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return self.subject

    @property
    def all_recipients(self):
        all_recipients = set(self.recipients.all())
        for group in self.groups.all():
            all_recipients.update(group.contacts.all())
        return all_recipients

    def build_email(self, contact=None):
        msg = EmailMultiAlternatives(
            subject=self.subject, from_email=settings.DEFAULT_FROM_EMAIL
        )

        html_content = self.content.strip()
        if contact:
            msg.to = contact.emails
            msg.cc = contact.email_ccs

            for placeholder in settings.CKEDITOR_PLACEHOLDERS:
                html_content = html_content.replace(
                    f"[[{placeholder}]]", getattr(contact, placeholder)
                )

        text_content = strip_tags(html_content).replace("&nbsp;", " ").strip()
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
        Email, on_delete=models.CASCADE, related_name="email_history"
    )
    contact = models.ForeignKey(
        Contact, on_delete=models.CASCADE, related_name="email_history"
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
        help_text="List of email addresses this email was sent to in CC.",
        editable=False,
    )
    sent_email = models.TextField(
        default="",
        blank=True,
        null=True,
        help_text="Complete copy of the sent email.",
    )

    class Meta:
        unique_together = ("email", "contact")
        get_latest_by = "created_on"

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
