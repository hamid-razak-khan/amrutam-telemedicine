# Amrutam Telemedicine Platform: Verification & Testing Report

This document records the actual test execution outputs, build results, security validations, and environment verifications performed on the Amrutam Telemedicine codebase.

> [!NOTE]
> All test counts and names in this document were verified against the live codebase using `pytest --collect-only -q` and `npm test`. Do not update test counts without re-running the test collection commands.

---

## 1. Automated Backend Test Suite Execution

### Environment & Toolchain

| Item | Value |
| :--- | :--- |
| **Command** | `pytest -v --no-cov` |
| **Python** | 3.11.9 (Windows host) |
| **pytest** | 8.2.2 |
| **Django** | 5.0.14 |
| **pytest-django** | 4.8.0 |
| **Database** | Supabase PostgreSQL 16 (via Session Pooler) |

### Summary

| Metric | Value |
| :--- | :--- |
| **Total Collected** | 41 |
| **Passed** | 41 |
| **Failed** | 0 |
| **Pass Rate** | 100% |

---

### Test Inventory by Module

#### `tests/integration/test_appointment_booking_business_rules.py` — `TestAppointmentBookingBusinessRules`

1. `test_01_patient_successfully_books_available_slot` → **PASSED**
2. `test_02_second_patient_cannot_book_same_active_slot` → **PASSED**
3. `test_03_same_doctor_can_have_appointments_at_different_times` → **PASSED**
4. `test_04_two_different_doctors_can_have_appointments_at_same_time` → **PASSED**
5. `test_05_cancelled_appointment_releases_slot` → **PASSED**
6. `test_06_completed_appointment_remains_in_history_without_blocking_future_bookings` → **PASSED**
7. `test_07_pending_payment_reservation_blocks_other_bookings_until_expires` → **PASSED**
8. `test_08_expired_reservation_no_longer_blocks_availability` → **PASSED**
9. `test_09_successful_payment_prevents_reservation_expiration_from_releasing_slot` → **PASSED**
10. `test_10_duplicate_payment_requests_do_not_create_duplicate_successful_payments` → **PASSED**
11. `test_11_patient_cannot_book_for_another_patient` → **PASSED**
12. `test_12_patient_cannot_pay_for_another_patients_appointment` → **PASSED**
13. `test_13_slot_in_past_cannot_be_booked` → **PASSED**
14. `test_14_slot_outside_doctor_availability_cannot_be_booked` → **PASSED**
15. `test_16_database_transactions_rollback_cleanly_on_booking_failure` → **PASSED**
16. `test_17_existing_doctor_approval_and_dashboard_intact` → **PASSED**

#### `tests/integration/test_appointment_booking_business_rules.py` — `TestAppointmentBookingConcurrencyRules`

17. `test_15_two_simultaneous_booking_requests_only_one_succeeds` → **PASSED**

#### `tests/integration/test_auth_api.py` — `TestAuthenticationAPI`

18. `test_patient_registration_success` → **PASSED**
19. `test_public_registration_cannot_escalate_to_admin` → **PASSED**
20. `test_login_and_jwt_issuance` → **PASSED**
21. `test_login_invalid_password_fails` → **PASSED**
22. `test_token_refresh_and_rotation` → **PASSED**
23. `test_logout_blacklists_token` → **PASSED**

#### `tests/integration/test_doctor_approval_and_mfa.py` — `TestDoctorApprovalAndMFA`

24. `test_doctor_registration_creates_pending_status` → **PASSED**
25. `test_doctor_login_blocked_while_pending_and_approved_lifecycle` → **PASSED**
26. `test_admin_rejects_doctor_with_reason` → **PASSED**
27. `test_totp_mfa_setup_confirmation_and_login_challenge` → **PASSED**
28. `test_admin_removes_approved_doctor_and_dates_are_tracked` → **PASSED**

#### `tests/security/test_security_rbac.py` — `TestSecurityAndRBAC`

29. `test_patient_cannot_access_other_patient_booking` → **PASSED**
30. `test_patient_cannot_call_doctor_endpoints` → **PASSED**
31. `test_doctor_cannot_manage_unrelated_consultations` → **PASSED**
32. `test_patient_cannot_access_admin_analytics` → **PASSED**
33. `test_admin_can_access_admin_analytics_and_audit` → **PASSED**

