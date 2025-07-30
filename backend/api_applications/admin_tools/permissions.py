from rest_framework.permissions import BasePermission

def HasGroup(group_name):
    class GroupPermission(BasePermission):
        def has_permission(self, request, view):
            return (request.user and
            request.user.is_authenticated and
            request.user.groups.filter(name =group_name).exists())
    return GroupPermission