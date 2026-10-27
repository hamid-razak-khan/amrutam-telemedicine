from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import connection
from django.conf import settings
from drf_spectacular.utils import extend_schema
import django_prometheus.exports

class HealthLiveView(APIView):
    """Liveness probe: verifies process is alive and accepting connections."""
    permission_classes = [permissions.AllowAny]

    @extend_schema(summary="Liveness check", responses={200: dict})
    def get(self, request):
        return Response({
            "status": "healthy",
            "service": "amrutam-telemedicine-backend",
            "uptime": "active"
        }, status=status.HTTP_200_OK)

class HealthReadyView(APIView):
    """Readiness probe: validates database connectivity and core services."""
    permission_classes = [permissions.AllowAny]

    @extend_schema(summary="Readiness check", responses={200: dict, 503: dict})
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
            db_status = "connected"
        except Exception as e:
            return Response({
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({
            "status": "ready",
            "database": db_status,
            "version": "1.0.0"
        }, status=status.HTTP_200_OK)

class RestrictedMetricsView(APIView):
    """Exposes Prometheus metrics, protected by a shared secret header or admin privileges."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '').strip()
        expected = getattr(settings, 'METRICS_TOKEN', 'internal-metrics-secret-key-amrutam')
        
        # Permit if token matches or user is authenticated Admin
        is_admin = bool(request.user and request.user.is_authenticated and (request.user.role == 'ADMIN' or request.user.is_staff))
        if token != expected and not is_admin:
            return Response({"error": "Unauthorized metrics access"}, status=status.HTTP_403_FORBIDDEN)
            
        return django_prometheus.exports.ExportToDjangoView(request)
