from rest_framework import serializers
from django.utils import timezone
from apps.availability.models import AvailabilitySlot

class AvailabilitySlotSerializer(serializers.ModelSerializer):
    doctor_id = serializers.UUIDField(source='doctor.id', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.full_name', read_only=True)

    class Meta:
        model = AvailabilitySlot
        fields = ['id', 'doctor_id', 'doctor_name', 'start_at', 'end_at', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']

class AvailabilitySlotCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilitySlot
        fields = ['start_at', 'end_at']

    def validate(self, attrs):
        start = attrs.get('start_at')
        end = attrs.get('end_at')
        if start and end and end <= start:
            raise serializers.ValidationError({"end_at": "End time must be strictly after start time."})
        if start and start < timezone.now():
            raise serializers.ValidationError({"start_at": "Cannot schedule an availability slot in the past."})
        return attrs
