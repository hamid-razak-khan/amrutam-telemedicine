from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.doctors.models import DoctorProfile
from apps.doctors.serializers import (
    DoctorProfileSerializer,
    DoctorProfileUpdateSerializer,
    DoctorRegisterSerializer,
    DoctorRejectSerializer,
    DoctorRemoveSerializer,
)
from apps.doctors.services.doctor_service import DoctorService
from apps.availability.models import AvailabilitySlot
from apps.availability.serializers import AvailabilitySlotSerializer, AvailabilitySlotCreateSerializer
from apps.common.permissions import IsDoctor, IsAdminUserRole
from apps.audit.utils import log_audit_event
from apps.audit.models import AuditLog
from apps.consultations.models import Consultation
from django.db import transaction


class DoctorListView(generics.ListAPIView):
    """
    Public directory of verified and active doctors.
    Supports filtering by name, specialization, fee range, and date.
    """
    serializer_class = DoctorProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # Admins can view all; others see only active and verified doctors
        user = self.request.user
        if user and user.is_authenticated and (user.role == 'ADMIN' or user.is_staff):
            qs = DoctorProfile.objects.all().select_related('user')
        else:
            qs = DoctorProfile.objects.filter(
                active_status=True,
                verification_status=DoctorProfile.STATUS_VERIFIED
            ).select_related('user')

        # Filters
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(specialization__icontains=search) |
                Q(credentials__icontains=search)
            )

        spec = self.request.query_params.get('specialization')
        if spec:
            qs = qs.filter(specialization__icontains=spec)

        min_fee = self.request.query_params.get('min_fee')
        if min_fee:
            try:
                qs = qs.filter(consultation_fee__gte=float(min_fee))
            except ValueError:
                pass

        max_fee = self.request.query_params.get('max_fee')
        if max_fee:
            try:
                qs = qs.filter(consultation_fee__lte=float(max_fee))
            except ValueError:
                pass

        date_str = self.request.query_params.get('date')
        if date_str:
            qs = qs.filter(
                slots__start_at__date=date_str,
                slots__status=AvailabilitySlot.STATUS_AVAILABLE
            ).distinct()

        return qs

class DoctorDetailView(generics.RetrieveAPIView):
    """
    Public doctor profile retrieval.
    """
    queryset = DoctorProfile.objects.all().select_related('user')
    serializer_class = DoctorProfileSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'

class DoctorAvailabilityListView(APIView):
    """
    Retrieves available time slots for a specific doctor.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Get doctor availability slots",
        parameters=[
            OpenApiParameter('date', str, description="Filter slots by date (YYYY-MM-DD)")
        ]
    )
    def get(self, request, id):
        doctor = generics.get_object_or_404(DoctorProfile, id=id)
        now = timezone.now()

        # Dynamic cleanup of expired reservations for this doctor
        expired_consultations = Consultation.objects.filter(
            doctor=doctor,
            status=Consultation.STATUS_BOOKED,
            expires_at__lt=now
        ).select_related('slot')

        for exp_c in expired_consultations:
            with transaction.atomic():
                exp_c.status = Consultation.STATUS_CANCELLED
                exp_c.cancellation_reason = "Reservation expired: payment was not completed within the 10-minute window."
                exp_c.expires_at = None
                exp_c.cancelled_at = now
                exp_c.save(update_fields=['status', 'cancellation_reason', 'expires_at', 'cancelled_at', 'updated_at'])
                if exp_c.slot and exp_c.slot.start_at > now:
                    exp_c.slot.status = AvailabilitySlot.STATUS_AVAILABLE
                    exp_c.slot.save(update_fields=['status', 'updated_at'])

        # Active reservations and bookings to exclude
        active_consultations = Consultation.objects.filter(
            doctor=doctor,
            status__in=[Consultation.STATUS_BOOKED, Consultation.STATUS_CONFIRMED, Consultation.STATUS_IN_PROGRESS]
        ).exclude(status=Consultation.STATUS_BOOKED, expires_at__lt=now)

        active_slot_ids = active_consultations.values_list('slot_id', flat=True)

        slots = AvailabilitySlot.objects.filter(
            doctor=doctor,
            status=AvailabilitySlot.STATUS_AVAILABLE,
            start_at__gte=now
        ).exclude(id__in=active_slot_ids).order_by('start_at')

        date_str = request.query_params.get('date')
        if date_str:
            slots = slots.filter(start_at__date=date_str)

        serializer = AvailabilitySlotSerializer(slots, many=True)
        return Response({"success": True, "slots": serializer.data}, status=status.HTTP_200_OK)

class DoctorProfileMeView(generics.RetrieveUpdateAPIView):
    """
    Allows the logged-in doctor to inspect and update their professional profile.
    """
    permission_classes = [permissions.IsAuthenticated, IsDoctor]
    serializer_class = DoctorProfileUpdateSerializer

    def get_object(self):
        return generics.get_object_or_404(DoctorProfile, user=self.request.user)

    def get(self, request, *args, **kwargs):
        doctor = self.get_object()
        return Response({"success": True, "doctor": DoctorProfileSerializer(doctor).data})

    def patch(self, request, *args, **kwargs):
        doctor = self.get_object()
        serializer = self.get_serializer(doctor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        log_audit_event(
            action='DOCTOR_PROFILE_UPDATED',
            resource_type='DOCTOR',
            resource_id=str(doctor.id),
            actor=request.user,
            request=request,
            outcome=AuditLog.OUTCOME_SUCCESS
        )

        return Response({"success": True, "doctor": DoctorProfileSerializer(doctor).data})

class DoctorMyAvailabilityView(APIView):
    """
    Doctor endpoint to view all their scheduled slots and create new availability slots.
    """
    permission_classes = [permissions.IsAuthenticated, IsDoctor]

    @extend_schema(summary="List doctor's own slots")
    def get(self, request):
        doctor = generics.get_object_or_404(DoctorProfile, user=request.user)
        slots = AvailabilitySlot.objects.filter(doctor=doctor).order_by('start_at')
        serializer = AvailabilitySlotSerializer(slots, many=True)
        return Response({"success": True, "slots": serializer.data})

    @extend_schema(summary="Create doctor availability slot", request=AvailabilitySlotCreateSerializer)
    def post(self, request):
        doctor = generics.get_object_or_404(DoctorProfile, user=request.user)
        serializer = AvailabilitySlotCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        slot = AvailabilitySlot(
            doctor=doctor,
            start_at=serializer.validated_data['start_at'],
            end_at=serializer.validated_data['end_at'],
            status=AvailabilitySlot.STATUS_AVAILABLE
        )
        try:
            slot.full_clean()
            slot.save()
        except Exception as e:
            return Response(
                {"success": False, "error": {"code": "OVERLAPPING_SLOT", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST
            )

        log_audit_event(
            action='AVAILABILITY_SLOT_CREATED',
            resource_type='AVAILABILITY_SLOT',
            resource_id=str(slot.id),
            actor=request.user,
            request=request,
            outcome=AuditLog.OUTCOME_SUCCESS
        )

        return Response({
            "success": True,
            "message": "Availability slot scheduled successfully.",
            "slot": AvailabilitySlotSerializer(slot).data
        }, status=status.HTTP_201_CREATED)

class DoctorSlotDetailView(APIView):
    """
    Doctor endpoint to cancel or modify a specific availability slot.
    """
    permission_classes = [permissions.IsAuthenticated, IsDoctor]

    @extend_schema(summary="Cancel or modify an availability slot")
    def patch(self, request, slot_id):
        doctor = generics.get_object_or_404(DoctorProfile, user=request.user)
        slot = generics.get_object_or_404(AvailabilitySlot, id=slot_id, doctor=doctor)

        if slot.status == AvailabilitySlot.STATUS_BOOKED:
            return Response(
                {"success": False, "error": {"code": "SLOT_ALREADY_BOOKED", "message": "Cannot cancel a slot that has an active booking. Cancel the consultation instead."}},
                status=status.HTTP_400_BAD_REQUEST
            )

        status_action = request.data.get('status')
        if status_action == 'CANCELLED':
            slot.status = AvailabilitySlot.STATUS_CANCELLED
            slot.save(update_fields=['status', 'updated_at'])

        log_audit_event(
            action='AVAILABILITY_SLOT_CANCELLED',
            resource_type='AVAILABILITY_SLOT',
            resource_id=str(slot.id),
            actor=request.user,
            request=request,
            outcome=AuditLog.OUTCOME_SUCCESS
        )

        return Response({"success": True, "slot": AvailabilitySlotSerializer(slot).data})


class DoctorRegisterView(APIView):
    """
    Public registration endpoint for medical doctors.
    Submits registration into PENDING approval status awaiting administrator review.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(summary="Doctor self-registration (Pending Approval)", request=DoctorRegisterSerializer)
    def post(self, request):
        serializer = DoctorRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = DoctorService.register_doctor(serializer.validated_data, request=request)
        return Response(result, status=status.HTTP_201_CREATED)


