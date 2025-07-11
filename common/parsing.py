import re
import string

punctuation_translate = {ord(c): " " for c in string.punctuation}
CONTACT_MAPPING = {
    "organization": "organization",
    "title": "title",
    "firstName": "first_name",
    "lastName": "last_name",
    "designation": "designation",
    "department": "department",
    "phones": "phones",
    "mobiles": "mobiles",
    "faxes": "faxes",
    "emails": "emails",
    "emailCcs": "email_ccs",
    "notes": "notes",
    "isUseOrganizationAddress": "is_use_organization_address",
    "address": "address",
    "city": "city",
    "state": "state",
    "country": "country",
    "postalCode": "postal_code",
    "dateOfBirth": "birth_date",
}
REGISTRATION_MAPPING = {
    "contactId": "contact_id",
    "eventId": "event_id",
    "status": "status",
    "role": "role",
    "priorityPassCode": "priority_pass_code",
    "createdOn": "date",
    "isFunded": "is_funded",
}


def remove_punctuation(value: str):
    return value.translate(punctuation_translate)


def parse_list(email_list):
    if isinstance(email_list, str):
        email_list = [email_list]

    result = set()
    for item in email_list:
        for addr in re.split(r"[;,]", item):
            if addr := str(addr).strip():
                result.add(addr)

    return sorted(result)
