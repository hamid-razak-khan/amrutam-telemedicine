import uuid
from django.db import models
from django.core.exceptions import ValidationError

class AuditLog(models.Model):
    """
    Append-only audit log tracking security, authentication, and clinical-administrative operations.
    Application-level immutability is enforced on save() and delete().
    """
    OUTCOME_SUCCESS = 'SUCCESS'
    OUTCOME_FAILURE = 'FAILURE'
    OUTCOME_DENIED = 'DENIED'

    OUTCOME_CHOICES = (
        (OUTCOME_SUCCESS, 'Success'),
        (OUTCOME_FAILURE, 'Failure'),
        (OUTCOME_DENIED, 'Denied'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_events'
    )
    actor_email = models.CharField(max_length=255, blank=True, null=True)
    actor_role = models.CharField(max_length=50, blank=True, null=True)
    action = models.CharField(max_length=100, db_index=True)
    resource_type = models.CharField(max_length=100, db_index=True)
    resource_id = models.CharField(max_length=120, blank=True, null=True, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    request_id = models.CharField(max_length=120, blank=True, null=True, db_index=True)
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, default=OUTCOME_SUCCESS)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    sanitized_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['actor', 'timestamp']),
        ]

    def save(self, *args, **kwargs):
        # Enforce append-only integrity at application level
        if self._state.adding is False:
            raise ValidationError("AuditLog entries are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("AuditLog entries are immutable and cannot be deleted.")

    def __str__(self):
        return f"{self.timestamp} - {self.action} by {self.actor_email or 'Anonymous'} [{self.outcome}]"
