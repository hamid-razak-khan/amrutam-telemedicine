from rest_framework import serializers
from apps.bookings.models import Booking
from apps.consultations.serializers import ConsultationSerializer

class BookingCreateSerializer(serializers.Serializer):
    slot_id = serializers.UUIDField(required=True)
    chief_complaint = serializers.CharField(required=False, allow_blank=True, default='')

class BookingCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default='Cancelled by user')

class BookingDetailSerializer(serializers.ModelSerializer):
    consultation = ConsultationSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'consultation', 'idempotency_key', 'created_at', 'updated_at']
