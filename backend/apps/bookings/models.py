import uuid
from django.db import models

class Booking(models.Model):
    """
    Booking record linking patient, doctor, consultation, and idempotency key.
    """
    STATUS_CONFIRMED = 'CONFIRMED'
    STATUS_CANCELLED = 'CANCELLED'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultation = models.OneToOneField('consultations.Consultation', on_delete=models.CASCADE, related_name='booking')
    idempotency_key = models.CharField(max_length=255, db_index=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.consultation.booking_reference}"
