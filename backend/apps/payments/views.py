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

from django.utils import timezone
from apps.availability.models import AvailabilitySlot

class PaymentInitiateView(APIView):
    """
    Process simulated payments for consultations with idempotency, reservation expiration check,
    and audit logs.
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

        # Check idempotency on payment if key provided
        if idempotency_key:
            existing_payment = Payment.objects.filter(idempotency_key=idempotency_key).first()
            if existing_payment:
                return Response({
                    "success": existing_payment.status == Payment.STATUS_COMPLETED,
                    "message": "Payment record returned from idempotent cache.",
                    "payment": PaymentSerializer(existing_payment).data
                }, status=status.HTTP_200_OK if existing_payment.status == Payment.STATUS_COMPLETED else status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            consultation = Consultation.objects.select_for_update().select_related('patient', 'doctor', 'slot').filter(id=consultation_id).first()
            if not consultation:
                return Response(
                    {"success": False, "error": {"code": "NOT_FOUND", "message": "Consultation not found."}},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Verification of appointment ownership
            if consultation.patient != request.user and request.user.role != 'ADMIN':
                return Response(
                    {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "Only the booking patient may submit payment."}},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Prevent duplicate payment processing if already paid
            completed_payment = consultation.payments.filter(status=Payment.STATUS_COMPLETED).first()
            if completed_payment:
                return Response({
                    "success": True,
                    "message": "Payment has already been completed for this consultation.",
                    "payment": PaymentSerializer(completed_payment).data
                }, status=status.HTTP_200_OK)

            # Check if consultation is cancelled
            if consultation.status == Consultation.STATUS_CANCELLED:
                return Response(
                    {"success": False, "error": {"code": "CONSULTATION_CANCELLED", "message": "Cannot pay for a cancelled appointment."}},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if consultation is already completed
            if consultation.status == Consultation.STATUS_COMPLETED:
                return Response(
                    {"success": False, "error": {"code": "CONSULTATION_COMPLETED", "message": "This consultation has already taken place."}},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Reservation expiration check: 10 minutes limit
            now = timezone.now()
            if consultation.status == Consultation.STATUS_BOOKED and consultation.expires_at and consultation.expires_at < now:
                consultation.transition_to(Consultation.STATUS_CANCELLED, actor=request.user, reason="Reservation expired: payment was not completed within the 10-minute window.")
                return Response(
                    {"success": False, "error": {"code": "RESERVATION_EXPIRED", "message": "Reservation has expired. Please select an available slot to book."}},
                    status=status.HTTP_400_BAD_REQUEST
                )

            provider_ref = f"SIM_PAY_{uuid.uuid4().hex[:12].upper()}"

            if simulate_failure:
                payment = consultation.payments.filter(status=Payment.STATUS_PENDING).first()
                if not payment:
                    payment = Payment.objects.create(
                        consultation=consultation,
                        patient=request.user,
                        amount=consultation.doctor.consultation_fee,
                        currency='INR',
                        status=Payment.STATUS_FAILED,
                        provider='SIMULATED_GATEWAY',
                        provider_reference=provider_ref,
                        idempotency_key=idempotency_key,
                        failure_reason='Simulated card payment decline.'
                    )
                else:
                    payment.status = Payment.STATUS_FAILED
                    payment.failure_reason = 'Simulated card payment decline.'
                    payment.save(update_fields=['status', 'failure_reason', 'updated_at'])

                log_audit_event(
                    action='PAYMENT_PROCESSED',
                    resource_type='PAYMENT',
                    resource_id=str(payment.id),
                    actor=request.user,
                    request=request,
                    outcome=AuditLog.OUTCOME_FAILURE,
                    metadata={
                        'amount': str(payment.amount),
                        'provider_reference': provider_ref,
                        'status': payment.status,
                        'consultation_id': str(consultation.id)
                    }
                )

                return Response({
                    "success": False,
                    "error": {"code": "PAYMENT_FAILED", "message": "Payment failed (simulated decline)."},
                    "payment": PaymentSerializer(payment).data
                }, status=status.HTTP_400_BAD_REQUEST)

            # Payment succeeded
            payment = consultation.payments.filter(status=Payment.STATUS_PENDING).first()
            if payment:
                payment.status = Payment.STATUS_COMPLETED
                payment.provider_reference = provider_ref
                payment.failure_reason = ''
                if idempotency_key:
                    payment.idempotency_key = idempotency_key
                payment.save(update_fields=['status', 'provider_reference', 'failure_reason', 'idempotency_key', 'updated_at'])
            else:
                payment = Payment.objects.create(
                    consultation=consultation,
                    patient=request.user,
                    amount=consultation.doctor.consultation_fee,
                    currency='INR',
                    status=Payment.STATUS_COMPLETED,
                    provider='SIMULATED_GATEWAY',
                    provider_reference=provider_ref,
                    idempotency_key=idempotency_key
                )

            # Confirm appointment and clear reservation expiration
            consultation.status = Consultation.STATUS_CONFIRMED
            consultation.expires_at = None
            consultation.save(update_fields=['status', 'expires_at', 'updated_at'])

            # Transition slot to BOOKED
            if consultation.slot:
                consultation.slot.status = AvailabilitySlot.STATUS_BOOKED
                consultation.slot.save(update_fields=['status', 'updated_at'])

            log_audit_event(
                action='PAYMENT_PROCESSED',
                resource_type='PAYMENT',
                resource_id=str(payment.id),
                actor=request.user,
                request=request,
                outcome=AuditLog.OUTCOME_SUCCESS,
                metadata={
                    'amount': str(payment.amount),
                    'provider_reference': provider_ref,
                    'status': payment.status,
                    'consultation_id': str(consultation.id)
                }
            )

            return Response({
                "success": True,
                "message": "Payment completed successfully.",
                "payment": PaymentSerializer(payment).data
            }, status=status.HTTP_200_OK)

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
