from rest_framework import permissions

class IsPatient(permissions.BasePermission):
    """Allows access only to authenticated patients."""
    message = "Access restricted to registered patients only."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'PATIENT' and
            request.user.is_active
        )

class IsDoctor(permissions.BasePermission):
    """Allows access only to authenticated doctors."""
    message = "Access restricted to verified medical doctors only."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'DOCTOR' and
            request.user.is_active
        )

class IsAdminUserRole(permissions.BasePermission):
    """Allows access only to platform administrators."""
    message = "Access restricted to platform administrators only."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == 'ADMIN' or request.user.is_staff or request.user.is_superuser) and
            request.user.is_active
        )

class IsDoctorOrAdmin(permissions.BasePermission):
    """Allows access to either doctors or administrators."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role in ('DOCTOR', 'ADMIN') or request.user.is_staff) and
            request.user.is_active
        )

class IsSelfOrAdmin(permissions.BasePermission):
    """Object-level permission allowing users to modify only their own record or admin."""
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'ADMIN' or request.user.is_staff:
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user
