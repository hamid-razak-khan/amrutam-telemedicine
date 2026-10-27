from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from drf_spectacular.utils import extend_schema

from apps.prescriptions.models import Prescription
from apps.prescriptions.serializers import (
    PrescriptionSerializer,
    PrescriptionCreateSerializer
)
from apps.consultations.models import Consultation
from apps.common.permissions import IsDoctor
from apps.audit.utils import log_audit_event
from apps.audit.models import AuditLog

class PrescriptionListCreateForConsultationView(APIView):
    """
    POST: Assigned doctor creates a prescription for an active or completed consultation.
    """
    permission_classes = [permissions.IsAuthenticated, IsDoctor]

    @extend_schema(summary="Create prescription for consultation", request=PrescriptionCreateSerializer)
    def post(self, request, id):
        consultation = Consultation.objects.filter(
            Q(id=id) | Q(booking_reference=id)
        ).select_related('patient', 'doctor', 'doctor__user').first()

        if not consultation:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Consultation not found."}},
                status=status.HTTP_404_NOT_FOUND
            )

        # Permission check: Only assigned doctor
        if consultation.doctor.user != request.user:
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "Only the assigned doctor may prescribe medications for this consultation."}},
                status=status.HTTP_403_FORBIDDEN
            )

        if consultation.status not in (Consultation.STATUS_IN_PROGRESS, Consultation.STATUS_COMPLETED):
            return Response(
                {"success": False, "error": {"code": "INVALID_STATE", "message": "Prescriptions can only be issued for consultations in progress or completed."}},
                status=status.HTTP_400_BAD_REQUEST
            )

        if hasattr(consultation, 'prescription'):
            return Response(
                {"success": False, "error": {"code": "PRESCRIPTION_EXISTS", "message": "A prescription has already been issued for this consultation."}},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PrescriptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        prescription = Prescription.objects.create(
            consultation=consultation,
            doctor=consultation.doctor,
            patient=consultation.patient,
            diagnosis=serializer.validated_data['diagnosis'],
            medications=serializer.validated_data['medications'],
            lifestyle_recommendations=serializer.validated_data.get('lifestyle_recommendations', ''),
            follow_up_date=serializer.validated_data.get('follow_up_date'),
            additional_notes=serializer.validated_data.get('additional_notes', '')
        )

        log_audit_event(
            action='PRESCRIPTION_CREATED',
            resource_type='PRESCRIPTION',
            resource_id=str(prescription.id),
            actor=request.user,
            request=request,
            outcome=AuditLog.OUTCOME_SUCCESS,
            metadata={
                'consultation_id': str(consultation.id),
                'patient_id': str(consultation.patient.id),
                'medication_count': len(prescription.medications)
            }
        )

        return Response({
            "success": True,
            "message": "Prescription generated successfully.",
            "prescription": PrescriptionSerializer(prescription).data
        }, status=status.HTTP_201_CREATED)

class PrescriptionListView(APIView):
    """
    List prescriptions accessible to the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="List accessible prescriptions")
    def get(self, request):
        user = request.user
        if user.role == 'PATIENT':
            prescriptions = Prescription.objects.filter(patient=user).select_related('patient', 'doctor', 'doctor__user', 'consultation')
        elif user.role == 'DOCTOR':
            prescriptions = Prescription.objects.filter(doctor__user=user).select_related('patient', 'doctor', 'doctor__user', 'consultation')
        elif user.role == 'ADMIN' or user.is_staff:
            prescriptions = Prescription.objects.all().select_related('patient', 'doctor', 'doctor__user', 'consultation')
        else:
            prescriptions = Prescription.objects.none()

        serializer = PrescriptionSerializer(prescriptions, many=True)
        return Response({"success": True, "prescriptions": serializer.data})

class PrescriptionDetailView(APIView):
    """
    Retrieve details of a specific prescription with strict tenant isolation.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Retrieve prescription details")
    def get(self, request, id):
        prescription = Prescription.objects.filter(id=id).select_related('patient', 'doctor', 'doctor__user', 'consultation').first()

        if not prescription:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Prescription not found."}},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        if user.role == 'PATIENT' and prescription.patient != user:
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "You cannot access another patient's medical prescription."}},
                status=status.HTTP_403_FORBIDDEN
            )
        if user.role == 'DOCTOR' and prescription.doctor.user != user:
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "You cannot access prescriptions authored by another doctor."}},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response({"success": True, "prescription": PrescriptionSerializer(prescription).data})
