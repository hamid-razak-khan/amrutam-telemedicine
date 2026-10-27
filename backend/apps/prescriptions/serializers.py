from rest_framework import serializers
from apps.prescriptions.models import Prescription
from apps.accounts.serializers import UserSerializer
from apps.doctors.serializers import DoctorProfileSerializer

class MedicationItemSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=True)
    dosage = serializers.CharField(max_length=100, required=True)
    duration = serializers.CharField(max_length=100, required=True)
    instructions = serializers.CharField(max_length=500, required=False, allow_blank=True, default='')

class PrescriptionSerializer(serializers.ModelSerializer):
    patient = UserSerializer(read_only=True)
    doctor = DoctorProfileSerializer(read_only=True)
    consultation_reference = serializers.CharField(source='consultation.booking_reference', read_only=True)

    class Meta:
        model = Prescription
        fields = [
            'id', 'consultation_id', 'consultation_reference', 'patient', 'doctor',
            'diagnosis', 'medications', 'lifestyle_recommendations',
            'follow_up_date', 'additional_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'patient', 'doctor', 'created_at', 'updated_at']

class PrescriptionCreateSerializer(serializers.ModelSerializer):
    medications = MedicationItemSerializer(many=True, required=True)

    class Meta:
        model = Prescription
        fields = [
            'diagnosis', 'medications', 'lifestyle_recommendations',
            'follow_up_date', 'additional_notes'
        ]
