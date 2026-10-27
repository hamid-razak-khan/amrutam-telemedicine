import json
import logging
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    """
    Structured JSON log formatter for production observability.
    Strips authorization headers, tokens, and sensitive fields.
    """
    SENSITIVE_KEYS = {'password', 'token', 'authorization', 'secret', 'access_token', 'refresh_token', 'cvv'}

    def format(self, record):
        log_record = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'severity': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        # Include request metadata if attached to record
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'http_method'):
            log_record['http_method'] = record.http_method
        if hasattr(record, 'route'):
            log_record['route'] = record.route
        if hasattr(record, 'status_code'):
            log_record['status_code'] = record.status_code
        if hasattr(record, 'duration_ms'):
            log_record['duration_ms'] = record.duration_ms

        # Sanitize any extra dict info
        if hasattr(record, 'extra_data') and isinstance(record.extra_data, dict):
            sanitized = {}
            for k, v in record.extra_data.items():
                if any(sens in k.lower() for sens in self.SENSITIVE_KEYS):
                    sanitized[k] = '[REDACTED]'
                else:
                    sanitized[k] = v
            log_record['metadata'] = sanitized

        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_record)
