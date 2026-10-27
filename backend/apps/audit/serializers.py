from rest_framework import serializers
from apps.audit.models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.full_name', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'actor_id', 'actor_name', 'actor_email', 'actor_role',
            'action', 'resource_type', 'resource_id', 'timestamp',
            'request_id', 'outcome', 'ip_address', 'sanitized_metadata'
        ]
