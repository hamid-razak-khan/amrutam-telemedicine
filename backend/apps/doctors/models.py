import uuid
from django.db import models

class DoctorProfile(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_VERIFIED = 'VERIFIED'
    STATUS_REJECTED = 'REJECTED'

    VERIFICATION_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_REJECTED, 'Rejected'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='doctor_profile')
    credentials = models.CharField(max_length=255, help_text="e.g. BAMS, MD (Ayurveda)")
    specialization = models.CharField(max_length=150, db_index=True)
    biography = models.TextField(blank=True, default='')
    years_of_experience = models.PositiveIntegerField(default=1)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=500.00, db_index=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default=STATUS_PENDING, db_index=True)
    active_status = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-years_of_experience', 'consultation_fee']
        indexes = [
            models.Index(fields=['verification_status', 'active_status']),
            models.Index(fields=['specialization', 'verification_status']),
        ]

    def __str__(self):
        return f"Dr. {self.user.full_name} ({self.specialization}) - {self.verification_status}"
