from rest_framework import serializers
from apps.payments.models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    consultation_id = serializers.UUIDField(read_only=True)
    consultation_reference = serializers.CharField(source='consultation.booking_reference', read_only=True)
    patient_email = serializers.EmailField(source='patient.email', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'consultation_id', 'consultation_reference', 'patient_email',
            'amount', 'currency', 'status', 'provider', 'provider_reference',
            'idempotency_key', 'failure_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'patient_email', 'provider', 'provider_reference', 'created_at', 'updated_at']

class PaymentInitiateSerializer(serializers.Serializer):
    consultation_id = serializers.UUIDField(required=True)
    simulate_failure = serializers.BooleanField(required=False, default=False)