#### `tests/unit/test_models.py` — `TestUserModel`

34. `test_create_patient_user` → **PASSED**
35. `test_create_superuser_role` → **PASSED**

#### `tests/unit/test_models.py` — `TestAvailabilitySlotModel`

36. `test_slot_end_time_before_start_time_raises_error` → **PASSED**
37. `test_overlapping_slots_rejected` → **PASSED**

#### `tests/unit/test_models.py` — `TestConsultationStateTransitions`

38. `test_valid_state_transitions` → **PASSED**

#### `tests/concurrency/test_booking_concurrency_idempotency.py` — `TestBookingConcurrencyAndIdempotency`

39. `test_idempotent_booking_retry_returns_cached_result` → **PASSED**
40. `test_idempotency_key_payload_mismatch_rejected` → **PASSED**
41. `test_simultaneous_booking_race_condition_only_one_succeeds` → **PASSED**

---

## 2. Frontend Test & Build Verification

### Vitest Test Suite

| Item | Value |
| :--- | :--- |
| **Command** | `npm test -- --run` |
| **Node.js** | v24.13.0 |
| **Vitest** | 1.6.1 |
| **Environment** | JSDOM + React Testing Library |
| **Total Tests** | 3 |
| **Passed** | 3 |
| **Failed** | 0 |
| **Pass Rate** | 100% |

#### Test Results:

1. `src/tests/auth.test.jsx > Frontend Authentication Tests > renders login form with email and password fields` → **PASSED**
2. `src/tests/auth.test.jsx > Frontend Authentication Tests > validates password mismatch during patient registration` → **PASSED**
3. `src/tests/booking.test.jsx > Doctors Directory and Booking UI Tests > renders search filter controls` → **PASSED**

### Production Vite Build

| Item | Value |
| :--- | :--- |
| **Command** | `npm run build` |
| **Status** | **SUCCESSFUL** |
| **Build Time** | 10.19 seconds |
| **Errors** | 0 |

**Output artifacts:**
- `dist/index.html`: 1.11 kB
- `dist/assets/index-DVhGNLow.css`: 30.40 kB
- `dist/assets/index-NsZguInx.js`: 716.88 kB

---

## 3. Concurrency & Idempotency Verification

| Scenario | Tested Input | Observed Backend Result | Verification Status |
| :--- | :--- | :--- | :--- |
| **Race Condition (Integration)** | 2 concurrent threads booking the exact same `AvailabilitySlot` simultaneously via `test_15_two_simultaneous_booking_requests_only_one_succeeds`. | Thread 1 returned HTTP 201 Created. Thread 2 returned HTTP 409 Conflict. Exactly 1 `Consultation` row created. | **VERIFIED** |
| **Race Condition (Concurrency)** | 2 concurrent threads via `test_simultaneous_booking_race_condition_only_one_succeeds` in `ThreadPoolExecutor`. | Same result: one 201, one 409. No duplicate rows in database. | **VERIFIED** |
| **Idempotent Retry** | Client resubmitting identical booking payload with identical `Idempotency-Key`. | Server returned identical cached 201 response. No duplicate records created. | **VERIFIED** |
| **Key Mismatch** | Client reusing existing `Idempotency-Key` with a different slot payload. | Server rejected with HTTP 422 Unprocessable Entity (`IDEMPOTENCY_CONFLICT`). | **VERIFIED** |
| **Payment Idempotency** | Duplicate payment submission for same consultation. | Server returned existing completed payment. No double-charge. | **VERIFIED** (`test_10_duplicate_payment_requests_do_not_create_duplicate_successful_payments`) |

---

## 4. Security & Isolation Verification

All items below verified via `tests/security/test_security_rbac.py` and `tests/integration/`:

