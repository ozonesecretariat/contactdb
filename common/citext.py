from django.db.models import CharField, EmailField, TextField


# Django is deprecating support for CIText, so ship our own instead.
# The alternative of using a non-deterministic DB collation has one big
# downside: no support for LIKE. So makes searches on such columns impossible.


class CIText:
    def get_internal_type(self):
        return "CI" + super().get_internal_type()

    def db_type(self, connection):
        return "citext"


class CICharField(CIText, CharField):
    pass


class CIEmailField(CIText, EmailField):
    pass


class CITextField(CIText, TextField):
    pass
