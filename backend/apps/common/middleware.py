import uuid
import time
from django.utils.deprecation import MiddlewareMixin

class RequestIdMiddleware(MiddlewareMixin):
    """
    Assigns or preserves a unique X-Request-ID for distributed tracing across services.
    Measures request processing duration.
    """
    def process_request(self, request):
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        request.id = request_id
        request._start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, 'id'):
            response['X-Request-ID'] = request.id
        if hasattr(request, '_start_time'):
            duration = round((time.time() - request._start_time) * 1000, 2)
            response['X-Response-Time-MS'] = str(duration)
        return response
