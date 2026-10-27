import logging
from apps.audit.models import AuditLog

logger = logging.getLogger('amrutam')

SENSITIVE_PATTERNS = {'password', 'token', 'secret', 'authorization', 'cvv', 'key', 'refresh', 'access'}

def sanitize_metadata(data):
    """Deeply sanitizes dictionaries to ensure zero credential or sensitive leakage."""
    if not isinstance(data, dict):
        return {}
    sanitized = {}
    for k, v in data.items():
        k_str = str(k).lower()
        if any(sens in k_str for sens in SENSITIVE_PATTERNS):
            sanitized[k] = '[REDACTED]'
        elif isinstance(v, dict):
            sanitized[k] = sanitize_metadata(v)
        elif isinstance(v, (list, tuple)):
            sanitized[k] = [sanitize_metadata(item) if isinstance(item, dict) else item for item in v]
        else:
            sanitized[k] = v
    return sanitized

def log_audit_event(
    action,
    resource_type,
    resource_id=None,
    actor=None,
    request=None,
    outcome=AuditLog.OUTCOME_SUCCESS,
    metadata=None
):
    """
    Central helper to record security and operational audit events.
    Captures actor, IP, Request ID, and sanitized payload.
    """
    try:
        actor_email = None
        actor_role = None

        if actor and getattr(actor, 'is_authenticated', False):
            actor_email = actor.email
            actor_role = getattr(actor, 'role', 'UNKNOWN')
        elif request and getattr(request, 'user', None) and request.user.is_authenticated:
            actor = request.user
            actor_email = request.user.email
            actor_role = getattr(request.user, 'role', 'UNKNOWN')

        request_id = getattr(request, 'id', None) if request else None
        ip_address = None
        user_agent = None

        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

        cleaned_meta = sanitize_metadata(metadata or {})

        entry = AuditLog.objects.create(
            actor=actor if actor and getattr(actor, 'is_authenticated', False) else None,
            actor_email=actor_email,
            actor_role=actor_role,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            request_id=request_id,
            outcome=outcome,
            ip_address=ip_address,
            user_agent=user_agent,
            sanitized_metadata=cleaned_meta
        )
        return entry
    except Exception as e:
        logger.error(f"Failed to record audit log: {e}")
        return None
