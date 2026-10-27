import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta

class TimeStampedModel(models.Model):
    """Abstract base model with auto-updating timestamps and UUID."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class IdempotencyKey(models.Model):
    """
    Tracks idempotency keys for write operations to prevent duplicate execution,
    concurrent double-spend/double-booking, and ensure consistent replay.
    """
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_FAILED = 'FAILED'

    STATUS_CHOICES = (
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='idempotency_keys')
    operation = models.CharField(max_length=120)
    request_hash = models.CharField(max_length=64)  # SHA-256 of request payload
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PROCESSING)
    response_code = models.IntegerField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['key', 'user', 'operation'], name='unique_user_idempotency_key')
        ]
        indexes = [
            models.Index(fields=['key', 'user']),
            models.Index(fields=['expires_at']),
        ]

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user.email} - {self.operation} - {self.key} [{self.status}]"
