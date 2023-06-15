import pytest
from django.urls import reverse

from core.models import (
    KronosEvent,
    LoadKronosEventsTask,
    LoadKronosParticipantsTask,
    Record,
    RegistrationStatus,
    Organization,
    ResolveAllConflictsTask,
)
from core.parsers import KronosParticipantsParser, KronosEventsParser
from core.temp_models import create_temporary_table, TemporaryContact
from core.utils import ConflictResolutionMethods

pytestmark = [pytest.mark.django_db]


def test_create_import_events_task(login_user_can_import, mocker):
    client, user = login_user_can_import
    mocker.patch.object(LoadKronosEventsTask, "run")

    assert LoadKronosEventsTask.objects.count() == 0

    response = client.post(reverse("kronos-events-import"))

    assert response.status_code == 302
    LoadKronosEventsTask.run.assert_called_once()
    assert LoadKronosEventsTask.objects.count() == 1


def test_kronos_events_parser():
    event_list = [
        {
            "eventId": "520000000000000000165b",
            "code": "000",
            "title": "\tWorkshop low-GWP alternatives to HFCs",
            "startDate": "2017-07-10T00:00:00Z",
            "endDate": "2018-07-10T00:00:00Z",
            "venueCountry": "ok",
            "venueCity": "City",
            "dates": "10 July 2017",
        },
        {
            "eventId": "52000000000000c00001606",
            "code": "0000-39",
            "title": "39th Meeting Protocol",
            "startDate": "2017-07-11T00:00:00Z",
            "endDate": "2017-07-14T00:00:00Z",
            "venueCountry": "ok",
            "venueCity": "City",
            "dates": "11 - 14 July 2017",
        },
        {
            "eventId": "52000000000000c00001607",
            "code": "000000",
            "title": "59th Meeting Procedure of the Montreal Protocol",
            "startDate": "2017-11-18T00:00:00Z",
            "endDate": "2017-11-18T00:00:00Z",
            "venueCountry": "ok",
            "venueCity": "City",
            "dates": "18 November 2017",
        },
    ]

    parser = KronosEventsParser()
    parser.parse_event_list(event_list)

    assert KronosEvent.objects.count() == 3
    assert KronosEvent.objects.filter(event_id="520000000000000000165b").count() == 1
    assert KronosEvent.objects.filter(event_id="52000000000000c00001606").count() == 1
    assert KronosEvent.objects.filter(event_id="52000000000000c00001607").count() == 1


def test_create_import_participants_task(login_user_can_import, kronos_event, mocker):
    client, user = login_user_can_import

    kronos_event.save()

    mocker.patch.object(LoadKronosParticipantsTask, "run")

    assert LoadKronosEventsTask.objects.count() == 0

    response = client.post(
        reverse("kronos-participants-import"),
        {"events": [kronos_event.pk]},
        follow=False,
    )

    assert response.status_code == 302
    LoadKronosParticipantsTask.run.assert_called_once()
    assert LoadKronosParticipantsTask.objects.count() == 1


def test_kronos_participants_parser(kronos_event):
    kronos_event.save()
    contact_list = [
        {
            "organization": {
                "organizationId": "60008f4b0000437400016002",
                "name": "Organization",
                "acronym": "",
                "organizationTypeId": "60008f4b60008f4b60008f4b",
                "organizationType": "GOV",
                "government": "ok",
                "governmentName": "Ok",
                "country": "ok",
                "countryName": "Ok",
            },
            "registrationStatuses": [
                {
                    "eventId": "52000000cbd0495c00001879",
                    "code": "GGG-MOP-34",
                    "status": 4,
                    "date": "2022-10-31T13:54:47.914Z",
                    "isFunded": False,
                }
            ],
            "contactId": "5959ec2af439c413049fc55e",
            "organizationId": "60008f4b0000437400016002",
            "organizationType": "GOV",
            "title": "Ms.",
            "firstName": "Other",
            "lastName": "Record",
            "designation": "Montreal Protocol and Vienna Convention Focal Point",
            "department": "National Ozone Unit",
            "affiliation": "",
            "phones": ["+37422222222"],
            "mobiles": ["+37444444446"],
            "faxes": [],
            "emails": ["other@test.com"],
            "emailCcs": [],
            "notes": "Picture #324200106\r\n##E\r\n##R",
            "isInMailingList": False,
            "isUseOrganizationAddress": True,
            "address": "",
            "city": "City",
            "state": "",
            "country": "ok",
            "postalCode": "0010",
            "createdOn": "2017-07-03T07:03:06.89Z",
            "createdBy": "Admin",
            "updatedOn": "2020-10-26T08:24:37.365Z",
            "updatedBy": "Registration",
        },
        {
            "organization": {
                "organizationId": "60008f4b0000437400016003",
                "name": "Department of Agriculture, Water and the Environment",
                "acronym": "",
                "organizationTypeId": "594bce8594bce8594bce8ff",
                "organizationType": "GOV",
                "government": "ok",
                "governmentName": "Ok",
                "country": "ok",
                "countryName": "Ok",
            },
            "registrationStatuses": [
                {
                    "eventId": "52000000cbd0495c00001879",
                    "code": "OOOOO-MOP-34",
                    "status": 4,
                    "date": "2022-10-30T16:57:48.138Z",
                    "isFunded": False,
                    "role": 1,
                    "priorityPassCode": "Q94CJPMHK7",
                }
            ],
            "contactId": "5959ecdaf439c413049fc561",
            "organizationId": "60008f4b0000437400016003",
            "organizationType": "GOV",
            "title": "Mr.",
            "firstName": "Alex",
            "lastName": "Alexandrescu",
            "designation": "Assistant Director",
            "department": "Ozone and Climate Protection Section",
            "affiliation": "",
            "phones": ["+6111111111"],
            "mobiles": ["+6122222222"],
            "faxes": [],
            "emails": ["alex.alex@test.com"],
            "emailCcs": [],
            "notes": "Picture #324200001\r\n##E\r\n",
            "isInMailingList": False,
            "isUseOrganizationAddress": True,
            "address": "",
            "city": "City",
            "state": "",
            "country": "ok",
            "postalCode": "",
            "createdOn": "2017-07-03T07:06:02.998Z",
            "createdBy": "Admin",
            "updatedOn": "2020-12-02T16:48:11.127Z",
            "updatedBy": "Admin",
        },
    ]

    parser = KronosParticipantsParser()
    parser.parse_contact_list(contact_list)

    assert Record.objects.count() == 2
    assert Record.objects.filter(contact_id="5959ec2af439c413049fc55e").count() == 1
    assert Record.objects.filter(contact_id="5959ecdaf439c413049fc561").count() == 1
    assert RegistrationStatus.objects.count() == 2
    assert Organization.objects.count() == 2


