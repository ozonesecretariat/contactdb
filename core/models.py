from ckeditor_uploader.fields import RichTextUploadingField
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mass_mail
from django.db import models
from django.utils.html import strip_tags
from django_task.models import TaskRQ
from ckeditor.fields import RichTextField
from django.contrib.postgres.fields import ArrayField

from core.utils import ConflictResolutionMethods, replace_relative_image_urls


class LoadKronosEventsTask(TaskRQ):
    DEFAULT_VERBOSITY = 2
    TASK_QUEUE = "default"
    TASK_TIMEOUT = 60
    LOG_TO_FIELD = True
    LOG_TO_FILE = False

    class Meta:
        get_latest_by = "created_on"

    @staticmethod
    def get_jobclass():
        from .jobs import LoadKronosEvents

        return LoadKronosEvents


class Organization(models.Model):
    organization_id = models.CharField(max_length=250, unique=True)
    name = models.CharField(max_length=250)
    acronym = models.CharField(blank=True, max_length=30)
    organization_type_id = models.CharField(max_length=250)
    organization_type = models.CharField(max_length=250)
    government = models.CharField(max_length=30, blank=True)
    government_name = models.CharField(max_length=250, blank=True)
    country = models.CharField(max_length=30, blank=True)
    country_name = models.CharField(max_length=250, blank=True)

    def __str__(self):
        if self.country_name:
            return self.name + ", " + self.country_name
        return self.name

    class Meta:
        ordering = ["name", "country_name"]


