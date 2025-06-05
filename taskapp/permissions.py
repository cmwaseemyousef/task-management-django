from rest_framework import permissions

class IsSuperAdminOrTaskOwner(permissions.BasePermission):
    """
    Custom permission to allow:
    - SuperAdmin: Full access to all tasks
    - Admin: Access to their assigned users' tasks
    - User: Only access to their own tasks
    """

    def has_permission(self, request, view):
        # Allow authenticated users only
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user

        # SuperAdmin has full access
        if user.role == 'superadmin':
            return True

        # Admin can access tasks of their assigned users
        if user.role == 'admin':
            return obj.assigned_to in user.assigned_users.all()

        # Regular users can only access their own tasks
        return obj.assigned_to == user
