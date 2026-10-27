# Amrutam Telemedicine Backend API

Production-ready, transaction-safe REST API engineered with Python 3.11, Django 5.0, Django REST Framework, SimpleJWT, Celery, and PostgreSQL.

---

## Architecture Highlights
- **Modular Monolith**: Separated domains for `accounts`, `doctors`, `availability`, `bookings`, `consultations`, `prescriptions`, `payments`, `audit`, `analytics`, and `common`.
- **Custom User Model**: `accounts.User` initialized before the first migration with role-based segregation (`PATIENT`, `DOCTOR`, `ADMIN`).
- **Pessimistic Concurrency**: Row-level locking via `select_for_update()` inside `transaction.atomic()` to prevent appointment race conditions.
- **Idempotency Protection**: SHA-256 fingerprinting of payloads and `Idempotency-Key` tracking header ensuring safe write retries.
- **Append-Only Audit Log**: Application-level immutable logging of security and clinical actions with automated credential redaction.
- **Observability**: Prometheus metrics (`/metrics`), structured JSON logging with `X-Request-ID` tracing, and health probes (`/health/live`, `/health/ready`).

---

## Local Setup & Development

### 1. Create Virtual Environment & Install Dependencies
```bash
# In backend/ directory
python -m venv venv
.\venv\Scripts\activate    # Windows
source venv/bin/activate     # macOS/Linux

pip install -r requirements-dev.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default `.env` configuration uses SQLite with Write-Ahead Logging (WAL) for local dev when PostgreSQL is not running. Set `DATABASE_URL` to connect to PostgreSQL.

### 3. Run Migrations & Seed Synthetic Data
```bash
python manage.py migrate
python manage.py seed_data
```
The seed command creates:
- Admin: `admin@amrutam.co.in` / `AdminPassword123!`
- Doctors: `dr.sharma@amrutam.co.in`, `dr.ananya@amrutam.co.in` / `DoctorPassword123!`
- Patients: `patient1@example.com`, `patient2@example.com` / `PatientPassword123!`
- 120+ active availability slots across certified doctors.

### 4. Run Development Server
```bash
python manage.py runserver 8000
```

---

## Running Automated Tests
```bash
pytest -v
```
Runs 19 comprehensive unit, integration, RBAC security, and multi-threaded concurrency race condition tests.

---

## OpenAPI & Swagger Documentation
- Swagger UI: `http://localhost:8000/api/docs/`
- OpenAPI 3.0 Schema: `http://localhost:8000/api/schema/`
- Health Liveness: `http://localhost:8000/health/live`
- Health Readiness: `http://localhost:8000/health/ready`
