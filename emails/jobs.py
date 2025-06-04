import logging

from django_task.job import Job

from emails.models import SendEmailTask


class SendEmailJob(Job):
    @staticmethod
    def execute(job, task: SendEmailTask):
        task.log(logging.INFO, "Building email %r", task.email)

        to_emails = []
        cc_emails = []
        bcc_emails = []
        if not task.contact:
            for contact in task.to_contacts.all():
                if contact.emails:
                    to_emails.extend(contact.emails)
            for contact in task.cc_contacts.all():
                if contact.emails:
                    cc_emails.extend(contact.emails)

            task.log(logging.INFO, "Setting recipients from to_contacts: %s", to_emails)

        msg = task.email.build_email(
            contact=task.contact,
            to_list=to_emails,
            cc_list=cc_emails,
            bcc_list=bcc_emails,
            invitation=task.invitation,
        )
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
        task.sent_email = msg.message().as_string()
        # Save a copy of the addresses we are sending this message to.
        # In case the contact addresses change in the future, we still have these
        # fields for easy searches, tracing and auditing.
        task.email_to = msg.to
        task.email_cc = msg.cc
        task.email_bcc = msg.bcc
        # Link to contacts as well for tracking; useful since group memberships can
        # change after this email is sent.
        task.cc_contacts.add(*task.email.all_cc_contacts)
        task.bcc_contacts.add(*task.email.all_bcc_contacts)
        task.save()

        msg.send()
        task.log(logging.INFO, "Email %r sent to all addresses", task.email)
