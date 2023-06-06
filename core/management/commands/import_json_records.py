import json
from django.core.management.base import BaseCommand
from core.models import Organization, RegistrationStatus, Record, KronosEvent


class Command(BaseCommand):
    help = "Import JSON records"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            help="Path to file",
        )

    def handle(self, *args, **options):
        def check_field(field, subfield):
            if subfield == "role" or subfield == "dateOfBirth":
                return field[subfield] if subfield in field else None
            if subfield == "tags":
                return field[subfield] if subfield in field else []
            return field[subfield] if subfield in field else ""

        with open(options["path"], "r") as f:
            json_obj = json.load(f)
            for record in json_obj["records"]:
                organization, _ = Organization.objects.get_or_create(
                    organization_id=record["organization"]["organizationId"],
                    name=record["organization"]["name"],
                    acronym=record["organization"]["acronym"],
                    organization_type_id=record["organization"]["organizationTypeId"],
                    organization_type=record["organization"]["organizationType"],
                    government=check_field(record["organization"], "government"),
                    government_name=check_field(
                        record["organization"], "governmentName"
                    ),
                    country=check_field(record["organization"], "country"),
                    country_name=check_field(record["organization"], "countryName"),
                )
                contact, _ = Record.objects.get_or_create(
                    contact_id=record["contactId"],
                    organization=organization,
                    title=record["title"],
                    first_name=record["firstName"],
                    last_name=record["lastName"],
                    designation=record["designation"],
                    department=record["department"],
                    affiliation=record["affiliation"],
                    phones=record["phones"],
                    mobiles=record["mobiles"],
                    faxes=record["faxes"],
                    emails=record["emails"],
                    email_ccs=record["emailCcs"],
                    notes=record["notes"],
                    is_in_mailing_list=record["isInMailingList"],
                    is_use_organization_address=record["isUseOrganizationAddress"],
                    address=check_field(record, "address"),
                    city=check_field(record, "city"),
                    state=check_field(record, "state"),
                    country=check_field(record, "country"),
                    postal_code=check_field(record, "postalCode"),
                    birth_date=check_field(record, "dateOfBirth"),
                )
                for registration in record["registrationStatuses"]:
                    RegistrationStatus.objects.get_or_create(
                        contact=contact,
                        event=KronosEvent.objects.filter(
                            event_id=registration.get("eventId")
                        ).first(),
                        code=registration["code"],
                        status=registration["status"],
                        date=registration["date"],
                        is_funded=registration["isFunded"],
                        role=check_field(registration, "role"),
                        priority_pass_code=check_field(
                            registration, "priorityPassCode"
                        ),
                        tags=check_field(registration, "tags"),
                    )
