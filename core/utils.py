def check_field(field, subfield):
    if subfield == "role" or subfield == "dateOfBirth":
        return field[subfield] if subfield in field else None
    if subfield == "tags":
        return field[subfield] if subfield in field else []
    return field[subfield] if subfield in field else ""
