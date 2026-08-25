from rest_framework import permissions


class IsAdminOrSelfReadOnly(permissions.BasePermission):
    """
    - Superuser: full access to everyone.
    - Staff/Admin (non-superuser): full access to non-staff objects and to
      themselves; no access to other staff/superuser accounts.
    - Regular (non-staff) user: read-only access to their own object.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        return request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if request.user.is_staff:
            if getattr(obj, 'is_superuser', False):
                return False
            if getattr(obj, 'is_staff', False) and obj != request.user:
                return False
            return True
        return request.method in permissions.SAFE_METHODS and obj == request.user