def test_kronos_participants_parser_conflict(
    kronos_event, first_organization, other_contact
):
    first_organization.save()
    other_contact.save()
    kronos_event.save()

    create_temporary_table()

    contact_list = [
        {
            "organization": {
                "organizationId": "60008f4b0000437400016002",
                "name": "Organization",
                "acronym": "",
                "organizationTypeId": "60008f4b60008f4b60008f4b",
                "organizationType": "GOV",
                "government": "ok",
                "governmentName": "Ok",
                "country": "ok",
                "countryName": "Ok",
            },
            "registrationStatuses": [
                {
                    "eventId": "52000000cbd0495c00001879",
                    "code": "GGG-MOP-34",
                    "status": 4,
                    "date": "2022-10-31T13:54:47.914Z",
                    "isFunded": False,
                }
            ],
            "contactId": "5959ec2af439c413049fc55e",
            "organizationId": "60008f4b0000437400016002",
            "organizationType": "GOV",
            "title": "Ms.",
            "firstName": "Other",
            "lastName": "Record",
            "designation": "Montreal Protocol and Vienna Convention Focal Point",
            "department": "National Ozone Unit",
            "affiliation": "",
            "phones": ["+37422222222"],
            "mobiles": ["+37444444446"],
            "faxes": [],
            "emails": ["other@test.com"],
            "emailCcs": [],
            "notes": "Picture #324200106\r\n##E\r\n##R",
            "isInMailingList": False,
            "isUseOrganizationAddress": True,
            "address": "",
            "city": "City",
            "state": "",
            "country": "ok",
            "postalCode": "0010",
            "createdOn": "2017-07-03T07:03:06.89Z",
            "createdBy": "Admin",
            "updatedOn": "2020-10-26T08:24:37.365Z",
            "updatedBy": "Registration",
        },
        {
            "organization": {
                "organizationId": "60008f4b0000437400016003",
                "name": "Department of Agriculture, Water and the Environment",
                "acronym": "",
                "organizationTypeId": "594bce8594bce8594bce8ff",
                "organizationType": "GOV",
                "government": "ok",
                "governmentName": "Ok",
                "country": "ok",
                "countryName": "Ok",
            },
            "registrationStatuses": [
                {
                    "eventId": "52000000cbd0495c00001879",
                    "code": "OOOOO-MOP-34",
                    "status": 4,
                    "date": "2022-10-30T16:57:48.138Z",
                    "isFunded": False,
                    "role": 1,
                    "priorityPassCode": "Q94CJPMHK7",
                }
            ],
            "contactId": "5959ecdaf439c413049fc561",
            "organizationId": "60008f4b0000437400016003",
            "organizationType": "GOV",
            "title": "Mr.",
            "firstName": "Alex",
            "lastName": "Alexandrescu",
            "designation": "Assistant Director",
            "department": "Ozone and Climate Protection Section",
            "affiliation": "",
            "phones": ["+6111111111"],
            "mobiles": ["+6122222222"],
            "faxes": [],
            "emails": ["alex.alex@test.com"],
            "emailCcs": [],
            "notes": "Picture #324200001\r\n##E\r\n",
            "isInMailingList": False,
            "isUseOrganizationAddress": True,
            "address": "",
            "city": "City",
            "state": "",
            "country": "ok",
            "postalCode": "",
            "createdOn": "2017-07-03T07:06:02.998Z",
            "createdBy": "Admin",
            "updatedOn": "2020-12-02T16:48:11.127Z",
            "updatedBy": "Admin",
        },
    ]

    parser = KronosParticipantsParser()
    parser.parse_contact_list(contact_list)

    assert Record.objects.count() == 2
    assert Record.objects.filter(contact_id="5959ec2af439c413049fc55e").count() == 0
    assert Record.objects.filter(contact_id="5959ecdaf439c413049fc561").count() == 1
    assert (
        TemporaryContact.objects.filter(contact_id="5959ec2af439c413049fc55e").count()
        == 1
    )
    assert RegistrationStatus.objects.count() == 2
    assert (
        Organization.objects.filter(organization_id="60008f4b0000437400016002").count()
        == 1
    )
    assert (
        Organization.objects.filter(organization_id="60008f4b0000437400016003").count()
        == 1
    )


