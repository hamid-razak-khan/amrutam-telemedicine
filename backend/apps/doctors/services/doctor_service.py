from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError, NotFound

from apps.accounts.models import User
from apps.doctors.models import DoctorProfile
from apps.audit.utils import log_audit_event
from apps.audit.models import AuditLog


class DoctorService:
    """
    Service Layer: Handles doctor registration, pending approval state management,
    and administrator review (approval/rejection) workflows.
    """

    @staticmethod
    @transaction.atomic
    def register_doctor(validated_data: dict, request=None) -> dict:
        """
        Submits a new doctor registration request.
        The account is assigned the DOCTOR role and set to PENDING approval by default.
        Doctors can never approve themselves or select an APPROVED status.
        """
        password = validated_data.pop('password')
        validated_data.pop('password_confirm', None)

        email = validated_data.pop('email').strip().lower()
        first_name = validated_data.pop('first_name', '').strip()
        last_name = validated_data.pop('last_name', '').strip()
        phone_number = validated_data.pop('phone_number', None)

        if User.objects.filter(email=email).exists():
            raise ValidationError({"email": "A user with this email address already exists."})

        # Server-enforced DOCTOR role and active user status
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            role=User.ROLE_DOCTOR,
            account_status=User.STATUS_ACTIVE,
            is_active=True
        )
        user.set_password(password)
        user.save()

        # Doctor profile initialized strictly with PENDING verification status
        doctor_profile = DoctorProfile.objects.create(
            user=user,
            verification_status=DoctorProfile.STATUS_PENDING,
            license_number=validated_data.get('license_number', '').strip(),
            credentials=validated_data.get('credentials', '').strip(),
            specialization=validated_data.get('specialization', '').strip(),
            biography=validated_data.get('biography', '').strip(),
            years_of_experience=validated_data.get('years_of_experience', 1),
            consultation_fee=validated_data.get('consultation_fee', 500.00),
            active_status=True
        )

        log_audit_event(
            action='DOCTOR_REGISTRATION_SUBMITTED',
            resource_type='DOCTOR',
            resource_id=str(doctor_profile.id),
            actor=user,
            request=request,
            outcome=AuditLog.OUTCOME_SUCCESS,
            metadata={
                'email': user.email,
                'specialization': doctor_profile.specialization,
                'license_number': doctor_profile.license_number,
                'status': DoctorProfile.STATUS_PENDING
            }
        )

        from apps.doctors.serializers import DoctorProfileSerializer

        return {
            "success": True,
            "message": "Doctor registration submitted successfully. Your account is awaiting administrator approval.",
            "status": DoctorProfile.STATUS_PENDING,
            "doctor_id": str(doctor_profile.id),
            "email": user.email,
            "doctor": DoctorProfileSerializer(doctor_profile).data
        }

    @staticmethod
    @transaction.atomic
    def approve_doctor(doctor_profile_id, admin_user: User, request=None) -> DoctorProfile:
        """
        Authorizes an administrator to approve a doctor's pending registration
        or restore a previously removed/rejected doctor.
        Transitions verification_status to APPROVED and active_status to True.
        """
        try:
            profile = DoctorProfile.objects.select_related('user').get(id=doctor_profile_id)
        except DoctorProfile.DoesNotExist:
            raise NotFound("Doctor profile not found.")

        previous_status = profile.verification_status
        now = timezone.now()

        profile.verification_status = DoctorProfile.STATUS_APPROVED
        profile.active_status = True
        profile.approved_by = admin_user
        if not profile.approved_at:
            profile.approved_at = now
        profile.rejection_reason = ''
        profile.removed_at = None
        profile.removed_by = None
        profile.removal_reason = ''
        profile.save(update_fields=[
            'verification_status', 'active_status', 'approved_by', 'approved_at',
            'rejection_reason', 'removed_at', 'removed_by', 'removal_reason', 'updated_at'
        ])

        if not profile.user.is_active:
            profile.user.is_active = True
            profile.user.save(update_fields=['is_active'])

        log_audit_event(
            action='DOCTOR_APPROVED',
            resource_type='DOCTOR',
            resource_id=str(profile.id),
            actor=admin_user,
            request=request,
            outcome=AuditLog.OUTCOME_SUCCESS,
            metadata={
                'doctor_email': profile.user.email,
                'previous_status': previous_status,
                'new_status': DoctorProfile.STATUS_APPROVED,
                'approved_by': str(admin_user.id)
            }
        )

        return profile

    @staticmethod
    @transaction.atomic
    def remove_doctor(doctor_profile_id, admin_user: User, reason: str = '', request=None) -> DoctorProfile:
        """
        Authorizes an administrator to remove an approved doctor who is no longer working
        with the organization.
        Transitions verification_status to REMOVED, active_status to False, records removed_at,
        removed_by, removal_reason, and cancels future unbooked availability slots.
        """
        try:
            profile = DoctorProfile.objects.select_related('user').get(id=doctor_profile_id)
        except DoctorProfile.DoesNotExist:
            raise NotFound("Doctor profile not found.")

        previous_status = profile.verification_status
        now = timezone.now()

        # Preserve joining date
        if not profile.approved_at:
            profile.approved_at = profile.created_at

        profile.verification_status = DoctorProfile.STATUS_REMOVED
        profile.active_status = False
        profile.removed_by = admin_user
        profile.removed_at = now
        profile.removal_reason = (reason or 'No longer working with the organization').strip()
        profile.save(update_fields=[
            'verification_status', 'active_status', 'removed_by', 'removed_at',
            'removal_reason', 'approved_at', 'updated_at'
        ])

        profile.user.is_active = False
        profile.user.save(update_fields=['is_active'])

        # Cancel any future unbooked availability slots for this doctor
        from apps.availability.models import AvailabilitySlot
        AvailabilitySlot.objects.filter(
            doctor=profile,
            status=AvailabilitySlot.STATUS_AVAILABLE,
            start_at__gt=now
        ).update(status=AvailabilitySlot.STATUS_CANCELLED)

        log_audit_event(
            action='DOCTOR_REMOVED',
            resource_type='DOCTOR',
            resource_id=str(profile.id),
            actor=admin_user,
            request=request,
            outcome=AuditLog.OUTCOME_SUCCESS,
            metadata={
                'doctor_email': profile.user.email,
                'previous_status': previous_status,
                'new_status': DoctorProfile.STATUS_REMOVED,
                'removed_by': str(admin_user.id),
                'joining_date': str(profile.joining_date),
                'removed_at': str(now),
                'reason': profile.removal_reason
            }
        )

        return profile

    @staticmethod
    @transaction.atomic
    def reject_doctor(doctor_profile_id, admin_user: User, reason: str, request=None) -> DoctorProfile:
        """
        Authorizes an administrator to reject a doctor's registration with a clear reason.
        Transitions verification_status to REJECTED.
        """
        if not reason or not reason.strip():
            raise ValidationError({"reason": "A rejection reason is required."})

        try:
            profile = DoctorProfile.objects.select_related('user').get(id=doctor_profile_id)
        except DoctorProfile.DoesNotExist:
            raise NotFound("Doctor profile not found.")

        previous_status = profile.verification_status
        now = timezone.now()

        profile.verification_status = DoctorProfile.STATUS_REJECTED
        profile.approved_by = admin_user
        profile.approved_at = now
        profile.rejection_reason = reason.strip()
        profile.save(update_fields=['verification_status', 'approved_by', 'approved_at', 'rejection_reason', 'updated_at'])

        log_audit_event(
            action='DOCTOR_REJECTED',
            resource_type='DOCTOR',
            resource_id=str(profile.id),
            actor=admin_user,
            request=request,
            outcome=AuditLog.OUTCOME_SUCCESS,
            metadata={
                'doctor_email': profile.user.email,
                'previous_status': previous_status,
                'new_status': DoctorProfile.STATUS_REJECTED,
                'rejected_by': str(admin_user.id),
                'reason': profile.rejection_reason
            }
        )

        return profile

    @staticmethod
    def get_pending_doctors():
        """
        Returns all doctor registrations currently awaiting administrator review.
        """
        return DoctorProfile.objects.filter(
            verification_status=DoctorProfile.STATUS_PENDING
        ).select_related('user').order_by('-created_at')

    @staticmethod
    def get_all_doctor_applications():
        """
        Returns all doctor registrations across all approval statuses for admin inspection.
        """
        return DoctorProfile.objects.all().select_related('user', 'approved_by').order_by('-created_at')
