from rest_framework import serializers
from apps.doctors.models import DoctorProfile
from apps.accounts.serializers import UserSerializer
from apps.availability.models import AvailabilitySlot

class DoctorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'user', 'doctor_name', 'credentials', 'specialization',
            'biography', 'years_of_experience', 'consultation_fee',
            'verification_status', 'active_status', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'verification_status', 'created_at']

    def get_doctor_name(self, obj):
        return f"Dr. {obj.user.first_name} {obj.user.last_name}"

class DoctorProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorProfile
        fields = [
            'credentials', 'specialization', 'biography',
            'years_of_experience', 'consultation_fee', 'active_status'
        ]
