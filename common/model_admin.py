from functools import wraps

from colorfield.fields import ColorField
from django.contrib import admin
from django.contrib.admin.options import get_content_type_for_model
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.safestring import mark_safe
from django_task.admin import TaskAdmin as BaseTaskAdmin
from import_export import resources, widgets

from common.boolean_widget import BooleanWidget
from common.urls import reverse


class _QuerysetMixIn:
    prefetch_related = ()
    annotate_query = {}

    def get_queryset(self, *args, **kwargs):
        query = super().get_queryset(*args, **kwargs)
        if self.annotate_query:
            query = query.annotate(**self.annotate_query)
        if self.prefetch_related:
            query = query.prefetch_related(*self.prefetch_related)
        return query


def maybe_redirect(func):
    @wraps(func)
    def inner_func(self, request, *args, **kwargs):
        original_response = func(self, request, *args, **kwargs)
        redirect_to = request.POST.get(
            self.redirect_field_name, request.GET.get(self.redirect_field_name)
        )
        url_is_safe = url_has_allowed_host_and_scheme(
            url=redirect_to,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
        if redirect_to and url_is_safe:
            return redirect(redirect_to)

        return original_response

    return inner_func


class _CustomModelAdminMixIn(_QuerysetMixIn, admin.ModelAdmin):
    show_index_page_count = False
    list_per_page = 20
    redirect_field_name = "next"
    view_fieldsets = ()

    def get_inline_action(self, obj, tool_name, classes=""):
        tool = getattr(self, tool_name)
        label = getattr(tool, "label", tool_name.replace("_", " ").capitalize())
        url = reverse(
            "admin:%s_%s_actions" % self.opt_info,
            kwargs={
                "pk": obj.pk,
                "tool": tool_name,
            },
        )
        return f'<a href="{url}" class="button {classes}">{label}</a>'

    def get_index_page_count(self):
        return self.model.objects.count()

    @property
    def opt_info(self):
        return self.opts.app_label, self.opts.model_name

    def get_fieldsets(self, request, obj=None):
        if obj and self.view_fieldsets:
            return self.view_fieldsets
        return super().get_fieldsets(request, obj=obj)

    def get_admin_template(self, name):
        return (f"admin/{self.opts.app_label}/{self.opts.model_name}/{name}",)

    @maybe_redirect
    def response_post_save_change(self, request, obj):
        return super().response_post_save_change(request, obj)

    def get_admin_list_link(self, model, query=None):
        opts = model._meta
        return reverse(
            f"admin:{opts.app_label}_{opts.model_name}_changelist", query=query
        )

    def get_object_display_link(self, obj, text=None):
        if not obj:
            return self.get_empty_value_display()

        opts = obj.__class__._meta
        url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_change", args=(obj.pk,)
        )
        return format_html(
            '<a href="{url}">{link_text}</a>', url=url, link_text=text or obj
        )

    def get_admin_list_filter_link(self, obj, name, filter_name, extra_filters=None):
        related_model = getattr(obj, name).model

        return self.get_admin_list_link(
            related_model,
            query={
                **(extra_filters or {}),
                filter_name: obj.pk,
            },
        )

    def get_related_link(self, obj, name, filter_name, text=None, extra_filters=None):
        if text is None:
            text = name.replace("_", " ").title()
        url = self.get_admin_list_filter_link(
            obj, name, filter_name, extra_filters=extra_filters
        )

        return format_html('<a href="{url}">{link_text}</a>', url=url, link_text=text)

    def get_m2m_links(self, objects):
        result = []
        for obj in objects:
            result.append(f"<li>{self.get_object_display_link(obj)}</li>")

        result = "\n".join(result)
        return mark_safe(f'<ul class="m2m-list">{result}</ul>')

    def get_intermediate_response(
        self, template, request, queryset, extra_context=None
    ):
        action_name = request.POST.get("action") or request.GET.get("action")
        if not action_name:
            raise ValueError("Action name is required in request parameters")

        description = self._get_action_description(
            getattr(self, action_name), action_name
        )

        if request.method == "POST":
            selected_action = request.POST.getlist("_selected_action")
            select_across = request.POST.get("select_across", "0")
            index = request.POST.get("index", "0")
        else:
            # We also need to support GET requests for form display
            # Using some sane defaults in that case
            selected_action = [str(obj.pk) for obj in queryset]
            select_across = "0"
            index = "0"

        return TemplateResponse(
            request,
            template,
            {
                "queryset": queryset,
                "opts": self.opts,
                "description": description,
                "title": description,
                # Initial POST or GET
                "action": action_name,
                "selected_action": selected_action,
                "select_across": select_across,
                "index": index,
                # Anything extra
                **(extra_context or {}),
            },
        )

    def history_view(self, request, object_id, extra_context=None):
        return redirect(
            reverse(
                "admin:auditlog_logentry_changelist",
                query={
                    "object_pk": object_id,
                    "resource_type": get_content_type_for_model(self.model).id,
                },
            )
        )

    def get_list_display(self, request):
        list_display = list(super().get_list_display(request))

        for field in self.model._meta.get_fields():
            if not isinstance(field, ColorField):
                continue

            try:
                index = list_display.index(field.name)
            except ValueError:
                continue

            preview_name = f"{field.name}_preview"

            if not hasattr(self, preview_name):
                # Dynamically create a preview method
                def _preview(self, obj, fname=field.name):
                    color = getattr(obj, fname)
                    return format_html(
                        """
                            <div class="color-field">
                                <div class="color-preview" style="background-color: {color}"></div> 
                                <div>{color}<div>
                            </div>
                        """,
                        color=color,
                    )

                _preview.short_description = field.name.replace("_", " ")
                _preview.admin_order_field = field.name
                setattr(self.__class__, preview_name, _preview)
            list_display[index] = preview_name

        return tuple(list_display)


class ModelAdmin(_CustomModelAdminMixIn, admin.ModelAdmin):
    pass


class TaskAdmin(_CustomModelAdminMixIn, BaseTaskAdmin):
    def get_list_display(self, request):
        return self.list_display

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Repeat")
    def repeat_action(self, obj):
        info = self.model._meta.app_label, self.model._meta.model_name
        url = reverse("admin:%s_%s_repeat" % info, args=(obj.id,))
        return format_html('<a href="{}">Repeat</a>', url)


class ModelResource(_QuerysetMixIn, resources.ModelResource):
    @classmethod
    def widget_from_django_field(cls, f, default=widgets.Widget):
        internal_type = ""
        if callable(getattr(f, "get_internal_type", None)):
            internal_type = f.get_internal_type()

        if internal_type in ("BooleanField", "NullBooleanField"):
            return BooleanWidget
        return super().widget_from_django_field(f, default=default)
