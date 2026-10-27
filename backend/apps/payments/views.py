import uuid
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.payments.models import Payment
from apps.payments.serializers import PaymentSerializer, PaymentInitiateSerializer
from apps.consultations.models import Consultation
from apps.audit.utils import log_audit_event
from apps.audit.models import AuditLog

class PaymentInitiateView(APIView):
    """
    Process simulated payments for consultations with idempotency and audit logs.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Process simulated payment for consultation",
        request=PaymentInitiateSerializer,
        parameters=[
            OpenApiParameter('Idempotency-Key', str, location=OpenApiParameter.HEADER, required=False, description="Idempotency key")
        ]
    )
    def post(self, request):
        serializer = PaymentInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        consultation_id = serializer.validated_data['consultation_id']
        simulate_failure = serializer.validated_data.get('simulate_failure', False)
        idempotency_key = request.headers.get('Idempotency-Key')

        consultation = Consultation.objects.filter(id=consultation_id).first()
        if not consultation:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Consultation not found."}},
                status=status.HTTP_404_NOT_FOUND
            )

        if consultation.patient != request.user and request.user.role != 'ADMIN':
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "Only the booking patient may submit payment."}},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check idempotency on payment if key provided
        if idempotency_key:
            existing_payment = Payment.objects.filter(idempotency_key=idempotency_key).first()
            if existing_payment:
                return Response({
                    "success": True,
                    "message": "Payment record returned from idempotent cache.",
                    "payment": PaymentSerializer(existing_payment).data
                }, status=status.HTTP_200_OK)

        with transaction.atomic():
            payment_status = Payment.STATUS_FAILED if simulate_failure else Payment.STATUS_COMPLETED
            provider_ref = f"SIM_PAY_{uuid.uuid4().hex[:12].upper()}"

            payment = Payment.objects.create(
                consultation=consultation,
                patient=request.user,
                amount=consultation.doctor.consultation_fee,
                currency='INR',
                status=payment_status,
                provider='SIMULATED_GATEWAY',
                provider_reference=provider_ref,
                idempotency_key=idempotency_key,
                failure_reason='Simulated card payment decline.' if simulate_failure else ''
            )

            if payment_status == Payment.STATUS_COMPLETED:
                if consultation.status == Consultation.STATUS_BOOKED:
                    consultation.status = Consultation.STATUS_CONFIRMED
                    consultation.save(update_fields=['status', 'updated_at'])

            log_audit_event(
                action='PAYMENT_PROCESSED',
                resource_type='PAYMENT',
                resource_id=str(payment.id),
                actor=request.user,
                request=request,
                outcome=AuditLog.OUTCOME_SUCCESS if payment_status == Payment.STATUS_COMPLETED else AuditLog.OUTCOME_FAILURE,
                metadata={
                    'amount': str(payment.amount),
                    'provider_reference': provider_ref,
                    'status': payment.status,
                    'consultation_id': str(consultation.id)
                }
            )

            return Response({
                "success": payment_status == Payment.STATUS_COMPLETED,
                "message": "Payment completed successfully." if payment_status == Payment.STATUS_COMPLETED else "Payment failed (simulated).",
                "payment": PaymentSerializer(payment).data
            }, status=status.HTTP_201_CREATED if payment_status == Payment.STATUS_COMPLETED else status.HTTP_400_BAD_REQUEST)

class PaymentDetailView(APIView):
    """
    Retrieve payment details by ID with tenant checks.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Retrieve payment details")
    def get(self, request, id):
        payment = Payment.objects.filter(id=id).select_related('patient', 'consultation').first()
        if not payment:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Payment record not found."}},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        if user.role == 'PATIENT' and payment.patient != user:
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "Cannot access another user's payment records."}},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response({"success": True, "payment": PaymentSerializer(payment).data})
