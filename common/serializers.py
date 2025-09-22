import mimetypes

import rest_framework.serializers
from drf_extra_fields.fields import Base64ImageField


class DateField(rest_framework.serializers.DateField):
    """Like DateField but allows empty string as input."""

    def __init__(self, *args, allow_blank=False, **kwargs):
        self.allow_blank = allow_blank
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        if data == "" and self.allow_blank:
            return None
        return super().to_internal_value(data)


class DataURIImageField(Base64ImageField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("represent_in_base64", True)
        super().__init__(*args, **kwargs)

    def to_representation(self, file):
        result = super().to_representation(file)
        if self.represent_in_base64:
            mime_type = mimetypes.guess_type(file.name)[0]
            return f"data:{mime_type};base64,{result}"
        return result
