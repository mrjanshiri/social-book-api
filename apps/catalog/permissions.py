from rest_framework import permissions


class IsBookOwnerOrAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_staff:
            return True

        if request.method == 'POST':
            self.message = "Adding books by regular users will be enabled soon via ISBN lookup."
            return False

        if request.method == 'PATCH':
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        if request.method == 'PATCH':
            return obj.added_by == request.user
        return False