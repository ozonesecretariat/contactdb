import logging

from django_task.job import Job


class SendEmailJob(Job):
    @staticmethod
    def execute(job, task):
        task.log(logging.INFO, "Building email %r for: %s", task.email, task.contact)
        msg = task.email.build_email(task.contact)
        if not (recipients := msg.recipients()):
            raise RuntimeError(
                "Contact has no email addresses, nowhere to send the email."
            )

        task.log(
            logging.INFO,
            "Sending email to addresses: %s",
            recipients,
        )
        # Save a copy of the message before sending
        task.email_to = msg.to
        task.email_cc = msg.cc
        task.sent_email = msg.message().as_string()
        task.save()
        msg.send()
        task.log(logging.INFO, "Email %r sent to all addresses", task.email)
