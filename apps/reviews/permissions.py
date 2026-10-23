from rest_framework import permissions


class IsReviewOwnerOrAdminDelete(permissions.BasePermission):
    """
    - Read: everyone, including guests.
    - Create: any authenticated user.
    - Update: only the review's owner.
    - Delete: the owner, or staff (moderation only; staff cannot edit
      someone else's words).
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if obj.user_id == request.user.id:
            return True
        return request.method == 'DELETE' and request.user.is_staff