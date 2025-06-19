import rest_framework.permissions
from rest_framework.exceptions import PermissionDenied

from core.models import Contact


class DjangoModelPermissions(rest_framework.permissions.DjangoModelPermissions):
    """Also enforces the view permission, unlike the rest_framework default."""

    perms_map = {
        **rest_framework.permissions.DjangoModelPermissions.perms_map,
        "GET": ["%(app_label)s.view_%(model_name)s"],
    }


class OrganizationResourcePermission(rest_framework.permissions.BasePermission):
    """
    Generic permission for organization-related resources.

    Any view using this should implement a get_organization_context() mthod,
    returning an `Organization` object.
    """

    def has_permission(self, request, view):
        if request.method in rest_framework.permissions.SAFE_METHODS:
            return True

        # Skip validation if no organization context available
        if not hasattr(view, "get_organization_context"):
            return True

        org_context = view.get_organization_context()
        if not org_context:
            return True

        # Get resources to validate
        resources = self.get_resources_to_validate(request)
        if not resources:
            return True

        # Check if all resources belong to organization
        return self.validate_organization_membership(resources, org_context)

    def get_resources_to_validate(self, request):
        """Override this to specify which resources to check."""
        return []

    def validate_organization_membership(self, resources, organizations):
        """Override this to implement specific validation logic."""
        return True


class ContactNominationPermission(OrganizationResourcePermission):
    """
    Specific permission for contact nominations,
    based on the generic OrganizationResourcePermission.
    """

    def get_resources_to_validate(self, request):
        if request.method == "POST" and request.data.get("nominations"):
            return [n.get("contact") for n in request.data.get("nominations", [])]
        return []

    def validate_organization_membership(self, contact_ids, organizations):
        if not contact_ids:
            return True

        valid_contacts = Contact.objects.filter(
            id__in=contact_ids, organization__in=organizations
        ).count()

        if valid_contacts != len(contact_ids):
            raise PermissionDenied("Cannot nominate contacts from other organizations")

        return True
