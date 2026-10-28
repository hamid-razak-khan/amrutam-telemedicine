from rest_framework import serializers
from apps.doctors.models import DoctorProfile
from apps.accounts.serializers import UserSerializer
from apps.availability.models import AvailabilitySlot

class DoctorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    doctor_name = serializers.SerializerMethodField()
    joining_date = serializers.SerializerMethodField()
    removed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'user', 'doctor_name', 'license_number', 'credentials', 'specialization',
            'biography', 'years_of_experience', 'consultation_fee',
            'verification_status', 'rejection_reason', 'approved_at', 'active_status',
            'joining_date', 'removed_at', 'removal_reason', 'removed_by_name', 'created_at'
        ]
        read_only_fields = [
            'id', 'user', 'verification_status', 'rejection_reason', 'approved_at',
            'joining_date', 'removed_at', 'removal_reason', 'removed_by_name', 'created_at'
        ]

    def get_doctor_name(self, obj):
        return f"Dr. {obj.user.first_name} {obj.user.last_name}"

    def get_joining_date(self, obj):
        date_val = obj.approved_at or obj.created_at
        return date_val.isoformat() if date_val else None

    def get_removed_by_name(self, obj):
        if obj.removed_by:
            return f"{obj.removed_by.first_name} {obj.removed_by.last_name}".strip() or obj.removed_by.email
        return None

class DoctorProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorProfile
        fields = [
            'license_number', 'credentials', 'specialization', 'biography',
            'years_of_experience', 'consultation_fee', 'active_status'
        ]

class DoctorRegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100, required=True)
    last_name = serializers.CharField(max_length=100, required=True)
    email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=True)
    license_number = serializers.CharField(max_length=100, required=True)
    credentials = serializers.CharField(max_length=255, required=True)
    specialization = serializers.CharField(max_length=150, required=True)
    biography = serializers.CharField(required=False, allow_blank=True, default='')
    years_of_experience = serializers.IntegerField(default=1, min_value=0)
    consultation_fee = serializers.DecimalField(max_digits=10, decimal_places=2, default=500.00)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

class DoctorRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, min_length=3, help_text="Reason for rejection visible to doctor")

class DoctorRemoveSerializer(serializers.Serializer):
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default="No longer working with the organization",
        help_text="Reason why doctor was removed/offboarded"
    )

