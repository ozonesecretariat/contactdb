def get_organization_recipients(org_types):
    """
    Get recipients per organization for invitation emails, using the organization's
    primary and secondary contacts.

    This is useful for sending emails to users that need to register for an
    upcoming event.
    """
    org_recipients = {}
    for org_type in org_types:
        for org in org_type.organizations.filter(
            include_in_invitation=True
        ).prefetch_related("primary_contacts", "secondary_contacts"):
            primary = set(org.primary_contacts.all())
            secondary = set(org.secondary_contacts.all())
            if primary or secondary:
                org_recipients[org] = {
                    "to": primary,
                    "cc": secondary,
                }
    return org_recipients
