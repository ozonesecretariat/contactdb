import factory
from django.utils import timezone

from core.models import Contact, Country, Organization
from events.models import (
    Event,
    EventGroup,
    EventInvitation,
    Registration,
    RegistrationRole,
    RegistrationStatus,
)


class CountryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Country
        django_get_or_create = ("code",)

    code = factory.Sequence(lambda n: f"C{n:02}")
    name = factory.Sequence(lambda n: f"Country {n}")
    official_name = factory.LazyAttribute(lambda obj: f"Republic of {obj.name}")
    region = None
    subregion = None


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Test Organization {n}")
    acronym = factory.Sequence(lambda n: f"ORG{n}")
    emails = ["org@example.com"]
    include_in_invitation = True


class ContactFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contact

    organization = factory.SubFactory(OrganizationFactory)
    first_name = factory.Sequence(lambda n: f"First{n}")
    last_name = factory.Sequence(lambda n: f"Last{n}")
    emails = factory.LazyFunction(lambda: ["contact@example.com"])
    email_ccs = factory.LazyFunction(lambda: [])
    phones = factory.LazyFunction(lambda: [])
    mobiles = factory.LazyFunction(lambda: [])
    faxes = factory.LazyFunction(lambda: [])

    title = "Mr."
    designation = "Test Designation"
    department = "Test Department"
    primary_lang = Contact.UNLanguage.ENGLISH
    is_use_organization_address = True
    org_head = False

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for group in extracted:
                self.groups.add(group)


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    code = factory.Sequence(lambda n: f"EVT{n:03}")
    title = factory.Sequence(lambda n: f"Test Event {n}")
    start_date = factory.LazyFunction(lambda: timezone.now().date())
    end_date = factory.LazyFunction(
        lambda: (timezone.now() + timezone.timedelta(days=3)).date()
    )
    venue_city = "Test City"
    venue_country = factory.SubFactory(CountryFactory)


class EventGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EventGroup

    name = factory.Sequence(lambda n: f"Event Group {n}")
    description = factory.LazyAttribute(lambda obj: f"Description for {obj.name}")

    @factory.post_generation
    def events(self, create, extracted, **kwargs):
        """Handle M2M relationship with event (does not work out-of-the-box)."""
        if not create:
            return

        if extracted:
            self.events.set(extracted)


class EventInvitationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EventInvitation
        django_get_or_create = ("event", "organization")

    event = factory.SubFactory(EventFactory)
    organization = factory.SubFactory(OrganizationFactory)
    token = factory.Faker("uuid4")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Handles mutual exclusion (TODO!) between event and event_group."""
        if "event_group" in kwargs and not kwargs.get("event"):
            kwargs["event"] = None
        return super()._create(model_class, *args, **kwargs)


class RegistrationStatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RegistrationStatus
        django_get_or_create = ("name",)

    name = "Nominated"
    kronos_value = 1


class RegistrationRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RegistrationRole
        django_get_or_create = ("name",)

    name = "Participant"
    kronos_value = 1


class RegistrationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Registration

    contact = factory.SubFactory(ContactFactory)
    event = factory.SubFactory("events.tests.factories.EventFactory")
    status = factory.SubFactory(RegistrationStatusFactory)
    role = factory.SubFactory(RegistrationRoleFactory)
    date = factory.LazyFunction(timezone.now)
    is_funded = False
    priority_pass_code = ""
