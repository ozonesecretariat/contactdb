from django.db import models


class KronosId(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 24)
        kwargs.setdefault("null", True)
        kwargs.setdefault("blank", True)
        kwargs.setdefault("unique", True)
        kwargs.setdefault("editable", False)
        kwargs.setdefault(
            "help_text",
            (
                "Unique Kronos ID. Will not be available if record "
                "was not imported from Kronos."
            ),
        )
        kwargs.setdefault("verbose_name", "Kronos ID")
        super().__init__(*args, **kwargs)


class KronosEnum(models.IntegerField):
    def __init__(self, *args, **kwargs):
        # Default to -1 as some Kronos Enums actually have meaning behind
        # null/undefined
        kwargs.setdefault("default", -1)
        kwargs.setdefault("blank", True)
        kwargs.setdefault("null", True)
        kwargs.setdefault("editable", False)
        kwargs.setdefault(
            "help_text",
            (
                "Unique Kronos Enum value. Will not be available if record "
                "was not imported from Kronos."
            ),
        )
        super().__init__(*args, **kwargs)
