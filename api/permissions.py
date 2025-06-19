import rest_framework
import rest_framework.permissions
from rest_framework.exceptions import PermissionDenied

from core.models import Contact
from events.models import EventInvitation


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

    def validate_organization_membership(self, resources, organization):
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

    def validate_organization_membership(self, contact_ids, organization):
        if not contact_ids:
            return True

        valid_contacts = Contact.objects.filter(
            id__in=contact_ids, organization=organization
        ).count()

        if valid_contacts != len(contact_ids):
            raise PermissionDenied("Cannot nominate contacts from other organizations")

        return True


class PhotoAccessPermission(rest_framework.permissions.BasePermission):
    """
    Allows access to a contact photo if:
    - the user is staff
    or
    - the request includes a valid nomination token and the contact belongs to the
      invited organization/country (taking GOV into account).
    """

    def has_permission(self, request, view):
        if request.method not in rest_framework.permissions.SAFE_METHODS:
            return False

        # Staff can access any contact photo
        if request.user.is_authenticated and request.user.is_staff:
            return True

        # For anonymous access, require both nomination UUID and photo UUID
        photo_token = view.kwargs.get("photo_token")
        nomination_token = request.GET.get("nomination_token")
        if not (photo_token and nomination_token):
            return False

        try:
            invitation = EventInvitation.objects.get(token=nomination_token)
            contact = Contact.objects.get(photo_access_uuid=photo_token)
        except (EventInvitation.DoesNotExist, Contact.DoesNotExist):
            return False

        # Check that invitation's organization or country (for GOV) matches contact
        if invitation.country:
            return (
                contact.organization
                and contact.organization.country == invitation.country
            )
        if invitation.organization:
            return contact.organization == invitation.organization
        return False


class PhotoUploadPermission(rest_framework.permissions.BasePermission):
    """
    Allows photo upload if:
    - the user is staff
    or
    - the request includes a valid nomination token and the contact belongs to the
      invited organization/country (taking GOV into account).
    """

    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_staff:
            return True

        nomination_token = request.data.get("nomination_token")
        contact_id = request.data.get("contact_id")
        if not (nomination_token and contact_id):
            return False

        try:
            invitation = EventInvitation.objects.get(token=nomination_token)
            contact = Contact.objects.get(id=contact_id)
        except (EventInvitation.DoesNotExist, Contact.DoesNotExist):
            return False

        if invitation.country:
            return (
                contact.organization
                and contact.organization.country == invitation.country
            )
        if invitation.organization:
            return contact.organization == invitation.organization
        return False
