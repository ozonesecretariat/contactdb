from django.db import models
from django_task.models import TaskRQ
from django.contrib.postgres.fields import ArrayField


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

    recipient = models.EmailField()
    subject = models.CharField(max_length=1024)
    message = models.TextField()

    class Meta:
        get_latest_by = "created_on"

    @staticmethod
    def get_jobclass():
        from .jobs import SendMailJob

        return SendMailJob


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
    contact_id = models.CharField(max_length=250, unique=True)
    title = models.CharField(max_length=30, blank=True)
    first_name = models.CharField(max_length=250, default="", blank=True)
    last_name = models.CharField(max_length=250, default="", blank=True)
    designation = models.CharField(max_length=250, default="", blank=True)
    department = models.CharField(max_length=250, default="", blank=True)
    affiliation = models.CharField(max_length=250, default="", blank=True)
    phones = ArrayField(base_field=models.TextField(), blank=True)
    mobiles = ArrayField(base_field=models.TextField(), blank=True)
    faxes = ArrayField(base_field=models.TextField(), blank=True)
    emails = ArrayField(base_field=models.TextField(), blank=True)
    email_ccs = ArrayField(base_field=models.TextField(), blank=True)
    notes = models.TextField(default="", blank=True)
    is_in_mailing_list = models.BooleanField()
    is_use_organization_address = models.BooleanField()
    address = models.CharField(max_length=250, default="", blank=True)
    city = models.CharField(max_length=250, default="", blank=True)
    state = models.CharField(max_length=250, default="", blank=True)
    country = models.CharField(max_length=250, default="", blank=True)
    postal_code = models.CharField(max_length=250, default="", blank=True)
    birth_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.first_name + " " + self.last_name


class RegistrationStatus(models.Model):
    contact = models.ForeignKey(Record, on_delete=models.CASCADE)
    event_id = models.CharField(max_length=150)
    code = models.CharField(max_length=100)
    status = models.IntegerField()
    date = models.DateTimeField()
    is_funded = models.BooleanField()
    role = models.IntegerField(null=True)
    priority_pass_code = models.CharField(max_length=150, blank=True)
    tags = ArrayField(base_field=models.TextField(), blank=True)

    def __str__(self):
        return self.event_id

    class Meta:
        verbose_name_plural = "registration statuses"


class Group(models.Model):
    name = models.CharField(max_length=250, null=False, blank=False)
    description = models.TextField(blank=True, null=True)
    contacts = models.ManyToManyField(Record, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