class Record(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True)
    contact_id = models.CharField(max_length=250, default="", blank=True)
    title = models.CharField(max_length=30, blank=True)
    honorific = models.CharField(max_length=30, default="", blank=True)
    respectful = models.CharField(max_length=30, default="", blank=True)
    first_name = models.CharField(max_length=250, default="", blank=True)
    last_name = models.CharField(max_length=250, default="", blank=True)
    designation = models.CharField(max_length=250, default="", blank=True)
    department = models.CharField(max_length=250, default="", blank=True)
    affiliation = models.CharField(max_length=250, default="", blank=True)
    primary_lang = models.CharField(
        max_length=100, default="", blank=True, verbose_name="Primary language"
    )
    second_lang = models.CharField(
        max_length=100, default="", blank=True, verbose_name="Second language"
    )
    third_lang = models.CharField(
        max_length=100, default="", blank=True, verbose_name="Third language"
    )
    phones = ArrayField(null=True, base_field=models.TextField(), blank=True)
    mobiles = ArrayField(null=True, base_field=models.TextField(), blank=True)
    faxes = ArrayField(null=True, base_field=models.TextField(), blank=True)
    emails = ArrayField(null=True, base_field=models.TextField(), blank=True)
    email_ccs = ArrayField(null=True, base_field=models.TextField(), blank=True)
    notes = models.TextField(default="", blank=True)
    is_in_mailing_list = models.BooleanField(default=False, blank=True)
    is_use_organization_address = models.BooleanField(default=False, blank=True)
    address = models.TextField(default="", blank=True)
    city = models.CharField(max_length=250, default="", blank=True)
    state = models.CharField(max_length=250, default="", blank=True)
    country = models.CharField(max_length=250, default="", blank=True)
    postal_code = models.CharField(max_length=250, default="", blank=True)
    birth_date = models.DateField(null=True, blank=True)
    focal_point = models.BooleanField(default=False, blank=True)
    org_head = models.BooleanField(
        default=False, blank=True, verbose_name="Head of organization"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    main_contact = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return self.first_name + " " + self.last_name

    @property
    def is_secondary(self):
        return self.main_contact is not None


class Group(models.Model):
    name = models.CharField(max_length=250, null=False, blank=False)
    description = models.TextField(blank=True, null=True)
    contacts = models.ManyToManyField(Record, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def members_count(self):
        return self.contacts.count()

    @property
    def description_preview(self):
        if len(str(self.description)) > 150:
            return self.description[:150] + "..."
        return self.description


class KronosEvent(models.Model):
    event_id = models.CharField(max_length=150, blank=False, null=False, unique=True)
    code = models.CharField(max_length=50, blank=False, null=False)
    title = models.CharField(max_length=255, blank=False, null=False)
    start_date = models.DateTimeField(null=False)
    end_date = models.DateTimeField(null=False)
    venue_country = models.CharField(max_length=50)
    venue_city = models.CharField(max_length=150)
    dates = models.CharField(max_length=255)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, default=None, null=True)

    def __str__(self):
        return self.title

    @property
    def imported_participants(self):
        return self.loadkronosparticipantstask_set.exists()

    @property
    def latest_import(self):
        if self.imported_participants:
            return self.loadkronosparticipantstask_set.latest()
        return None

    class Meta:
        verbose_name_plural = "kronos events"


class RegistrationStatus(models.Model):
    contact = models.ForeignKey(Record, on_delete=models.CASCADE)
    event = models.ForeignKey(KronosEvent, on_delete=models.CASCADE)
    code = models.CharField(max_length=100)
    status = models.IntegerField()
    date = models.DateTimeField()
    is_funded = models.BooleanField()
    role = models.IntegerField(null=True)
    priority_pass_code = models.CharField(max_length=150, blank=True)
    tags = ArrayField(base_field=models.TextField(), blank=True)

    def __str__(self):
        return self.event.event_id

    class Meta:
        verbose_name_plural = "registration statuses"


class NoRecipients(Exception):
    pass


class EmailTemplate(models.Model):
    name = models.CharField(max_length=100)
    html_content = RichTextUploadingField()

    def __str__(self):
        return self.name


class Emails(models.Model):
    recipients = models.ManyToManyField(Record, related_name="recipients")
    cc = models.ManyToManyField(Record, related_name="cc", verbose_name="CC")
    subject = models.TextField()
    content = RichTextUploadingField()
    groups = models.ManyToManyField(Group, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    send_personalised_emails = models.BooleanField(default=False)

    def __str__(self):
        return self.subject

    def send(self):
        if not self.recipients:
            raise NoRecipients("No recipients found.")

        from_email = settings.DEFAULT_FROM_EMAIL
        recipients = []
        cc = []

        if not self.send_personalised_emails:
            for contact in self.recipients.all():
                recipients += contact.emails

            for contact in self.cc.all():
                cc += contact.emails

            self.send_email(
                subject=self.subject,
                content=self.content,
                recipients=recipients,
                cc=cc,
                from_email=from_email,
                attachments=self.emailfile_set.all(),
            )
        else:
            for contact in self.recipients.all():
                subject = self.subject.strip()
                content = self.content.strip()

                for tag in EmailTag.objects.all():
                    subject = subject.replace(
                        str(tag), getattr(contact, tag.field_name)
                    )
                    content = content.replace(
                        str(tag), getattr(contact, tag.field_name)
                    )
                self.send_email(
                    subject=subject,
                    content=content,
                    recipients=contact.emails,
                    cc=[],
                    from_email=from_email,
                    attachments=self.emailfile_set.all(),
                )

    @staticmethod
    def send_email(subject, content, recipients, cc, from_email, attachments):
        text_content = strip_tags(content)
        email = EmailMultiAlternatives(
            subject=subject,
            from_email=from_email,
            to=recipients,
            cc=cc,
            body=text_content,
        )
        email.attach_alternative(replace_relative_image_urls(content), "text/html")
        for file in attachments:
            email.attach_file(file.path)
        email.send()

    class Meta:
        verbose_name_plural = "e-mails"


class EmailFile(models.Model):
    name = models.CharField(max_length=100)
    file = models.FileField(upload_to="email_files/")
    email = models.ForeignKey(Emails, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    @property
    def path(self):
        return self.file.path

    @property
    def url(self):
        return self.file.url


class SendMailTask(TaskRQ):
    """Can be used to send email asynchronously. Example usage:

    SendMailTask.objects.create(
        recipient="test@example.com",
        subject="[Test email] subject here",
        message="Hello world",
    ).run(is_async=True)
    """

    DEFAULT_VERBOSITY = 2
    TASK_QUEUE = "default"
    TASK_TIMEOUT = 60
    LOG_TO_FIELD = True
    LOG_TO_FILE = False

    email = models.ForeignKey(Emails, on_delete=models.SET_NULL, null=True)

    class Meta:
        get_latest_by = "created_on"

    @staticmethod
    def get_jobclass():
        from .jobs import SendMailJob

        return SendMailJob


class LoadKronosParticipantsTask(TaskRQ):
    DEFAULT_VERBOSITY = 2
    TASK_QUEUE = "default"
    TASK_TIMEOUT = 60
    LOG_TO_FIELD = True
    LOG_TO_FILE = False

    kronos_events = models.ManyToManyField(KronosEvent)
    create_groups = models.BooleanField(default=False)

    class Meta:
        get_latest_by = "created_on"

    @staticmethod
    def get_jobclass():
        from .jobs import LoadKronosParticipants

        return LoadKronosParticipants


class ResolveAllConflictsTask(TaskRQ):
    DEFAULT_VERBOSITY = 2
    TASK_QUEUE = "default"
    TASK_TIMEOUT = 60
    LOG_TO_FIELD = True
    LOG_TO_FILE = False

    method = models.CharField(max_length=60, choices=ConflictResolutionMethods.choices)

    class Meta:
        get_latest_by = "created_on"

    @staticmethod
    def get_jobclass():
        from .jobs import ResolveAllConflicts

        return ResolveAllConflicts


class TemporaryContact(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE, null=True)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True)
    contact_id = models.CharField(max_length=250, default="", blank=True)
    title = models.CharField(max_length=30, blank=True)
    honorific = models.CharField(max_length=30, default="", blank=True)
    respectful = models.CharField(max_length=30, default="", blank=True)
    first_name = models.CharField(max_length=250, default="", blank=True)
    last_name = models.CharField(max_length=250, default="", blank=True)
    designation = models.CharField(max_length=250, default="", blank=True)
    department = models.CharField(max_length=250, default="", blank=True)
    affiliation = models.CharField(max_length=250, default="", blank=True)
    primary_lang = models.CharField(
        max_length=100, default="", blank=True, verbose_name="Primary language"
    )
    second_lang = models.CharField(
        max_length=100, default="", blank=True, verbose_name="Second language"
    )
    third_lang = models.CharField(
        max_length=100, default="", blank=True, verbose_name="Third language"
    )
    phones = ArrayField(null=True, base_field=models.TextField(), blank=True)
    mobiles = ArrayField(null=True, base_field=models.TextField(), blank=True)
    faxes = ArrayField(null=True, base_field=models.TextField(), blank=True)
    emails = ArrayField(null=True, base_field=models.TextField(), blank=True)
    email_ccs = ArrayField(null=True, base_field=models.TextField(), blank=True)
    notes = models.TextField(default="", blank=True)
    is_in_mailing_list = models.BooleanField(default=False, blank=True)
    is_use_organization_address = models.BooleanField(default=False, blank=True)
    address = models.TextField(default="", blank=True)
    city = models.CharField(max_length=250, default="", blank=True)
    state = models.CharField(max_length=250, default="", blank=True)
    country = models.CharField(max_length=250, default="", blank=True)
    postal_code = models.CharField(max_length=250, default="", blank=True)
    birth_date = models.DateField(null=True, blank=True)
    focal_point = models.BooleanField(default=False, blank=True)
    org_head = models.BooleanField(
        default=False, blank=True, verbose_name="Head of organization"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.first_name + " " + self.last_name


class EmailTag(models.Model):
    name = models.CharField(max_length=20, blank=False, null=False)
    field_name = models.CharField(max_length=20, blank=False, null=False)

    def __str__(self):
        return "{{ " + self.name + " }}"
