import uuid
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.bookings.models import Booking
from apps.bookings.serializers import (
    BookingCreateSerializer,
    BookingCancelSerializer,
    BookingDetailSerializer
)
from apps.availability.models import AvailabilitySlot
from apps.consultations.models import Consultation
from apps.consultations.serializers import ConsultationSerializer
from apps.payments.models import Payment
from apps.common.permissions import IsPatient
from apps.common.idempotency import (
    check_idempotency,
    complete_idempotency,
    fail_idempotency,
    IdempotencyConflictError
)
from apps.audit.utils import log_audit_event
from apps.audit.models import AuditLog
from django.db import IntegrityError
from rest_framework.exceptions import NotFound, ValidationError
from apps.bookings.services.booking_service import (
    BookingService,
    SlotUnavailableError,
    SlotExpiredError
)

class BookingListCreateView(APIView):
    """
    List appointments or book a new appointment with transaction safety and idempotency protection.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="List appointments for authenticated user")
    def get(self, request):
        user = request.user
        if user.role == 'PATIENT':
            consultations = Consultation.objects.filter(patient=user).select_related('patient', 'doctor', 'doctor__user', 'slot')
        elif user.role == 'DOCTOR':
            consultations = Consultation.objects.filter(doctor__user=user).select_related('patient', 'doctor', 'doctor__user', 'slot')
        elif user.role == 'ADMIN' or user.is_staff:
            consultations = Consultation.objects.all().select_related('patient', 'doctor', 'doctor__user', 'slot')
        else:
            consultations = Consultation.objects.none()

        status_filter = request.query_params.get('status')
        if status_filter:
            consultations = consultations.filter(status=status_filter.upper())

        serializer = ConsultationSerializer(consultations, many=True)
        return Response({"success": True, "bookings": serializer.data})

    @extend_schema(
        summary="Book an appointment (Transaction-safe & Idempotent)",
        request=BookingCreateSerializer,
        parameters=[
            OpenApiParameter('Idempotency-Key', str, location=OpenApiParameter.HEADER, required=True, description="Unique client-generated idempotency UUID/token")
        ]
    )
    def post(self, request):
        if request.user.role != 'PATIENT':
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "Only registered patients can book appointments."}},
                status=status.HTTP_403_FORBIDDEN
            )

        idempotency_key = request.headers.get('Idempotency-Key')
        if not idempotency_key:
            return Response(
                {"success": False, "error": {"code": "MISSING_IDEMPOTENCY_KEY", "message": "The Idempotency-Key header is strictly required for booking operations."}},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slot_id = serializer.validated_data['slot_id']
        chief_complaint = serializer.validated_data.get('chief_complaint', '')

        # Check idempotency store
        try:
            cached_resp, key_record = check_idempotency(request, 'CREATE_BOOKING', request.data)
            if cached_resp:
                return Response(cached_resp['data'], status=cached_resp['status_code'])
        except IdempotencyConflictError as e:
            return Response(
                {"success": False, "error": {"code": "IDEMPOTENCY_CONFLICT", "message": str(e)}},
                status=e.code
            )
        try:
            booking, consultation, payment = BookingService.create_booking(
                patient_user=request.user,
                slot_id=slot_id,
                chief_complaint=chief_complaint,
                idempotency_key=idempotency_key,
                request=request
            )

            response_data = {
                "success": True,
                "message": "Appointment booked successfully.",
                "booking": ConsultationSerializer(consultation).data
            }

            # Mark idempotency record as completed
            complete_idempotency(key_record, status.HTTP_201_CREATED, response_data)

            return Response(response_data, status=status.HTTP_201_CREATED)

        except SlotUnavailableError as e:
            fail_idempotency(key_record)
            return Response(
                {"success": False, "error": {"code": "SLOT_UNAVAILABLE", "message": "Sorry, this time slot has just been booked. Please select another available time."}},
                status=status.HTTP_409_CONFLICT
            )
        except SlotExpiredError as e:
            fail_idempotency(key_record)
            return Response(
                {"success": False, "error": {"code": "SLOT_EXPIRED", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST
            )
        except NotFound as e:
            fail_idempotency(key_record)
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": str(e)}},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            fail_idempotency(key_record)
            return Response(
                {"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST
            )
        except IntegrityError:
            fail_idempotency(key_record)
            return Response(
                {"success": False, "error": {"code": "SLOT_UNAVAILABLE", "message": "Sorry, this time slot has just been booked. Please select another available time."}},
                status=status.HTTP_409_CONFLICT
            )
        except Exception as e:
            fail_idempotency(key_record)
            log_audit_event(
                action='BOOKING_FAILED',
                resource_type='AVAILABILITY_SLOT',
                resource_id=str(slot_id),
                actor=request.user,
                request=request,
                outcome=AuditLog.OUTCOME_FAILURE,
                metadata={'error': str(e)}
            )
            raise e

class BookingDetailView(APIView):
    """
    Retrieve details of a specific booking with strict resource authorization.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Retrieve booking details")
    def get(self, request, id):
        # Look up consultation by ID or booking reference
        consultation = Consultation.objects.filter(
            Q(id=id) | Q(booking_reference=id)
        ).select_related('patient', 'doctor', 'doctor__user', 'slot').first()

        if not consultation:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Booking not found."}},
                status=status.HTTP_404_NOT_FOUND
            )

        # Resource-level access control
        user = request.user
        if user.role == 'PATIENT' and consultation.patient != user:
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "You cannot access another patient's booking."}},
                status=status.HTTP_403_FORBIDDEN
            )
        if user.role == 'DOCTOR' and consultation.doctor.user != user:
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "You cannot access bookings assigned to another doctor."}},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response({"success": True, "booking": ConsultationSerializer(consultation).data})

class BookingCancelView(APIView):
    """
    Cancel an appointment and safely release the occupied slot.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Cancel an appointment", request=BookingCancelSerializer)
    def post(self, request, id):
        consultation = Consultation.objects.filter(
            Q(id=id) | Q(booking_reference=id)
        ).select_related('patient', 'doctor', 'doctor__user', 'slot').first()

        if not consultation:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Booking not found."}},
                status=status.HTTP_404_NOT_FOUND
            )

        # Authorization: Only booking patient, assigned doctor, or admin can cancel
        user = request.user
        is_patient = user == consultation.patient
        is_assigned_doctor = user == consultation.doctor.user
        is_admin = user.role == 'ADMIN' or user.is_staff

        if not (is_patient or is_assigned_doctor or is_admin):
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "Not authorized to cancel this booking."}},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BookingCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason', 'Cancelled by user')

        try:
            with transaction.atomic():
                consultation.transition_to(Consultation.STATUS_CANCELLED, actor=user, reason=reason)

                log_audit_event(
                    action='BOOKING_CANCELLED',
                    resource_type='CONSULTATION',
                    resource_id=str(consultation.id),
                    actor=user,
                    request=request,
                    outcome=AuditLog.OUTCOME_SUCCESS,
                    metadata={'reason': reason, 'booking_reference': consultation.booking_reference}
                )

                return Response({
                    "success": True,
                    "message": "Appointment cancelled successfully.",
                    "booking": ConsultationSerializer(consultation).data
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"success": False, "error": {"code": "INVALID_STATE_TRANSITION", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST
            )
