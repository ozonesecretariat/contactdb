import django_filters
from djangorestframework_camel_case.util import underscoreize
from rest_framework import filters


class CamelCaseOrderingFilter(filters.OrderingFilter):
    def get_ordering(self, request, queryset, view):
        params = request.query_params.get(self.ordering_param)
        if params:
            fields = dict.fromkeys([param.strip() for param in params.split(",")], None)
            fields = list(underscoreize(fields).keys())
            ordering = self.remove_invalid_fields(queryset, fields, view, request)
            if ordering:
                return ordering

        # No ordering was included, or all the ordering fields were invalid
        return self.get_default_ordering(view)


class CharInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    pass
