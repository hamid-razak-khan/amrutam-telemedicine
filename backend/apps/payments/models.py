import uuid
from django.db import models

class Payment(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_FAILED = 'FAILED'
    STATUS_REFUNDED = 'REFUNDED'

    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultation = models.ForeignKey('consultations.Consultation', on_delete=models.CASCADE, related_name='payments')
    patient = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    provider = models.CharField(max_length=50, default='SIMULATED_GATEWAY')
    provider_reference = models.CharField(max_length=120, unique=True, db_index=True)
    idempotency_key = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
    failure_reason = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['consultation', 'status']),
            models.Index(fields=['patient', 'status']),
        ]

    def __str__(self):
        return f"Payment {self.provider_reference}: {self.amount} {self.currency} [{self.status}]"
