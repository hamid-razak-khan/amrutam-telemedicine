# Amrutam Telemedicine: Five-Minute Demonstration Script

This script guides reviewers and evaluators through a comprehensive, step-by-step walkthrough of the Amrutam Telemedicine Platform, demonstrating key architectural, security, and clinical workflows.

---

## Pre-requisites & Local Services
Ensure backend and frontend are running:
```bash
# Terminal 1: Backend
cd backend
.\venv\Scripts\python.exe manage.py runserver 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Frontend URL: `http://localhost:3000`  
Backend API Base: `http://localhost:8000/api/v1`  
Swagger Documentation: `http://localhost:8000/api/docs/`  
Health Endpoint: `http://localhost:8000/health/ready`  

---

## Demonstration Timeline (5 Minutes)

### Minute 0:00 – 0:45: Platform Health & Interactive Swagger Documentation
1. **Liveness & Readiness**:
   - Open browser to `http://localhost:8000/health/live` & `http://localhost:8000/health/ready`.
   - Show `{"status": "ready", "database": "connected"}` verifying active connection pooling.
2. **Interactive OpenAPI 3.0 Documentation**:
   - Navigate to `http://localhost:8000/api/docs/`.
   - Point out the comprehensive OpenAPI schema generated via `drf-spectacular`, detailing authentication, request/response schemas, and `Idempotency-Key` headers.

---

### Minute 0:45 – 1:45: Patient Discovery & Transaction-Safe Booking
1. **Patient Login**:
   - Go to `http://localhost:3000/login`.
   - Click the **"Patient"** fast demo credentials button (loads `patient1@example.com` / `PatientPassword123!`).
   - Click **Sign In to Platform**.
2. **Doctor Directory Search**:
   - Navigate to **Consult Doctors** (`/doctors`).
   - Search for "Kayachikitsa" or filter by maximum fee.
   - Click **Book Slot** on **Dr. Rajesh Sharma**.
3. **Pessimistic Slot Claiming**:
   - In the modal, pick an open slot.
   - Enter symptom description: *"Experiencing severe seasonal indigestion."*
   - Point out the unique generated `Idempotency-Key` guarantee shown at the bottom.
   - Click **Confirm & Reserve Appointment**.
   - Show instant confirmation with unique booking reference (e.g. `AMR-20261027-ABC123`).

---

### Minute 1:45 – 2:30: Concurrency Race Condition & Idempotency Verification
1. **Idempotency Protection Demonstration**:
   - Re-send the exact same booking request using the same `Idempotency-Key`.
   - The platform immediately replays the cached 201/200 response without creating a duplicate consultation in the database.
2. **Race Condition Prevention Demonstration**:
   - If two patients attempt to book the exact same slot concurrently, PostgreSQL row locking (`select_for_update()`) serializes the transactions.
   - The first patient secures the booking; the second immediately receives:
     ```json
     {
       "success": false,
       "error": {
         "code": "SLOT_UNAVAILABLE",
         "message": "This slot has already been booked or is no longer available."
       }
     }
     ```

---

### Minute 2:30 – 3:30: Doctor Workspace & Prescription Workflow
1. **Switch to Doctor Account**:
   - Log out, then on the login page click **"Doctor"** (`dr.sharma@amrutam.co.in` / `DoctorPassword123!`).
   - Land on the **Doctor Workspace** (`/doctor/dashboard`).
2. **State Machine Transition**:
   - Locate the scheduled consultation.
   - Click **Start Consultation** &rarr; status updates to `IN_PROGRESS`.
   - Click **Complete Consultation** &rarr; status transitions to `COMPLETED`.
3. **Structured Ayurvedic Formulation**:
   - Click **Issue Prescription**.
   - Prescribe classical formulations (e.g., *Amrutam Kuntal Care Herbal Malt*, *Triphala Churna*) with precise dosage and dietary pathya.
   - Submit prescription.
4. **Tenant Isolation Check**:
   - Switch back to Patient 1: view the newly assigned prescription with complete instructions at `/patient/prescriptions`.
   - Verify Patient 2 cannot view Patient 1's prescription (tested and proven via test suite).

---

### Minute 3:30 – 4:15: Administrator Telemetry & Forensic Audit Logs
1. **Admin Sign In**:
   - Log out, then click **"Admin"** (`admin@amrutam.co.in` / `AdminPassword123!`).
   - Navigate to **Admin Analytics** (`/admin/dashboard`).
2. **Recharts Visualizations**:
   - Review live Area Charts showing daily consultation trajectory and Bar Charts of status distributions.
   - Review Gross Revenue and Cancellation Rate metrics.
3. **Forensic Audit Trails**:
   - Click **Inspect Audit Logs** (`/admin/audit-logs`).
   - Show the append-only logs capturing `AUTH_LOGIN`, `BOOKING_CREATED`, `CONSULTATION_STARTED`, and `PRESCRIPTION_CREATED` events with sanitized metadata and `X-Request-ID` tracing.

---

### Minute 4:15 – 5:00: Automated Test Suite & Infrastructure Verification
1. **Run Backend Test Suite**:
   ```bash
   pytest -v
   ```
   - Show 19/19 tests passing: unit models, authentication, security RBAC, and multi-threaded concurrency race conditions.
2. **Run Frontend Test Suite**:
   ```bash
   npm test
   ```
   - Show Vitest component and form validation tests passing.
3. **Conclusion**:
   - Summarize the clean modular monolithic architecture, independent deployment readiness, and compliance with all assignment objectives.
