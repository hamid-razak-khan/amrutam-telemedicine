import uuid
from django.db import models

class DoctorProfile(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_VERIFIED = 'APPROVED'  # Backward compatibility alias
    STATUS_REJECTED = 'REJECTED'
    STATUS_REMOVED = 'REMOVED'

    VERIFICATION_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_REMOVED, 'Removed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='doctor_profile')
    license_number = models.CharField(max_length=100, blank=True, default='', db_index=True, help_text="Medical council / license registration number")
    credentials = models.CharField(max_length=255, help_text="e.g. BAMS, MD (Ayurveda)")
    specialization = models.CharField(max_length=150, db_index=True)
    biography = models.TextField(blank=True, default='')
    years_of_experience = models.PositiveIntegerField(default=1)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=500.00, db_index=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default=STATUS_PENDING, db_index=True)
    rejection_reason = models.TextField(blank=True, default='', help_text="Reason for rejection visible to doctor")
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_doctors')
    approved_at = models.DateTimeField(null=True, blank=True)
    removed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='removed_doctors')
    removed_at = models.DateTimeField(null=True, blank=True)
    removal_reason = models.TextField(blank=True, default='', help_text="Reason doctor was removed/offboarded")
    active_status = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-years_of_experience', 'consultation_fee']
        indexes = [
            models.Index(fields=['verification_status', 'active_status']),
            models.Index(fields=['specialization', 'verification_status']),
            models.Index(fields=['license_number']),
        ]

    @property
    def is_approved(self):
        return self.verification_status in (self.STATUS_APPROVED, 'VERIFIED')

    @property
    def is_removed(self):
        return self.verification_status == self.STATUS_REMOVED

    @property
    def joining_date(self):
        return self.approved_at or self.created_at

    def __str__(self):
        return f"Dr. {self.user.full_name} ({self.specialization}) - {self.verification_status}"

