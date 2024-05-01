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
    groups = models.ManyToManyField(
        ContactGroup,
        blank=True,
        help_text="Send the email to all contacts in these selected groups.",
        limit_choices_to=~Q(contacts=None),
        related_name="sent_emails",
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
    def all_recipients(self):
        all_recipients = set(self.recipients.all())
        for group in self.groups.prefetch_related("contacts"):
            all_recipients.update(group.contacts.all())
        for event in self.events.all().prefetch_related(
            "registrations", "registrations__contact"
        ):
            for registration in event.registrations.all():
                all_recipients.add(registration.contact)
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
        Email, on_delete=models.CASCADE, related_name="email_logs"
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        related_name="email_logs",
        null=True,
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
        get_latest_by = "created_on"

    def __str__(self):
        return f"To: {', '.join(self.email_to)} {self.email.subject}"

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