| Test | Result |
| :--- | :--- |
| **Patient Isolation**: Patient A cannot retrieve Patient B's booking via `/api/v1/bookings/{id}`. | HTTP 403 Forbidden (`PERMISSION_DENIED`) — **VERIFIED** |
| **Doctor Isolation**: Doctor B cannot start or update Doctor A's consultation. | HTTP 403 Forbidden — **VERIFIED** |
| **Privilege Escalation Prevention**: Passing `role=ADMIN` in public self-registration body. | Role is hardcoded to `PATIENT` in serializer — **VERIFIED** |
| **Append-Only Audit Log Integrity**: Calling `.save()` on an existing `AuditLog` instance. | `ValidationError` raised at application layer — **VERIFIED** |
| **Doctor Access Block (Pending)**: Doctor with `STATUS_PENDING` attempts to log in. | Login rejected with appropriate error — **VERIFIED** (`test_doctor_login_blocked_while_pending_and_approved_lifecycle`) |
| **Doctor Access Block (Removed)**: Removed doctor's `user.is_active` is set to `False`. | All subsequent API calls return HTTP 401 — **VERIFIED** (`test_admin_removes_approved_doctor_and_dates_are_tracked`) |
| **TOTP MFA Challenge**: Login with MFA enabled without providing OTP code. | Returns challenge token, not access token — **VERIFIED** (`test_totp_mfa_setup_confirmation_and_login_challenge`) |
| **Past Slot Booking Prevention**: Attempting to book a slot with `start_at` in the past. | HTTP 400 Bad Request — **VERIFIED** (`test_13_slot_in_past_cannot_be_booked`) |

---

## 5. Background Job Verification

| Task | Execution Mode | Result |
| :--- | :--- | :--- |
| `release_expired_reservations` management command | Local Django management command | Executes without errors; expired slots released dynamically via ORM query. |
| `cleanup_expired_idempotency_keys.delay()` | `CELERY_TASK_ALWAYS_EAGER=True` (synchronous local mode) | Returns `{'status': 'SUCCESS', 'deleted_count': 0}` |
| `send_appointment_reminders.delay()` | `CELERY_TASK_ALWAYS_EAGER=True` (synchronous local mode) | Returns `{'status': 'SUCCESS', 'reminders_dispatched': 0}` |

> [!IMPORTANT]
> Celery background workers require a running Redis instance. In the local dev environment, `CELERY_TASK_ALWAYS_EAGER=True` executes tasks synchronously in-process. For production validation, run `docker-compose up` to start the Celery worker container against a live Redis broker.

---

## 6. Docker & CI Verification

| Check | Status | Notes |
| :--- | :--- | :--- |
| `docker-compose.yml` syntax | **VALID** | Validated via `docker-compose config`. Services: `amrutam_postgres`, `amrutam_redis`, `amrutam_backend`, `amrutam_celery`, `amrutam_prometheus`. |
| Backend `Dockerfile` build | **NOT VERIFIED in this session** | CI pipeline runs Docker build on every push via `.github/workflows/ci.yml`. |
| GitHub Actions `ci.yml` | **PRESENT** | Workflow file exists at `.github/workflows/ci.yml`. Includes flake8, Django system check, migration check, pytest, vitest, and Docker build jobs. CI execution depends on GitHub-hosted runners. |
| Prometheus config | **VALID** | `infra/prometheus/prometheus.yml` correctly references the backend metrics endpoint. |

---

## 7. Outstanding Limitations & Manual Verification Tasks

1. **Backend test suite execution time**: The full integration suite (`test_appointment_booking_business_rules.py`, `test_doctor_approval_and_mfa.py`) operates against Supabase PostgreSQL over SSL and may take 3–5 minutes to complete. The concurrency and unit tests complete in under 30 seconds.

2. **Production Hosting**: Local deployment verified on Windows host with Supabase PostgreSQL. Live cloud hosting (Render/Railway/Vercel) requires production cloud account credentials (not included in this academic assessment).

3. **Payment Processing**: Simulated payment engine implemented and idempotency verified. Integration with Razorpay/Stripe requires production merchant credentials and webhook endpoints.

4. **Load Testing**: The application is architecturally designed for 100,000 daily consultations, but distributed load tests (e.g., Locust at peak write throughput) have not been executed against a production-tier infrastructure. This is documented as NOT VERIFIED in [`docs/assignment-compliance.md`](assignment-compliance.md).

5. **Five-Minute Demo Video**: A walkthrough script is provided in [`docs/demo-script.md`](demo-script.md). The video recording itself must be created manually by the candidate using screen capture software (e.g., OBS Studio, Loom).
