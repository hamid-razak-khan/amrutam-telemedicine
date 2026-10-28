# Amrutam Telemedicine: Five-Minute Demonstration Script

This script guides reviewers and evaluators through a comprehensive, step-by-step walkthrough of the Amrutam Telemedicine Platform, demonstrating key architectural, security, and clinical workflows.

> [!IMPORTANT]
> **Security Note**: This script does not contain plaintext passwords or API keys. Use the pre-seeded demonstration accounts described in `README.md § 14` (Administrator Provisioning and Secure Setup). Credentials are stored in the local `.env` file and are not committed to the repository.

---

## Pre-requisites & Local Services

Ensure backend and frontend are running before starting the demonstration:

```bash
# Terminal 1: Backend
cd backend
.\venv\Scripts\python.exe manage.py runserver 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

| Service | URL |
| :--- | :--- |
| **Frontend Application** | `http://localhost:3000` |
| **Backend API Base** | `http://localhost:8000/api/v1` |
| **Swagger / OpenAPI UI** | `http://localhost:8000/api/docs/` |
| **Liveness Health Probe** | `http://localhost:8000/health/live` |
| **Readiness Health Probe** | `http://localhost:8000/health/ready` |
| **Prometheus Metrics** | `http://localhost:8000/metrics` (requires `METRICS_TOKEN` header) |

---

## Demonstration Timeline (5 Minutes)

### Minute 0:00 – 0:45 — Platform Health & Interactive Swagger Documentation

1. **Liveness & Readiness Health Probes**:
   - Open `http://localhost:8000/health/live` → confirms backend is running.
   - Open `http://localhost:8000/health/ready` → confirm `{"status": "ready", "database": "connected"}`, verifying active Supabase PostgreSQL connection pooling.

2. **Interactive OpenAPI 3.0 Documentation**:
   - Navigate to `http://localhost:8000/api/docs/`.
   - Point out the auto-generated Swagger UI from `drf-spectacular`: authentication schemes, request/response schemas, `Idempotency-Key` header requirement on booking endpoints, and the complete API surface across all domain modules.

---

### Minute 0:45 – 1:45 — Patient Discovery & Transaction-Safe Booking

1. **Patient Login**:
   - Sign in using the pre-seeded **Patient** demonstration account (see `README.md § 14`).
   - If MFA is enabled for this account, you will receive a short-lived challenge token. Open your authenticator app, enter the 6-digit TOTP code, and complete the `POST /api/v1/auth/mfa/verify-login` challenge.

2. **Doctor Directory Search**:
   - Navigate to **Consult Doctors** (`/doctors`).
   - Search for `"Kayachikitsa"` or filter by maximum consultation fee.
   - Click **Book Slot** on **Dr. Rajesh Sharma**.

3. **Pessimistic Slot Claiming**:
   - In the booking modal, pick an open availability slot.
   - Enter a symptom description (e.g., *"Experiencing seasonal indigestion and fatigue"*).
   - Click **Confirm & Reserve Appointment**.
   - Show the instant booking confirmation with a unique reference (e.g., `AMR-20261028-XXXXX`) and a **10-minute payment countdown timer**.

---

### Minute 1:45 – 2:30 — Concurrency Race Condition & Idempotency Verification

1. **Idempotency Protection**:
   - Re-send the exact same booking request with the same `Idempotency-Key` header (either via Swagger UI or a duplicate browser tab submitting simultaneously).
   - The platform immediately replays the cached `201 Created` response without inserting a duplicate `Consultation` row.

2. **Race Condition Prevention**:
   - If two patients attempt to book the exact same slot simultaneously, PostgreSQL row locking (`select_for_update()`) serializes the transactions.
   - The first patient secures the slot (HTTP 201); the second immediately receives:
     ```json
     {
       "success": false,
       "error": {
         "code": "SLOT_UNAVAILABLE",
         "message": "Sorry, this time slot has just been booked. Please select another available time."
       }
     }
     ```
   - This is proven by `test_15_two_simultaneous_booking_requests_only_one_succeeds` and `test_simultaneous_booking_race_condition_only_one_succeeds` in the automated test suite.

---

### Minute 2:30 – 3:30 — Doctor Workspace & Prescription Workflow

