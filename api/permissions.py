import rest_framework
import rest_framework.permissions

from core.models import Contact
from events.models import EventInvitation


class DjangoModelPermissions(rest_framework.permissions.DjangoModelPermissions):
    """Also enforces the view permission, unlike the rest_framework default."""

    perms_map = {
        **rest_framework.permissions.DjangoModelPermissions.perms_map,
        "GET": ["%(app_label)s.view_%(model_name)s"],
    }


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
