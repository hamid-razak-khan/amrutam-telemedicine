import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger('amrutam')

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
    retry_jitter=True
)
def cleanup_expired_idempotency_keys(self):
    """
    Periodic maintenance task to clean up expired idempotency keys from the database.
    """
    from apps.common.models import IdempotencyKey
    try:
        now = timezone.now()
        deleted_count, _ = IdempotencyKey.objects.filter(expires_at__lt=now).delete()
        logger.info(f"Successfully cleaned up {deleted_count} expired idempotency keys.")
        return {"status": "SUCCESS", "deleted_count": deleted_count}
    except Exception as exc:
        logger.error(f"Error cleaning up idempotency keys: {exc}")
        raise self.retry(exc=exc)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    retry_backoff=True,
    retry_jitter=True
)
def send_appointment_reminders(self):
    """
    Scans for upcoming appointments in the next 2 hours and simulates dispatching reminders.
    Safe to retry, avoids storing sensitive health notes in queue payload.
    """
    from apps.consultations.models import Consultation
    try:
        now = timezone.now()
        upcoming_window = now + timedelta(hours=2)
        upcoming = Consultation.objects.filter(
            status__in=[Consultation.STATUS_BOOKED, Consultation.STATUS_CONFIRMED],
            scheduled_start__gte=now,
            scheduled_start__lte=upcoming_window
        ).select_related('patient', 'doctor', 'doctor__user')

        dispatched = 0
        for consultation in upcoming:
            # Simulate reminder dispatch via email/SMS without logging sensitive patient diagnosis
            logger.info(
                f"[REMINDER] Upcoming appointment {consultation.booking_reference} for patient "
                f"at {consultation.scheduled_start.strftime('%Y-%m-%d %H:%M UTC')} with Dr. {consultation.doctor.user.last_name}"
            )
            dispatched += 1

        return {"status": "SUCCESS", "reminders_dispatched": dispatched}
    except Exception as exc:
        logger.error(f"Error dispatching appointment reminders: {exc}")
        raise self.retry(exc=exc)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True
)
def release_expired_reservations_task(self):
    """
    Periodic task to release expired pending-payment reservations and return slots to AVAILABLE status.
    """
    from django.db import transaction
    from apps.consultations.models import Consultation
    from apps.availability.models import AvailabilitySlot
    try:
        now = timezone.now()
        expired_consultations = Consultation.objects.filter(
            status=Consultation.STATUS_BOOKED,
            expires_at__lt=now
        ).select_related('slot')

        released_count = 0
        for consultation in expired_consultations:
            with transaction.atomic():
                consultation.status = Consultation.STATUS_CANCELLED
                consultation.cancellation_reason = "Reservation expired: payment was not completed within the 10-minute window."
                consultation.expires_at = None
                consultation.cancelled_at = now
                consultation.save(update_fields=['status', 'cancellation_reason', 'expires_at', 'cancelled_at', 'updated_at'])

                if consultation.slot and consultation.slot.start_at > now:
                    consultation.slot.status = AvailabilitySlot.STATUS_AVAILABLE
                    consultation.slot.save(update_fields=['status', 'updated_at'])

                released_count += 1
                logger.info(f"Released expired reservation for booking {consultation.booking_reference}")

        return {"status": "SUCCESS", "released_count": released_count}
    except Exception as exc:
        logger.error(f"Error releasing expired reservations: {exc}")
        raise self.retry(exc=exc)
