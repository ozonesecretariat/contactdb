"""Script to run import legacy contacts from cmd line."""

from django.core.management.base import BaseCommand

from core.models import Organization


class Command(BaseCommand):
    help = __doc__

    def handle(self, *args, **options):
        organizations = Organization.objects.all()

        for organization in organizations:
            primary_contacts = organization.primary_contacts.all()
            secondary_contacts = organization.secondary_contacts.all()

            contact_emails = set(
                list(primary_contacts.values_list("emails", flat=True).distinct())
                + list(primary_contacts.values_list("email_ccs", flat=True).distinct())
                + list(secondary_contacts.values_list("emails", flat=True).distinct())
                + list(
                    secondary_contacts.values_list("email_ccs", flat=True).distinct()
                )
            )

            organization.emails = set(organization.emails) - contact_emails
            organization.email_ccs = set(organization.email_ccs) - contact_emails
            organization.save()
