from django.db import models
from django_task.models import TaskRQ


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
