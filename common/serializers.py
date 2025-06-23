import rest_framework.serializers


class DateField(rest_framework.serializers.DateField):
    """Like DateField but allows empty string as input."""

    def __init__(self, *args, allow_blank=False, **kwargs):
        self.allow_blank = allow_blank
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        if data == "" and self.allow_blank:
            return None
        return super().to_internal_value(data)
