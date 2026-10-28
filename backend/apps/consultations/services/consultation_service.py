from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.consultations.models import Consultation
from apps.audit.utils import log_audit_event
from apps.audit.models import AuditLog


class ConsultationService:
    """
    Service Layer: Manages consultation lifecycle state transitions and doctor authorization rules.
    """

    @staticmethod
    def start_consultation(consultation_id, doctor_user, request=None) -> Consultation:
        """
        Assigned doctor initiates the consultation session, transitioning to IN_PROGRESS.
        """
        consultation = Consultation.objects.select_related('doctor', 'doctor__user', 'patient', 'slot').filter(id=consultation_id).first()

        if not consultation:
            raise NotFound("Consultation not found.")

        if consultation.doctor.user != doctor_user:
            raise PermissionDenied("Cannot start consultations assigned to another doctor.")

        if consultation.status not in (Consultation.STATUS_SCHEDULED, Consultation.STATUS_BOOKED):
            raise ValidationError(f"Cannot start consultation from current status '{consultation.status}'.")

        consultation.status = Consultation.STATUS_IN_PROGRESS
        consultation.started_at = timezone.now()
        consultation.save(update_fields=['status', 'started_at', 'updated_at'])

        log_audit_event(
            action='CONSULTATION_STARTED',
            resource_type='CONSULTATION',
            resource_id=str(consultation.id),
            actor=doctor_user,
            request=request,
            outcome=AuditLog.OUTCOME_SUCCESS,
            metadata={'booking_reference': consultation.booking_reference}
        )

        return consultation

    @staticmethod
    def complete_consultation(consultation_id, doctor_user, clinical_notes: str, request=None) -> Consultation:
        """
        Assigned doctor concludes the consultation session, transitioning to COMPLETED.
        """
        consultation = Consultation.objects.select_related('doctor', 'doctor__user', 'patient', 'slot').filter(id=consultation_id).first()

        if not consultation:
            raise NotFound("Consultation not found.")

        if consultation.doctor.user != doctor_user:
            raise PermissionDenied("Cannot complete consultations assigned to another doctor.")

        if consultation.status != Consultation.STATUS_IN_PROGRESS:
            raise ValidationError("Can only complete consultations that are currently IN_PROGRESS.")

        consultation.status = Consultation.STATUS_COMPLETED
        consultation.completed_at = timezone.now()
        consultation.clinical_notes = clinical_notes
        consultation.save(update_fields=['status', 'completed_at', 'clinical_notes', 'updated_at'])

        log_audit_event(
            action='CONSULTATION_COMPLETED',
            resource_type='CONSULTATION',
            resource_id=str(consultation.id),
            actor=doctor_user,
            request=request,
            outcome=AuditLog.OUTCOME_SUCCESS,
            metadata={'booking_reference': consultation.booking_reference}
        )

        return consultation
