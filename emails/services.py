from django.db import models

from core.models import Organization


def get_organization_recipients(org_types):
    """
    Get recipients per organization for *invitation* emails, using the organization's
    primary and secondary contacts.

    This is useful for sending emails to users that need to register for an
    upcoming event.
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

    org_recipients = {}
    for org_type in org_types:
        for org in org_type.organizations.filter(include_in_invitation=True).all():
            primary = set(org.primary_contacts.all())
            secondary = set(org.secondary_contacts.all())

            if org_type.acronym == "GOV":
                # If it's a GOV, include all invite-able orgs from that country
                related_orgs = Organization.objects.filter(
                    government=org.government, include_in_invitation=True
                ).prefetch_related("primary_contacts", "secondary_contacts")
                for related_organization in related_orgs:
                    primary |= set(related_organization.primary_contacts.all())
                    secondary |= set(related_organization.secondary_contacts.all())

            if primary or secondary:
                org_recipients[org] = {
                    "to": primary,
                    "cc": secondary,
                }
    return org_recipients
