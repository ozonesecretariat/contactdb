import re
import string

punctuation_translate = {ord(c): " " for c in string.punctuation}

title_map = {
    "Mr": "Mr.",
    "Ms": "Ms.",
    "Mrs": "Ms.",
    "Mrs.": "Ms.",
    "Mme": "Mme.",
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
