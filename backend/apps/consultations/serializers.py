from rest_framework import serializers
from apps.consultations.models import Consultation
from apps.accounts.serializers import UserSerializer
from apps.doctors.serializers import DoctorProfileSerializer
from apps.availability.serializers import AvailabilitySlotSerializer

class ConsultationSerializer(serializers.ModelSerializer):
    patient = UserSerializer(read_only=True)
    doctor = DoctorProfileSerializer(read_only=True)
    slot = AvailabilitySlotSerializer(read_only=True)

    class Meta:
        model = Consultation
        fields = [
            'id', 'booking_reference', 'patient', 'doctor', 'slot',
            'scheduled_start', 'scheduled_end', 'status',
            'chief_complaint', 'clinical_notes', 'cancellation_reason',
            'started_at', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'booking_reference', 'patient', 'doctor', 'slot',
            'scheduled_start', 'scheduled_end', 'started_at', 'completed_at',
            'created_at', 'updated_at'
        ]

class ConsultationStartSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True, default='')

class ConsultationCompleteSerializer(serializers.Serializer):
    clinical_notes = serializers.CharField(required=False, allow_blank=True, default='')
