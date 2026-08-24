from rest_framework import permissions


class IsSuperAdminOrAdmin(permissions.BasePermission):
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
            return True
        return request.method in permissions.SAFE_METHODS and obj == request.user