class AdminDoctorApplicationsListView(APIView):
    """
    Administrator endpoint to view doctor registrations and applications.
    Supports status filtering (PENDING, APPROVED, REJECTED).
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    @extend_schema(summary="List doctor applications for administrator review")
    def get(self, request):
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = DoctorProfile.objects.filter(verification_status=status_filter.upper())
        else:
            qs = DoctorProfile.objects.all()

        qs = qs.select_related('user', 'approved_by').order_by('-created_at')
        serializer = DoctorProfileSerializer(qs, many=True)
        return Response({"success": True, "doctors": serializer.data}, status=status.HTTP_200_OK)


class AdminDoctorApproveView(APIView):
    """
    Administrator endpoint to approve a doctor's registration.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    @extend_schema(summary="Approve doctor registration")
    def post(self, request, id):
        profile = DoctorService.approve_doctor(id, request.user, request=request)
        return Response({
            "success": True,
            "message": f"Dr. {profile.user.full_name} has been approved successfully.",
            "doctor": DoctorProfileSerializer(profile).data
        }, status=status.HTTP_200_OK)


class AdminDoctorRejectView(APIView):
    """
    Administrator endpoint to reject a doctor's registration with a stated reason.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    @extend_schema(summary="Reject doctor registration with reason", request=DoctorRejectSerializer)
    def post(self, request, id):
        serializer = DoctorRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = DoctorService.reject_doctor(id, request.user, serializer.validated_data['reason'], request=request)
        return Response({
            "success": True,
            "message": f"Doctor registration for Dr. {profile.user.full_name} has been rejected.",
            "doctor": DoctorProfileSerializer(profile).data
        }, status=status.HTTP_200_OK)


class AdminDoctorRemoveView(APIView):
    """
    Administrator endpoint to remove an approved doctor who is no longer working with the organization.
    Records joining date, removal date, and marks doctor as REMOVED.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    @extend_schema(summary="Remove/offboard doctor who is no longer with the organization", request=DoctorRemoveSerializer)
    def post(self, request, id):
        serializer = DoctorRemoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason', 'No longer working with the organization')
        profile = DoctorService.remove_doctor(id, request.user, reason, request=request)
        return Response({
            "success": True,
            "message": f"Dr. {profile.user.full_name} has been removed from active practice.",
            "doctor": DoctorProfileSerializer(profile).data
        }, status=status.HTTP_200_OK)

