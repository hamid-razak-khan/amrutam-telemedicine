import uuid
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied

from apps.bookings.models import Booking
from apps.availability.models import AvailabilitySlot
from apps.consultations.models import Consultation
from apps.payments.models import Payment
from apps.audit.utils import log_audit_event
from apps.audit.models import AuditLog


from django.db import IntegrityError
from apps.doctors.models import DoctorProfile


class SlotUnavailableError(Exception):
    pass


class SlotExpiredError(Exception):
    pass


class BookingService:
    """
    Service Layer: Encapsulates appointment booking rules, transactional pessimistic locking,
    consultation record creation, and booking cancellation workflows.
    """

    @staticmethod
    def create_booking(patient_user, slot_id, chief_complaint='', idempotency_key=None, request=None):
        """
        Executes appointment booking inside a database transaction with a pessimistic
        row lock (select_for_update) on the AvailabilitySlot and active consultation checks.
        """
        with transaction.atomic():
            slot = AvailabilitySlot.objects.select_for_update().select_related('doctor', 'doctor__user').filter(id=slot_id).first()

            if not slot:
                raise NotFound("The specified availability slot does not exist.")

            now = timezone.now()

            if slot.start_at < now:
                raise SlotExpiredError("Cannot book a time slot in the past.")

            # Validate doctor approval
            if slot.doctor.verification_status != DoctorProfile.STATUS_VERIFIED:
                raise ValidationError("Doctor is not currently verified to accept bookings.")

            # Check if this slot was previously reserved and has expired
            if slot.status == AvailabilitySlot.STATUS_RESERVED:
                expired_consultation = Consultation.objects.filter(
                    slot=slot,
                    status=Consultation.STATUS_BOOKED,
                    expires_at__lt=now
                ).first()
                if expired_consultation:
                    # Release expired reservation
                    expired_consultation.status = Consultation.STATUS_CANCELLED
                    expired_consultation.cancellation_reason = "Reservation expired: payment was not completed within the time limit."
                    expired_consultation.cancelled_at = now
                    expired_consultation.expires_at = None
                    expired_consultation.save(update_fields=['status', 'cancellation_reason', 'cancelled_at', 'expires_at', 'updated_at'])
                    slot.status = AvailabilitySlot.STATUS_AVAILABLE
                    slot.save(update_fields=['status', 'updated_at'])
                else:
                    raise SlotUnavailableError("Sorry, this time slot has just been booked. Please select another available time.")

            if slot.status != AvailabilitySlot.STATUS_AVAILABLE:
                raise SlotUnavailableError("Sorry, this time slot has just been booked. Please select another available time.")

            # Conflict check: ensure doctor doesn't already have an active appointment at this time
            doctor_conflict = Consultation.objects.filter(
                doctor=slot.doctor,
                scheduled_start=slot.start_at,
                status__in=[Consultation.STATUS_BOOKED, Consultation.STATUS_CONFIRMED, Consultation.STATUS_IN_PROGRESS]
            ).exclude(status=Consultation.STATUS_BOOKED, expires_at__lt=now).exists()

            if doctor_conflict:
                raise SlotUnavailableError("Sorry, this time slot has just been booked. Please select another available time.")

            # Atomically reserve slot
            slot.status = AvailabilitySlot.STATUS_RESERVED
            slot.save(update_fields=['status', 'updated_at'])

            # 10-minute reservation window
            expires_at = now + timezone.timedelta(minutes=10)

            # Unique booking reference
            booking_ref = f"AMR-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

            try:
                # Create Consultation record
                consultation = Consultation.objects.create(
                    booking_reference=booking_ref,
                    patient=patient_user,
                    doctor=slot.doctor,
                    slot=slot,
                    scheduled_start=slot.start_at,
                    scheduled_end=slot.end_at,
                    status=Consultation.STATUS_BOOKED,
                    expires_at=expires_at,
                    chief_complaint=chief_complaint
                )

                # Create Booking association
                booking = Booking.objects.create(
                    consultation=consultation,
                    idempotency_key=idempotency_key
                )

                # Initialize Payment record (simulated gateway)
                payment = Payment.objects.create(
                    consultation=consultation,
                    patient=patient_user,
                    amount=slot.doctor.consultation_fee,
                    currency='INR',
                    status=Payment.STATUS_PENDING,
                    provider='SIMULATED_GATEWAY',
                    provider_reference=f"SIM_PAY_{uuid.uuid4().hex[:10].upper()}"
                )
            except IntegrityError as exc:
                raise SlotUnavailableError("Sorry, this time slot has just been booked. Please select another available time.") from exc

            log_audit_event(
                action='BOOKING_CREATED',
                resource_type='CONSULTATION',
                resource_id=str(consultation.id),
                actor=patient_user,
                request=request,
                outcome=AuditLog.OUTCOME_SUCCESS,
                metadata={
                    'booking_reference': booking_ref,
                    'doctor_id': str(slot.doctor.id),
                    'slot_id': str(slot.id),
                    'idempotency_key': idempotency_key
                }
            )

            return booking, consultation, payment

    @staticmethod
    def cancel_booking(consultation_id, user, cancellation_reason='', request=None):
        """
        Cancels a consultation and releases the availability slot.
        """
        with transaction.atomic():
            consultation = Consultation.objects.select_for_update().select_related('slot', 'patient', 'doctor', 'doctor__user').filter(id=consultation_id).first()

            if not consultation:
                raise NotFound("Consultation not found.")

            # Check permissions
            is_patient = consultation.patient == user
            is_doctor = hasattr(user, 'doctor_profile') and consultation.doctor == user.doctor_profile
            is_admin = user.role == 'ADMIN' or user.is_staff

            if not (is_patient or is_doctor or is_admin):
                raise PermissionDenied("You do not have permission to cancel this consultation.")

            if consultation.status in (Consultation.STATUS_CANCELLED, Consultation.STATUS_COMPLETED):
                raise ValidationError(f"Cannot cancel a consultation that is already {consultation.status}.")

            consultation.transition_to(Consultation.STATUS_CANCELLED, actor=user, reason=cancellation_reason)

            log_audit_event(
                action='BOOKING_CANCELLED',
                resource_type='CONSULTATION',
                resource_id=str(consultation.id),
                actor=user,
                request=request,
                outcome=AuditLog.OUTCOME_SUCCESS,
                metadata={
                    'booking_reference': consultation.booking_reference,
                    'reason': cancellation_reason
                }
            )

            return consultation
