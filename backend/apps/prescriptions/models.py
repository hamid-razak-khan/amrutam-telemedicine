import uuid
from django.db import models
from django.core.exceptions import ValidationError

class Prescription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultation = models.OneToOneField('consultations.Consultation', on_delete=models.CASCADE, related_name='prescription')
    doctor = models.ForeignKey('doctors.DoctorProfile', on_delete=models.CASCADE, related_name='prescriptions')
    patient = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='prescriptions_received')
    diagnosis = models.TextField(help_text="Clinical Ayurvedic / Allopathic diagnosis")
    medications = models.JSONField(
        default=list,
        help_text="Structured list of medications: [{name, dosage, duration, instructions}]"
    )
    lifestyle_recommendations = models.TextField(blank=True, default='', help_text="Pathya / Apathya (Dietary and Lifestyle)")
    follow_up_date = models.DateField(null=True, blank=True)
    additional_notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'created_at']),
            models.Index(fields=['doctor', 'created_at']),
        ]

    def clean(self):
        super().clean()
        if not isinstance(self.medications, list):
            raise ValidationError({'medications': 'Medications must be a structured list.'})
        for item in self.medications:
            if not isinstance(item, dict) or 'name' not in item:
                raise ValidationError({'medications': 'Each medication entry must be an object with at least a "name" key.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Prescription for {self.patient.email} by Dr. {self.doctor.user.last_name} ({self.created_at.strftime('%Y-%m-%d')})"
