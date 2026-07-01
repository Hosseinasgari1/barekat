from rest_framework import permissions


class IsVendor(permissions.BasePermission):
    """Any authenticated user who has a store profile is considered a vendor.
    Role field is no longer enforced — any user can create a shop."""
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'store')
        )


class IsApprovedVendor(permissions.BasePermission):
    """Allows access only to users whose store status is APPROVED."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return hasattr(request.user, 'store') and request.user.store.status == 'APPROVED'


class CanListProduct(permissions.BasePermission):
    """Allows authenticated users to list products.
    If the user has a store profile, it must be APPROVED.
    If they do not have a store profile, they can list immediately (as an individual seller)."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if hasattr(request.user, 'store'):
            return request.user.store.status == 'APPROVED'
        return True

