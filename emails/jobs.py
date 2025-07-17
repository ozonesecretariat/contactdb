import logging

from django.db import transaction
from django_task.job import Job
from django_task.utils import get_model_from_id

from emails.models import Email, InvitationEmail, SendEmailTask
from emails.services import get_organization_recipients
from events.models import EventInvitation

logger = logging.getLogger(__name__)


class SendEmailJob(Job):
    @staticmethod
    def execute(job, task: SendEmailTask):
        task.log(logging.INFO, "Building email %r", task.email)

        # For invitation emails, use the pre-computed email address recipients
        is_invitation_email = not task.contact

        msg = task.email.build_email(
            contact=task.contact,
            to_list=task.email_to if is_invitation_email else [],
            cc_list=task.email_cc if is_invitation_email else [],
            bcc_list=task.email_bcc if is_invitation_email else [],
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
        # Task addresses & contacts already saved for invitation emails
        if task.contact:
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


def queue_emails(email_id):
    if email := get_model_from_id(Email, email_id):
        email.queue_emails()
    else:
        logger.warning("Could not find email %s to queue", email_id)


def queue_invitation_emails(invitation_email_id, original_email_id=None):
    obj = get_model_from_id(InvitationEmail, invitation_email_id)
    original_email = None
    if original_email_id:
        original_email = get_model_from_id(InvitationEmail, original_email_id)

    if not obj:
        logger.warning("Could not find email %s to queue", invitation_email_id)
        return

    event = obj.events.first() if obj.events.exists() else None
    event_group = obj.event_group

    org_recipients = get_organization_recipients(
        obj.organization_types.all(),
        obj.organizations.all(),
        additional_cc_contacts=obj.cc_recipients.all(),
        additional_bcc_contacts=obj.bcc_recipients.all(),
        invitation_email=original_email,
    )

    for org, data in org_recipients.items():
        if not data["to_emails"]:
            continue
        with transaction.atomic():
            if (
                org.organization_type
                and org.organization_type.acronym == "GOV"
                and org.government
            ):
                # Create or get country-level invitation
                # If organization is missing the government field,
                # it will be processed below and invited simply as org
                invitation, _ = EventInvitation.objects.get_or_create(
                    country=org.government,
                    event=event,
                    event_group=event_group,
                    # This (together with setting the country) signifies we're
                    # inviting all GOV-related organizations from that country.
                    organization=None,
                )
            else:
                # Regular organization-level invitation
                invitation, _ = EventInvitation.objects.get_or_create(
                    country=None,
                    organization=org,
                    event=event,
                    event_group=event_group,
                )
            task = SendEmailTask.objects.create(
                email=obj,
                organization=org,
                invitation=invitation,
                created_by=obj.created_by,
                email_to=list(data["to_emails"]),
                email_cc=list(data["cc_emails"]),
                email_bcc=list(data["bcc_emails"]),
            )

            # Set contacts M2M as returned by get_organization_recipients()
            task.to_contacts.set(data["to_contacts"])
            task.cc_contacts.set(data["cc_contacts"])
            task.bcc_contacts.set(data["bcc_contacts"])

        task.run(is_async=True)
