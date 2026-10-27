from django.utils.deprecation import MiddlewareMixin
from apps.audit.utils import log_audit_event
from apps.audit.models import AuditLog

class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to catch security exceptions and unauthorized access attempts.
    """
    def process_response(self, request, response):
        # Automatically log permission denied or unauthenticated attempts on API
        if request.path.startswith('/api/v1/') and response.status_code in (401, 403):
            outcome = AuditLog.OUTCOME_DENIED if response.status_code == 403 else AuditLog.OUTCOME_FAILURE
            log_audit_event(
                action='ACCESS_REJECTED',
                resource_type='ENDPOINT',
                resource_id=request.path,
                request=request,
                outcome=outcome,
                metadata={
                    'method': request.method,
                    'status_code': response.status_code,
                    'query_params': dict(request.GET.items())
                }
            )
        return response
