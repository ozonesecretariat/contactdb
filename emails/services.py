from django.db import models

from core.models import Organization


def get_organization_recipients(
    org_types, additional_cc_contacts=None, additional_bcc_contacts=None
):
    """
    Get Contacts per organization for *invitation* emails, using the organization's
    primary and secondary contacts.

    This is useful for sending emails to users that need to register for an
    upcoming event.

    Args:
    org_types: QuerySet of OrganizationType objects
    additional_cc_contacts: Optional set of additional contacts to CC
    additional_bcc_contacts: Optional set of additional contacts to BCC
    """
    org_types = org_types.prefetch_related(
        models.Prefetch(
            "organizations",
            queryset=Organization.objects.filter(
                include_in_invitation=True
            ).prefetch_related(
                "primary_contacts",
                "secondary_contacts",
                "government",
            ),
        )
    )

    additional_cc_contacts = set(additional_cc_contacts or [])
    additional_bcc_contacts = set(additional_bcc_contacts or [])

    org_recipients = {}
    for org_type in org_types:
        for org in org_type.organizations.filter(include_in_invitation=True).all():
            primary = set(org.primary_contacts.all())
            secondary = set(org.secondary_contacts.all())

            to_emails = set(org.emails or [])
            cc_emails = set(org.email_ccs or [])

            # If it's a GOV, include all invite-able orgs from that country
            if org_type.acronym == "GOV":
                related_orgs = Organization.objects.filter(
                    government=org.government, include_in_invitation=True
                ).prefetch_related("primary_contacts", "secondary_contacts")

                for related_organization in related_orgs:
                    primary |= set(related_organization.primary_contacts.all())
                    secondary |= set(related_organization.secondary_contacts.all())

                    to_emails |= set(related_organization.emails or [])
                    cc_emails |= set(related_organization.email_ccs or [])

            if primary:
                to_emails.update(
                    email for contact in primary for email in (contact.emails or [])
                )
                cc_emails.update(
                    email for contact in primary for email in (contact.email_ccs or [])
                )

            if secondary:
                cc_emails.update(
                    email
                    for contact in secondary
                    for email in ((contact.emails or []) + (contact.email_ccs or []))
                )

            if additional_cc_contacts:
                cc_emails.update(
                    email
                    for contact in additional_cc_contacts
                    for email in ((contact.emails or []) + (contact.email_ccs or []))
                )

            org_recipients[org] = {
                "to_contacts": primary,
                "cc_contacts": secondary | additional_cc_contacts,
                "bcc_contacts": additional_bcc_contacts,
                "to_emails": to_emails,
                "cc_emails": cc_emails,
                "bcc_emails": {
                    email
                    for contact in additional_bcc_contacts
                    for email in ((contact.emails or []) + (contact.email_ccs or []))
                },
            }

    return org_recipients
