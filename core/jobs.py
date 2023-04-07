import logging

from django_task.job import Job
from django.core.mail import send_mail


class SendMailJob(Job):
    @staticmethod
    def execute(job, task):
        task.log(logging.INFO, "Sending email to: %s", task.recipient)

        send_mail(
            task.subject.strip(),
            task.message,
            None,
            [task.recipient],
        )
