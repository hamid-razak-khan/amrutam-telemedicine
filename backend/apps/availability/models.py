import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class AvailabilitySlot(models.Model):
    STATUS_AVAILABLE = 'AVAILABLE'
    STATUS_RESERVED = 'RESERVED'
    STATUS_BOOKED = 'BOOKED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = (
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_RESERVED, 'Reserved'),
        (STATUS_BOOKED, 'Booked'),
        (STATUS_CANCELLED, 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey('doctors.DoctorProfile', on_delete=models.CASCADE, related_name='slots')
    start_at = models.DateTimeField(db_index=True)
    end_at = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_at__gt=models.F('start_at')),
                name='check_slot_end_after_start'
            ),
        ]
        indexes = [
            models.Index(fields=['doctor', 'status', 'start_at']),
            models.Index(fields=['start_at', 'end_at']),
        ]

    def clean(self):
        super().clean()
        if self.start_at and self.end_at:
            if self.end_at <= self.start_at:
                raise ValidationError({"end_at": "Slot end time must be strictly after start time."})

            # Check for overlapping slots for the same doctor unless cancelled
            if self.status != self.STATUS_CANCELLED:
                overlapping = AvailabilitySlot.objects.filter(
                    doctor=self.doctor,
                    status__in=[self.STATUS_AVAILABLE, self.STATUS_RESERVED, self.STATUS_BOOKED],
                    start_at__lt=self.end_at,
                    end_at__gt=self.start_at
                )
                if self.pk:
                    overlapping = overlapping.exclude(pk=self.pk)
                if overlapping.exists():
                    raise ValidationError("This time slot overlaps with an existing active slot for this doctor.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Dr. {self.doctor.user.last_name}: {self.start_at.strftime('%Y-%m-%d %H:%M')} - {self.end_at.strftime('%H:%M')} [{self.status}]"
