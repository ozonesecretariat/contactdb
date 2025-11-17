import django_filters
from constance import config
from django.contrib.auth.decorators import permission_required
from django.db.models import Max
from django.http import FileResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action

from api.serializers.priority_pass import PriorityPassSerializer
from common.filters import CamelCaseOrderingFilter
from common.pdf import print_pdf
from events.models import PriorityPass


class PriorityPassFilterSet(FilterSet):
    is_recent = django_filters.BooleanFilter(method="filter_is_recent")

    class Meta:
        model = PriorityPass
        fields = ["is_recent"]

    def filter_is_recent(self, queryset, name, value):
        today = timezone.now().date() - timezone.timedelta(
            days=config.RECENT_EVENTS_DAYS
        )

        if value is True:
            return queryset.filter(registrations__event__end_date__gte=today)
        if value is False:
            return queryset.filter(registrations__event__end_date__lt=today)
        return queryset


class PriorityPassViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "code"
    lookup_url_kwarg = "code"
    serializer_class = PriorityPassSerializer
    queryset = (
        PriorityPass.objects.all()
        .annotate(latest_event_date=Max("registrations__event__start_date"))
        .prefetch_related(
            "registrations",
            "registrations__role",
            "registrations__contact",
            "registrations__contact__country",
            "registrations__contact__organization",
            "registrations__contact__organization__country",
            "registrations__contact__organization__government",
            "registrations__organization",
            "registrations__organization__country",
            "registrations__organization__government",
            "registrations__event",
            "registrations__event__venue_country",
        )
        .order_by("-latest_event_date")
        .distinct()
    )
    filter_backends = (
        filters.SearchFilter,
        CamelCaseOrderingFilter,
        DjangoFilterBackend,
    )
    search_fields = (
        "code",
        "registrations__event__code",
        "registrations__event__title__unaccent",
        "registrations__contact__first_name__unaccent",
        "registrations__contact__last_name__unaccent",
        "registrations__contact__emails",
        "registrations__contact__email_ccs",
        "registrations__contact__phones",
        "registrations__contact__organization__name__unaccent",
        "registrations__organization__name__unaccent",
    )
    filterset_class = PriorityPassFilterSet

    @method_decorator(
        permission_required("events.view_registration", raise_exception=True)
    )
    @action(detail=True, methods=["get"])
    def print_badge(self, *args, **kwargs):
        priority_pass = self.get_object()
        include_back_side = self.request.GET.get("include_back_side", "true") == "true"
        return FileResponse(
            print_pdf(
                priority_pass.badge_template,
                context={
                    **priority_pass.priority_pass_context,
                    "include_back_side": include_back_side,
                },
                request=self.request,
            ),
            content_type="application/pdf",
            filename=f"badge_{priority_pass.code}.pdf",
            as_attachment=self.request.GET.get("download") == "true",
        )