def test_create_resolve_all_conflicts_task(login_user_can_import, mocker):
    client, user = login_user_can_import

    mocker.patch.object(ResolveAllConflictsTask, "run")

    assert ResolveAllConflictsTask.objects.count() == 0

    response = client.post(
        reverse("resolve-all-conflicts"),
        {"method": ConflictResolutionMethods.KEEP_OLD_DATA},
        follow=False,
    )

    assert response.status_code == 302
    ResolveAllConflictsTask.run.assert_called_once()
    assert ResolveAllConflictsTask.objects.count() == 1


def test_resolve_all_conflicts_task_keep_old_data(
    create_temporary_contact_table_and_drop_trigger,
    first_organization,
    other_contact,
    temporary_contact,
    snd_organization,
    third_contact,
    snd_temporary_contact,
):
    first_organization.save()
    other_contact.save()
    temporary_contact.save()
    snd_organization.save()
    third_contact.save()
    snd_temporary_contact.save()

    task = ResolveAllConflictsTask.objects.create(
        method=ConflictResolutionMethods.KEEP_OLD_DATA
    )
    task.run(is_async=False)

    other_contact.refresh_from_db()
    third_contact.refresh_from_db()

    assert other_contact.department == "Minister of Agriculture"
    assert other_contact.designation == "President"
    assert other_contact.email_ccs == []
    assert third_contact.department == "Department"
    assert third_contact.designation == "Designation"
    assert third_contact.email_ccs == []


def test_resolve_all_conflicts_task_save_incoming_data(
    create_temporary_contact_table_and_drop_trigger,
    first_organization,
    other_contact,
    temporary_contact,
    snd_organization,
    third_contact,
    snd_temporary_contact,
):
    first_organization.save()
    other_contact.save()
    temporary_contact.save()
    snd_organization.save()
    third_contact.save()
    snd_temporary_contact.save()

    task = ResolveAllConflictsTask.objects.create(
        method=ConflictResolutionMethods.SAVE_INCOMING_DATA
    )
    task.run(is_async=False)

    other_contact.refresh_from_db()
    third_contact.refresh_from_db()

    assert other_contact.department == "Minister of Defence"
    assert other_contact.designation == "Secretary"
    assert other_contact.email_ccs == ["email@test.com"]
    assert third_contact.department == "New Department"
    assert third_contact.designation == "New Designation"
    assert third_contact.email_ccs == ["email2@test.com"]


def test_resolve_conflict_keep_old_data(
    login_user_can_import,
    create_temporary_contact_table_and_drop_trigger,
    first_organization,
    other_contact,
    temporary_contact,
):
    first_organization.save()
    other_contact.save()
    temporary_contact.save()

    client, user = login_user_can_import
    url = reverse("resolve-conflict")

    response = client.post(
        url,
        {
            "method": ConflictResolutionMethods.KEEP_OLD_DATA,
            "incoming_contact": temporary_contact.pk,
        },
        follow=False,
    )

    other_contact.refresh_from_db()

    assert response.status_code == 302
    assert other_contact.department == "Minister of Agriculture"
    assert other_contact.designation == "President"
    assert other_contact.email_ccs == []


def test_resolve_conflict_save_incoming_data(
    login_user_can_import,
    create_temporary_contact_table_and_drop_trigger,
    first_organization,
    other_contact,
    temporary_contact,
):
    first_organization.save()
    other_contact.save()
    temporary_contact.save()

    client, user = login_user_can_import
    url = reverse("resolve-conflict")

    response = client.post(
        url,
        {
            "method": ConflictResolutionMethods.SAVE_INCOMING_DATA,
            "incoming_contact": temporary_contact.pk,
        },
        follow=False,
    )

    other_contact.refresh_from_db()

    assert response.status_code == 302
    assert other_contact.department == "Minister of Defence"
    assert other_contact.designation == "Secretary"
    assert other_contact.email_ccs == ["email@test.com"]
