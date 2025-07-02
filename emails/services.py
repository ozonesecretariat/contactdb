from django.db import models

from core.models import Organization


def get_organization_recipients(
    org_types,
    organizations,
    additional_cc_contacts=None,
    additional_bcc_contacts=None,
    invitation_email=None,
):
    """
    Get Contacts per organization for *invitation* emails, using the organization's
    primary and secondary contacts.

    This is useful for sending emails to users that need to register for an
    upcoming event.

    Args:
    org_types: QuerySet of OrganizationType objects (can be empty)
    organizations: QuerySet of Organization objects (can be empty)
    additional_cc_contacts: Optional set of additional contacts to CC
    additional_bcc_contacts: Optional set of additional contacts to BCC
    invitation_email: Optional InvitationEmail used to filter only unregistered orgs
    """
    # First identify governments (called them countries, but there's a subtle difference)
    # for which GOV organizations exist.
    gov_orgs = (
        Organization.objects.filter(
            organization_type__acronym="GOV",
            include_in_invitation=True,
            government__isnull=False,
        )
        .order_by("government_id")
        .distinct("government_id")
    )

    gov_countries = {org.government for org in gov_orgs if org.government}

    is_reminder = invitation_email is not None

    if is_reminder:
        # For reminders, keep only orgs that haven't registered anyone.
        # unregistered_organizations can handle both org_types / organizations list
        orgs_queryset = invitation_email.unregistered_organizations

    elif organizations:
        # For invitations, just use those orgs
        orgs_queryset = organizations.prefetch_related(
            "primary_contacts", "secondary_contacts", "government"
        )

    elif org_types:
        orgs_queryset = (
            Organization.objects.filter(
                organization_type__in=org_types, include_in_invitation=True
            )
            .prefetch_related(
                "primary_contacts",
                "secondary_contacts",
                "government",
            )
            .filter(
                # Organization is either:
                # - one of the selected GOV orgs
                # - or is not related to any GOV country
                # This avoids mails being sent both as part of a GOV-wide invitations and as
                # an individual invitation for the non-GOV organization.
                models.Q(id__in=gov_orgs.values("id"))
                | models.Q(
                    models.Q(government__isnull=True)
                    | ~models.Q(government__in=gov_countries)
                )
            )
        )

    org_recipients = {}
    for org in orgs_queryset:
        primary = set(org.primary_contacts.all())
        secondary = set(org.secondary_contacts.all())

        to_emails = set(org.emails or [])
        cc_emails = set(org.email_ccs or [])
        bcc_emails = set()

        # If it's a GOV, include all inviteable orgs from that country (incl. other GOVs)
        # TODO: not sure about the `not organizations` part.
        # TODO: ^ maybe we should simply behave the same regardless of GOV/include
        should_expand_gov = (
            org.organization_type
            and org.organization_type.acronym == "GOV"
            and (not organizations or org.include_in_invitation)
        )

        if should_expand_gov:
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
                email
                for contact in primary
                for email in (contact.emails or [])
                if email
            )
            cc_emails.update(
                email
                for contact in primary
                for email in (contact.email_ccs or [])
                if email
            )

        if secondary:
            cc_emails.update(
                email
                for contact in secondary
                for email in ((contact.emails or []) + (contact.email_ccs or []))
                if email
            )

        org_recipients[org] = {
            "to_contacts": primary,
            "cc_contacts": secondary,
            "to_emails": to_emails,
            "cc_emails": cc_emails,
            "bcc_emails": bcc_emails,
        }

    return remove_duplicated_emails(
        org_recipients, additional_cc_contacts, additional_bcc_contacts
    )


def remove_duplicated_emails(
    org_recipients, additional_cc_contacts, additional_bcc_contacts
):
    """
    Adds additional contacts to organization recipients.
    Then deduplicates email addresses and skips all orgs that
    end up not having a "to" email.

    Args:
        org_recipients: Dict of { org: { contacts & emails for "TO", "CC", "BCC" } }
        additional_cc_contacts: Set of additional contacts to CC
        additional_bcc_contacts: Set of additional contacts to BCC

    Returns:
        Updated org_recipients dict with additional contacts and deduplicated emails
    """
    additional_cc_contacts = set(additional_cc_contacts or [])
    additional_bcc_contacts = set(additional_bcc_contacts or [])

    final_org_recipients = {}

    for org, data in org_recipients.items():
        primary = data["to_contacts"]
        secondary = data["cc_contacts"]
        to_emails = data["to_emails"]
        cc_emails = data["cc_emails"]
        bcc_emails = data["bcc_emails"]

        # Add emails from additional contacts
        if additional_cc_contacts:
            cc_emails.update(
                email
                for contact in additional_cc_contacts
                for email in ((contact.emails or []) + (contact.email_ccs or []))
                if email
            )

        if additional_bcc_contacts:
            bcc_emails.update(
                email
                for contact in additional_bcc_contacts
                for email in ((contact.emails or []) + (contact.email_ccs or []))
                if email
            )

        # Only add org if there is at least one "to" email address;
        # otherwise email won't get sent and we'll just pollute the admin.
        if not to_emails:
            continue

        final_org_recipients[org] = {
            "to_contacts": primary,
            "cc_contacts": secondary | additional_cc_contacts,
            "bcc_contacts": additional_bcc_contacts
            - primary
            - (secondary | additional_cc_contacts),
            "to_emails": to_emails,
            "cc_emails": cc_emails - to_emails,
            "bcc_emails": bcc_emails - to_emails - cc_emails,
        }

    return final_org_recipients
