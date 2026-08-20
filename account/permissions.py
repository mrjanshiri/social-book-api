from rest_framework import permissions



class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'admin'
        )
    
    

class IsSuperAdminOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.role == 'superadmin':
                return True
            if request.user.role == 'admin':
                return True
            if request.user.role == 'user' and request.method in permissions.SAFE_METHODS:
                return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            if request.user.role == 'superadmin':
                return True
            if request.user.role == 'admin':
                # Admin cannot modify any superadmin object.
                # This implicitly covers preventing admins from promoting themselves or others to superadmin.
                if obj.role == 'superadmin':
                    return False
                return True
            if request.user.role == 'user':
                # User can only access their own object with safe methods
                return request.method in permissions.SAFE_METHODS and obj == request.user
        return False