import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django_task.job import Job
from common.utils import replace_relative_image_urls


class SendMailJob(Job):
    @staticmethod
    def execute(job, task):
        task.log(logging.INFO, "Building email %r for: %s", task.email, task.contact)

        html_content = task.email.content.strip()
        for placeholder in settings.CKEDITOR_PLACEHOLDERS:
            html_content = html_content.replace(
                f"[[{placeholder}]]", getattr(task.contact, placeholder)
            )

        text_content = strip_tags(html_content).replace("&nbsp;", " ").strip()

        msg = EmailMultiAlternatives(
            subject=task.email.subject,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=task.contact.emails,
            cc=task.contact.email_ccs,
            body=text_content,
        )
        msg.attach_alternative(
            replace_relative_image_urls(html_content),
            "text/html",
        )

        recipients = msg.recipients()
        if not recipients:
            raise RuntimeError(
                "Contact has no email addresses, nowhere to send the email."
            )

        for attachment in task.email.attachments.all():
            task.log(logging.INFO, "Attaching: %s", attachment)
            with attachment.file.open("rb") as fp:
                msg.attach(
                    attachment.name or attachment.file.name,
                    fp.read(),
                )
        task.log(
            logging.INFO,
            "Sending email to addresses: %s",
            recipients,
        )

        # Save a copy of the message before sending.
        task.sent_email = msg.message().as_string()
        task.save()
        count = msg.send()
        task.log(logging.INFO, "Email %r sent to address, total %s", task.email, count)
