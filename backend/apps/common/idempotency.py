import hashlib
import json
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from apps.common.models import IdempotencyKey

class IdempotencyConflictError(Exception):
    def __init__(self, message, code=409, cached_response=None):
        super().__init__(message)
        self.code = code
        self.cached_response = cached_response

def compute_payload_hash(data):
    """Computes deterministic SHA-256 hash of request payload."""
    if isinstance(data, dict):
        serialized = json.dumps(data, sort_keys=True, default=str)
    elif isinstance(data, (str, bytes)):
        serialized = str(data)
    else:
        serialized = str(data or '')
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

def check_idempotency(request, operation, payload_data):
    """
    Checks or registers an idempotency key.
    If the key already completed with the same payload, returns (cached_response, None).
    If a new key, returns (None, key_record).
    If conflict or mismatch, raises IdempotencyConflictError.
    """
    key_str = request.headers.get('Idempotency-Key')
    if not key_str:
        return None, None

    user = request.user
    payload_hash = compute_payload_hash(payload_data)
    now = timezone.now()

    with transaction.atomic():
        key_record = IdempotencyKey.objects.select_for_update().filter(
            key=key_str,
            user=user,
            operation=operation
        ).first()

        if key_record:
            if key_record.is_expired():
                # Clean up expired record to allow fresh request
                key_record.delete()
            else:
                # Check payload match
                if key_record.request_hash != payload_hash:
                    raise IdempotencyConflictError(
                        "Idempotency key has already been used with a different request payload.",
                        code=422
                    )

                if key_record.status == IdempotencyKey.STATUS_COMPLETED:
                    return {
                        'status_code': key_record.response_code or 200,
                        'data': key_record.response_body
                    }, None
                elif key_record.status == IdempotencyKey.STATUS_PROCESSING:
                    raise IdempotencyConflictError(
                        "A request with this idempotency key is currently being processed. Please retry in a few moments.",
                        code=409
                    )
                # If FAILED, we allow re-attempting
                key_record.status = IdempotencyKey.STATUS_PROCESSING
                key_record.save(update_fields=['status', 'updated_at'])
                return None, key_record

        # Create new idempotency record
        new_key = IdempotencyKey.objects.create(
            key=key_str,
            user=user,
            operation=operation,
            request_hash=payload_hash,
            status=IdempotencyKey.STATUS_PROCESSING,
            expires_at=now + timedelta(hours=24)
        )
        return None, new_key

def complete_idempotency(key_record, response_code, response_data):
    """Marks idempotency record as completed with stored response."""
    if key_record:
        try:
            key_record.status = IdempotencyKey.STATUS_COMPLETED
            key_record.response_code = response_code
            key_record.response_body = response_data
            key_record.save(update_fields=['status', 'response_code', 'response_body', 'updated_at'])
        except Exception:
            pass

def fail_idempotency(key_record):
    """Marks idempotency record as failed so it does not block future retries."""
    if key_record:
        try:
            key_record.status = IdempotencyKey.STATUS_FAILED
            key_record.save(update_fields=['status', 'updated_at'])
        except Exception:
            pass
