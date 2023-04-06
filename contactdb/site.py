from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig


class ContactDBAdminSite(AdminSite):
    site_title = "Ozone Contact DB"
    site_header = "Ozone Contact DB"
    index_title = "Ozone Contact DB"


class ContactDBAdminConfig(AdminConfig):
    default_site = "contactdb.site.ContactDBAdminSite"
