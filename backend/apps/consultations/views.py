from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from drf_spectacular.utils import extend_schema

from apps.consultations.models import Consultation
from apps.consultations.serializers import (
    ConsultationSerializer,
    ConsultationStartSerializer,
    ConsultationCompleteSerializer
)
from apps.common.permissions import IsDoctor
from apps.audit.utils import log_audit_event
from apps.audit.models import AuditLog

class ConsultationListView(APIView):
    """
    List consultations for the authenticated user based on role.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="List consultations")
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

        serializer = ConsultationSerializer(consultations, many=True)
        return Response({"success": True, "consultations": serializer.data})

class ConsultationDetailView(APIView):
    """
    Retrieve specific consultation with strict role-based tenant checks.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Retrieve consultation details")
    def get(self, request, id):
        consultation = Consultation.objects.filter(
            Q(id=id) | Q(booking_reference=id)
        ).select_related('patient', 'doctor', 'doctor__user', 'slot').first()

        if not consultation:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Consultation not found."}},
                status=status.HTTP_404_NOT_FOUND
            )

        # RBAC Check
        user = request.user
        if user.role == 'PATIENT' and consultation.patient != user:
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "Cannot access another patient's consultation."}},
                status=status.HTTP_403_FORBIDDEN
            )
        if user.role == 'DOCTOR' and consultation.doctor.user != user:
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "Cannot access consultations assigned to another doctor."}},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response({"success": True, "consultation": ConsultationSerializer(consultation).data})

class ConsultationStartView(APIView):
    """
    Assigned doctor starts the clinical consultation, moving status to IN_PROGRESS.
    """
    permission_classes = [permissions.IsAuthenticated, IsDoctor]

    @extend_schema(summary="Start consultation", request=ConsultationStartSerializer)
    def post(self, request, id):
        consultation = Consultation.objects.filter(
            Q(id=id) | Q(booking_reference=id)
        ).select_related('patient', 'doctor', 'doctor__user', 'slot').first()

        if not consultation:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Consultation not found."}},
                status=status.HTTP_404_NOT_FOUND
            )

        if consultation.doctor.user != request.user:
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "Only the assigned doctor may start this consultation."}},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            consultation.transition_to(Consultation.STATUS_IN_PROGRESS, actor=request.user)

            log_audit_event(
                action='CONSULTATION_STARTED',
                resource_type='CONSULTATION',
                resource_id=str(consultation.id),
                actor=request.user,
                request=request,
                outcome=AuditLog.OUTCOME_SUCCESS,
                metadata={'booking_reference': consultation.booking_reference}
            )

            return Response({
                "success": True,
                "message": "Consultation started.",
                "consultation": ConsultationSerializer(consultation).data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"success": False, "error": {"code": "INVALID_STATE_TRANSITION", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST
            )

class ConsultationCompleteView(APIView):
    """
    Assigned doctor marks the consultation as COMPLETED.
    """
    permission_classes = [permissions.IsAuthenticated, IsDoctor]

    @extend_schema(summary="Complete consultation", request=ConsultationCompleteSerializer)
    def post(self, request, id):
        consultation = Consultation.objects.filter(
            Q(id=id) | Q(booking_reference=id)
        ).select_related('patient', 'doctor', 'doctor__user', 'slot').first()

        if not consultation:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Consultation not found."}},
                status=status.HTTP_404_NOT_FOUND
            )

        if consultation.doctor.user != request.user:
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "Only the assigned doctor may complete this consultation."}},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ConsultationCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        clinical_notes = serializer.validated_data.get('clinical_notes', '')

        try:
            if clinical_notes:
                consultation.clinical_notes = clinical_notes
            consultation.transition_to(Consultation.STATUS_COMPLETED, actor=request.user)

            log_audit_event(
                action='CONSULTATION_COMPLETED',
                resource_type='CONSULTATION',
                resource_id=str(consultation.id),
                actor=request.user,
                request=request,
                outcome=AuditLog.OUTCOME_SUCCESS,
                metadata={'booking_reference': consultation.booking_reference}
            )

            return Response({
                "success": True,
                "message": "Consultation completed successfully.",
                "consultation": ConsultationSerializer(consultation).data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"success": False, "error": {"code": "INVALID_STATE_TRANSITION", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST
            )
