def get_event_registered_recipients(events):
    """
    Gets all contacts registered for given events queryset.

    This is useful for sending emails to users registered to an event.
    """
    recipients = set()
    for event in events.prefetch_related("registrations", "registrations__contact"):
        recipients.update(reg.contact for reg in event.registrations.all())
    return recipients


def get_organization_recipients(org_types):
    """
    Get recipients per organization for invitation emails, using the organization's
    primary and secondary contacts.

    This is useful for sending emails to users that need to register for an
    upcoming event.
    """
    org_recipients = {}
    for org_type in org_types:
        for org in org_type.organizations.all():
            primary = set(org.primary_contacts.all())
            secondary = set(org.secondary_contacts.all())
            if primary or secondary:
                org_recipients[org] = {
                    "to": primary,
                    "cc": secondary,
                }
    return org_recipients
