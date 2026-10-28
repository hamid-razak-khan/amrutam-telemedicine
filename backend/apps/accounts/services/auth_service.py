import logging
from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import APIException, AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User, PatientProfile
from apps.doctors.models import DoctorProfile
from apps.accounts.services.mfa_service import MFAService
from apps.audit.utils import log_audit_event
from apps.audit.models import AuditLog

logger = logging.getLogger('amrutam.security')


class DoctorApprovalPendingError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = 'DOCTOR_APPROVAL_PENDING'
    default_detail = 'Your registration is awaiting administrator approval. You cannot access the doctor dashboard yet.'


class DoctorApprovalRejectedError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = 'DOCTOR_APPROVAL_REJECTED'
    default_detail = 'Your doctor registration has been rejected.'


class AuthService:
    """
    Service Layer: Handles authentication, patient self-registration,
    credential verification, doctor approval status checks, and two-stage MFA challenges.
    """

    @staticmethod
    @transaction.atomic
    def register_patient(validated_data: dict, request=None) -> User:
        """
        Registers a new patient. Role is strictly assigned server-side as ROLE_PATIENT.
        """
        password = validated_data.pop('password')
        validated_data.pop('password_confirm', None)

        email = validated_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError({"email": "A user with this email address already exists."})

        user = User(
            email=email,
            first_name=validated_data.get('first_name', '').strip(),
            last_name=validated_data.get('last_name', '').strip(),
            phone_number=validated_data.get('phone_number', '').strip() if validated_data.get('phone_number') else None,
            role=User.ROLE_PATIENT,
            account_status=User.STATUS_ACTIVE,
            is_active=True
        )
        user.set_password(password)
        user.save()

        # Create associated PatientProfile
        PatientProfile.objects.create(user=user)

        log_audit_event(
            action='AUTH_REGISTER',
            resource_type='USER',
            resource_id=str(user.id),
            actor=user,
            request=request,
            outcome=AuditLog.OUTCOME_SUCCESS,
            metadata={'email': user.email, 'role': user.role}
        )

        return user

    @staticmethod
    def authenticate_user(email: str, password: str, request=None) -> dict:
        """
        Validates credentials and enforces account policies:
        1. Checks credentials.
        2. Verifies account status (active, not suspended).
        3. If Doctor, checks approval status:
           - PENDING: raises DoctorApprovalPendingError (403)
           - REJECTED: raises DoctorApprovalRejectedError (403)
        4. If MFA is enabled (or required for Admin with MFA configured):
           - Returns mfa_required=True with an ephemeral challenge token.
        5. If MFA is not required:
           - Issues full JWT access & refresh tokens.
        """
        if not email or not password:
            raise ValidationError({"detail": "Email and password are required."})

        clean_email = email.strip().lower()

        try:
            user = User.objects.get(email=clean_email)
        except User.DoesNotExist:
            log_audit_event(
                action='AUTH_LOGIN_FAILED',
                resource_type='USER',
                request=request,
                outcome=AuditLog.OUTCOME_FAILURE,
                metadata={'attempted_email': clean_email, 'reason': 'User not found'}
            )
            raise AuthenticationFailed("No active account found with the given credentials.")

        if not user.check_password(password):
            log_audit_event(
                action='AUTH_LOGIN_FAILED',
                resource_type='USER',
                resource_id=str(user.id),
                request=request,
                outcome=AuditLog.OUTCOME_FAILURE,
                metadata={'attempted_email': clean_email, 'reason': 'Invalid password'}
            )
            raise AuthenticationFailed("No active account found with the given credentials.")

        if not user.is_active or user.account_status != User.STATUS_ACTIVE:
            log_audit_event(
                action='AUTH_LOGIN_BLOCKED',
                resource_type='USER',
                resource_id=str(user.id),
                actor=user,
                request=request,
                outcome=AuditLog.OUTCOME_FAILURE,
                metadata={'reason': 'Account inactive or suspended'}
            )
            raise AuthenticationFailed("Your account is currently suspended or inactive. Please contact support.")

        # Doctor Approval Check
        if user.role == User.ROLE_DOCTOR:
            if hasattr(user, 'doctor_profile'):
                doc_profile = user.doctor_profile
                status_val = doc_profile.verification_status

                if status_val == DoctorProfile.STATUS_PENDING:
                    log_audit_event(
                        action='AUTH_LOGIN_DOCTOR_PENDING',
                        resource_type='DOCTOR',
                        resource_id=str(doc_profile.id),
                        actor=user,
                        request=request,
                        outcome=AuditLog.OUTCOME_FAILURE,
                        metadata={'status': 'PENDING'}
                    )
                    raise DoctorApprovalPendingError()
                elif status_val == DoctorProfile.STATUS_REJECTED:
                    log_audit_event(
                        action='AUTH_LOGIN_DOCTOR_REJECTED',
                        resource_type='DOCTOR',
                        resource_id=str(doc_profile.id),
                        actor=user,
                        request=request,
                        outcome=AuditLog.OUTCOME_FAILURE,
                        metadata={'status': 'REJECTED', 'reason': doc_profile.rejection_reason}
                    )
                    reason_msg = f": {doc_profile.rejection_reason}" if doc_profile.rejection_reason else "."
                    raise DoctorApprovalRejectedError(f"Your doctor registration has been rejected{reason_msg}")
            else:
                raise DoctorApprovalPendingError()

        # Multi-Factor Authentication Check
        has_mfa_enabled = hasattr(user, 'mfa_settings') and user.mfa_settings.is_enabled
        is_admin_mfa_required = (user.role == User.ROLE_ADMIN) and has_mfa_enabled

        if has_mfa_enabled or is_admin_mfa_required:
            challenge_token = MFAService.create_mfa_challenge(user)
            log_audit_event(
                action='AUTH_MFA_CHALLENGE_ISSUED',
                resource_type='USER',
                resource_id=str(user.id),
                actor=user,
                request=request,
                outcome=AuditLog.OUTCOME_SUCCESS,
                metadata={'role': user.role}
            )
            return {
                "success": True,
                "mfa_required": True,
                "mfa_token": challenge_token,
                "message": "Two-factor authentication required. Please enter your 6-digit authenticator code or backup recovery code."
            }

        # Issue full JWT tokens when MFA is not required
        from apps.accounts.serializers import UserSerializer

        refresh = RefreshToken.for_user(user)
        refresh['email'] = user.email
        refresh['role'] = user.role
        refresh['full_name'] = user.full_name

        user_data = UserSerializer(user).data
        if user.role == User.ROLE_DOCTOR and hasattr(user, 'doctor_profile'):
            from apps.doctors.serializers import DoctorProfileSerializer
            user_data['doctor_profile'] = DoctorProfileSerializer(user.doctor_profile).data

        log_audit_event(
            action='AUTH_LOGIN',
            resource_type='USER',
            resource_id=str(user.id),
            actor=user,
            request=request,
            outcome=AuditLog.OUTCOME_SUCCESS,
            metadata={'email': user.email, 'role': user.role}
        )

        return {
            "success": True,
            "mfa_required": False,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": user_data
        }

    @staticmethod
    @transaction.atomic
    def create_initial_admin(email: str, password: str, first_name: str = 'Admin', last_name: str = 'Platform', phone_number: str = None) -> tuple[User, bool]:
        """
        Secure provisioning helper for creating the initial administrator.
        Prevents unsafe duplicate creation.
        """
        clean_email = email.strip().lower()
        user, created = User.objects.get_or_create(
            email=clean_email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'phone_number': phone_number,
                'role': User.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'account_status': User.STATUS_ACTIVE,
                'is_active': True
            }
        )
        if created:
            user.set_password(password)
            user.save()
        return user, created
