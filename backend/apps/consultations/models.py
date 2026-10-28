import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class Consultation(models.Model):
    STATUS_BOOKED = 'BOOKED'
    STATUS_CONFIRMED = 'CONFIRMED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_NO_SHOW = 'NO_SHOW'

    STATUS_CHOICES = (
        (STATUS_BOOKED, 'Booked'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_NO_SHOW, 'No Show'),
    )

    VALID_TRANSITIONS = {
        STATUS_BOOKED: [STATUS_CONFIRMED, STATUS_IN_PROGRESS, STATUS_CANCELLED, STATUS_NO_SHOW],
        STATUS_CONFIRMED: [STATUS_IN_PROGRESS, STATUS_CANCELLED, STATUS_NO_SHOW],
        STATUS_IN_PROGRESS: [STATUS_COMPLETED, STATUS_CANCELLED],
        STATUS_COMPLETED: [],  # Terminal state
        STATUS_CANCELLED: [],  # Terminal state
        STATUS_NO_SHOW: [],    # Terminal state
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_reference = models.CharField(max_length=64, unique=True, db_index=True)
    patient = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='consultations_as_patient')
    doctor = models.ForeignKey('doctors.DoctorProfile', on_delete=models.CASCADE, related_name='consultations')
    slot = models.ForeignKey('availability.AvailabilitySlot', on_delete=models.PROTECT, related_name='consultations')
    scheduled_start = models.DateTimeField(db_index=True)
    scheduled_end = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_BOOKED, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Reservation expiration timestamp")
    
    chief_complaint = models.TextField(blank=True, default='', help_text="Patient reported issues")
    clinical_notes = models.TextField(blank=True, default='', help_text="Doctor internal clinical assessment")
    
    cancellation_reason = models.TextField(blank=True, null=True)
    cancelled_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_consultations')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_start']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['doctor', 'status']),
            models.Index(fields=['status', 'scheduled_start']),
            models.Index(fields=['status', 'expires_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['slot'],
                condition=models.Q(status__in=['BOOKED', 'CONFIRMED', 'IN_PROGRESS']),
                name='unique_active_consultation_per_slot'
            ),
            models.UniqueConstraint(
                fields=['doctor', 'scheduled_start'],
                condition=models.Q(status__in=['BOOKED', 'CONFIRMED', 'IN_PROGRESS']),
                name='unique_active_doctor_appointment_time'
            ),
        ]

    def can_transition_to(self, new_status):
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])

    def transition_to(self, new_status, actor=None, reason=''):
        if not self.can_transition_to(new_status):
            raise ValidationError(f"Invalid consultation state transition from {self.status} to {new_status}.")
        
        self.status = new_status
        now = timezone.now()
        if new_status == self.STATUS_IN_PROGRESS:
            self.started_at = now
        elif new_status == self.STATUS_COMPLETED:
            self.completed_at = now
            self.expires_at = None
        elif new_status == self.STATUS_CANCELLED:
            self.cancelled_at = now
            self.cancelled_by = actor
            self.cancellation_reason = reason
            self.expires_at = None
            # Release slot if in future
            if self.slot and self.slot.start_at > now:
                self.slot.status = 'AVAILABLE'
                self.slot.save(update_fields=['status', 'updated_at'])
        self.save()

    def __str__(self):
        return f"Consultation {self.booking_reference}: {self.patient.email} with Dr. {self.doctor.user.last_name} [{self.status}]"
