import factory
from factory.django import DjangoModelFactory

from emails.models import Email, InvitationEmail


class EmailFactory(DjangoModelFactory):
    class Meta:
        model = Email

    subject = factory.Sequence(lambda n: f"Test Email {n}")
    content = factory.LazyAttribute(lambda obj: f"Body for {obj.subject}")
    email_type = Email.EmailTypeChoices.EVENT_NOTIFICATION
    is_reminder = False

    @factory.post_generation
    def events(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for event in extracted:
                self.events.add(event)

    @factory.post_generation
    def organizations(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for org_type in extracted:
                self.organizations.add(org_type)

    @factory.post_generation
    def recipients(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for contact in extracted:
                self.recipients.add(contact)

    @factory.post_generation
    def cc_recipients(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for contact in extracted:
                self.cc_recipients.add(contact)


class InvitationEmailFactory(DjangoModelFactory):
    class Meta:
        model = InvitationEmail

    subject = factory.Sequence(lambda n: f"Test Invitation {n}")
    content = factory.LazyAttribute(lambda obj: f"Body for {obj.subject}")
    email_type = InvitationEmail.EmailTypeChoices.EVENT_INVITE
    is_reminder = False

    @factory.post_generation
    def events(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for event in extracted:
                self.events.add(event)

    @factory.post_generation
    def organization_types(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for org_type in extracted:
                self.organization_types.add(org_type)

    @factory.post_generation
    def organizations(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for org_type in extracted:
                self.organizations.add(org_type)

    @factory.post_generation
    def cc_recipients(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for contact in extracted:
                self.cc_recipients.add(contact)

    @factory.post_generation
    def bcc_recipients(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for contact in extracted:
                self.bcc_recipients.add(contact)
