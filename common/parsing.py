import re
import string

from core.models import BaseContact

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

FIX_TITLE_MAPPING = {
    "Mr": "Mr.",
    "Ms": "Ms.",
    "Mrs": "Ms.",
    "Mrs.": "Ms.",
    "Mme": "Mme.",
}

LOCALIZED_TITLE_TO_ENGLISH = {
    # French
    "M.": "Mr.",
    "Mme.": "Ms.",
    "H.E. M.": "H.E. Mr.",
    "H.E. Mme.": "H.E. Ms.",
    "Hon. M.": "Hon. Mr.",
    "Hon. Mme.": "Hon. Ms.",
    # Spanish
    "Sr.": "Mr.",
    "Sra.": "Ms.",
    "H.E. Sr.": "H.E. Mr.",
    "H.E. Sra.": "H.E. Ms.",
    "Hon. Sr.": "Hon. Mr.",
    "Hon. Sra.": "Hon. Ms.",
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


def normalize_title(raw_title):
    """
    Normalize and return (english_title, localized_title) tuple.
    """

    title = FIX_TITLE_MAPPING.get(raw_title, raw_title)

    english_title = LOCALIZED_TITLE_TO_ENGLISH.get(title, title)
    english_title = english_title if english_title in BaseContact.Title.values else ""
    localized_title = title if title in BaseContact.LocalizedTitle.values else ""

    return english_title, localized_title
