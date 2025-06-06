import factory
from factory.django import DjangoModelFactory

from emails.models import InvitationEmail


class InvitationEmailFactory(DjangoModelFactory):
    class Meta:
        model = InvitationEmail

    subject = factory.Sequence(lambda n: f"Test Invitation {n}")
    content = factory.LazyAttribute(lambda obj: f"Body for {obj.subject}")

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
