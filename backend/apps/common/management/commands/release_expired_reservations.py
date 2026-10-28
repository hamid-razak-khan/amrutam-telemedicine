import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from apps.consultations.models import Consultation
from apps.availability.models import AvailabilitySlot

logger = logging.getLogger('amrutam')

class Command(BaseCommand):
    help = "Release expired pending-payment reservations and return slots to AVAILABLE status."

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help="Maximum number of expired reservations to process per run."
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        now = timezone.now()

        expired_consultations = Consultation.objects.filter(
            status=Consultation.STATUS_BOOKED,
            expires_at__lt=now
        ).select_related('slot')[:batch_size]

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

        self.stdout.write(
            self.style.SUCCESS(f"Successfully processed and released {released_count} expired reservation(s).")
        )
