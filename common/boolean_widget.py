from import_export import widgets


class BooleanWidget(widgets.BooleanWidget):
    """Same as the parent class but add more true/false values."""

    TRUE_VALUES = ["yes", "y" "1", 1, True, "true", "TRUE", "True"]
    FALSE_VALUES = ["no", "n", "0", 0, False, "false", "FALSE", "False"]
    NULL_VALUES = ["", None, "null", "NULL", "none", "NONE", "None"]
