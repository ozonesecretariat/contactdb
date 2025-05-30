from django.core.management.base import BaseCommand

from core.models import Organization


def flatten_emails(emails: list[list[str]]) -> list[str]:
    """Reduce a list of email lists to a list of emails."""
    return [
        email.lower()
        for lst in emails
        if lst is not None
        for email in lst
        if email and email not in ["", None]
    ]


class Command(BaseCommand):
    """
    Command to clean organization emails by removing those that are
    already associated with primary or secondary contacts.
    """

    help = __doc__

    def handle(self, *args, **options):
        organizations = Organization.objects.all()

        for org in organizations:
            if org.emails is None and org.email_ccs is None:
                continue

            primary_contacts = org.primary_contacts.all()
            secondary_contacts = org.secondary_contacts.all()

            contact_emails = set(
                flatten_emails(
                    primary_contacts.values_list("emails", flat=True).distinct()
                )
                + flatten_emails(
                    primary_contacts.values_list("email_ccs", flat=True).distinct()
                )
                + flatten_emails(
                    secondary_contacts.values_list("emails", flat=True).distinct()
                )
                + flatten_emails(
                    secondary_contacts.values_list("email_ccs", flat=True).distinct()
                )
            )

            org_emails = set(map(str.lower, org.emails or []))
            org_email_ccs = set(map(str.lower, org.email_ccs or []))

            org.emails = list(org_emails - contact_emails)
            org.email_ccs = list(org_email_ccs - contact_emails)
            org.save()

            del_emails = org_emails - set(org.emails)
            del_email_ccs = org_email_ccs - set(org.email_ccs)

            if del_emails or del_email_ccs:
                self.stdout.write(
                    f"Deleted emails from organization {org.name}: {del_emails | del_email_ccs}"
                )
