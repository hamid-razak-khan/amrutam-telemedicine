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
    """Allows access only to authenticated and administrator-approved doctors."""
    message = "Access restricted to verified and approved medical doctors only."

    def has_permission(self, request, view):
        is_doctor_user = bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'DOCTOR' and
            request.user.is_active
        )
        if not is_doctor_user:
            return False

        if hasattr(request.user, 'doctor_profile'):
            return request.user.doctor_profile.verification_status in ('APPROVED', 'VERIFIED')
        return False

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
    """Allows access to either approved doctors or administrators."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False
        if request.user.role == 'ADMIN' or request.user.is_staff or request.user.is_superuser:
            return True
        if request.user.role == 'DOCTOR':
            return hasattr(request.user, 'doctor_profile') and request.user.doctor_profile.verification_status in ('APPROVED', 'VERIFIED')
        return False


class IsSelfOrAdmin(permissions.BasePermission):
    """Object-level permission allowing users to modify only their own record or admin."""
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'ADMIN' or request.user.is_staff:
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user
