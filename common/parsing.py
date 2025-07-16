import re
import string

punctuation_translate = {ord(c): " " for c in string.punctuation}

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