1. **Switch to Doctor Account**:
   - Log out. On the login page, sign in using the pre-seeded **Approved Doctor** demonstration account (see `README.md § 14`).
   - Land on the **Doctor Workspace** (`/doctor/dashboard`).

2. **Consultation State Machine Transitions**:
   - Locate the scheduled consultation created above.
   - Click **Start Consultation** → status transitions to `IN_PROGRESS`.
   - Click **Complete Consultation** → status transitions to `COMPLETED`.

3. **Structured Ayurvedic Prescription**:
   - Click **Issue Prescription**.
   - Add classical Ayurvedic formulations (e.g., *Triphala Churna*, *Amrutam Kuntal Care Herbal Malt*) with precise dosage, duration, and instructions.
   - Add *Pathya* (dietary) recommendations.
   - Submit the prescription.

4. **Patient Tenant Isolation**:
   - Switch back to the patient account; verify the prescription appears at `/patient/prescriptions`.
   - A different patient account **cannot** access this prescription (proven by `test_patient_cannot_access_other_patient_booking` in `test_security_rbac.py`).

---

### Minute 3:30 – 4:15 — Administrator Telemetry & Forensic Audit Logs

1. **Admin Sign In**:
   - Log out, then sign in using the pre-seeded **Administrator** demonstration account (see `README.md § 14`).
   - Navigate to **Admin Analytics** (`/admin/dashboard`).

2. **Recharts Visualizations**:
   - Review live Area Charts showing daily consultation trajectory across the last 14 days.
   - Review Bar Charts of consultation status distribution (BOOKED, CONFIRMED, IN_PROGRESS, COMPLETED, CANCELLED).
   - Review Gross Revenue and Cancellation Rate KPIs.
   - Note the sub-100 ms load time (the backend executes a single range query rather than per-day sequential queries).

3. **Doctor Lifecycle Management**:
   - Navigate to the **Doctors** tab.
   - Review the **Removed Doctors** filter tab, which displays joining dates and removal dates for offboarded practitioners.
   - Show the **Remove Doctor** action (with confirmation modal and reason input) and **Restore Doctor** action.

4. **Forensic Audit Trails**:
   - Navigate to **Audit Logs** (`/admin/audit-logs`).
   - Show the append-only log entries capturing `AUTH_LOGIN`, `BOOKING_CREATED`, `CONSULTATION_STARTED`, `PRESCRIPTION_CREATED`, and `DOCTOR_REMOVED` events.
   - Each log entry displays: actor, action type, resource, IP address, `X-Request-ID` correlation identifier, and sanitized (password-redacted) metadata.

---

### Minute 4:15 – 5:00 — Automated Test Suite & Infrastructure Verification

1. **Run Backend Test Suite**:
   ```bash
   cd backend
   pytest -v --no-cov
   ```
   - Demonstrates 41 tests passing: unit model validations, authentication flows, security RBAC isolation, appointment booking business rules, doctor lifecycle (approval, rejection, removal, MFA), and multi-threaded concurrency race conditions.

2. **Run Frontend Test Suite**:
   ```bash
   cd frontend
   npm test -- --run
   ```
   - Demonstrates Vitest component rendering and form validation tests (3 tests, 100% pass rate).

3. **Conclusion**:
   - Summarize the clean modular monolithic architecture, pessimistic concurrency guarantee, TOTP MFA, append-only audit trail, and full compliance with the assignment requirements.
   - Reference [`docs/assignment-compliance.md`](assignment-compliance.md) for the complete 50-item requirement-compliance matrix.

---

## Demo Accounts Quick Reference

Refer to `README.md § 14` for the full list of pre-seeded demonstration accounts and their roles. Credentials are **not** published in public-facing documentation.

## Technical Support References

| Document | Purpose |
| :--- | :--- |
| [`docs/architecture.md`](architecture.md) | System data flow, ER diagram, booking sequence diagram |
| [`docs/assignment-compliance.md`](assignment-compliance.md) | 50-item requirement compliance matrix |
| [`docs/verification-report.md`](verification-report.md) | Actual test execution results (41 backend + 3 frontend) |
| [`docs/security-checklist.md`](security-checklist.md) | Implemented security controls |
| [`docs/threat-model.md`](threat-model.md) | STRIDE threat analysis |
