from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.doctors.models import DoctorProfile
from apps.doctors.serializers import DoctorProfileSerializer, DoctorProfileUpdateSerializer
from apps.availability.models import AvailabilitySlot
from apps.availability.serializers import AvailabilitySlotSerializer, AvailabilitySlotCreateSerializer
from apps.common.permissions import IsDoctor
from apps.audit.utils import log_audit_event
from apps.audit.models import AuditLog

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
        slots = AvailabilitySlot.objects.filter(
            doctor=doctor,
            status=AvailabilitySlot.STATUS_AVAILABLE,
            start_at__gte=now
        ).order_by('start_at')

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
