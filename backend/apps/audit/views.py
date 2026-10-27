from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.common.permissions import IsAdminUserRole

class AdminAuditLogListView(generics.ListAPIView):
    """
    Administrator endpoint to view immutable system audit trails.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    @extend_schema(
        summary="Admin audit logs inspection",
        parameters=[
            OpenApiParameter('action', str, description="Filter by action code"),
            OpenApiParameter('resource_type', str, description="Filter by resource type"),
        ]
    )
    def get_queryset(self):
        qs = AuditLog.objects.all().select_related('actor')
        action = self.request.query_params.get('action')
        if action:
            qs = qs.filter(action=action)
        res_type = self.request.query_params.get('resource_type')
        if res_type:
            qs = qs.filter(resource_type=res_type)
        return qs
