# AMRUTAM TELEMEDICINE PLATFORM
### Full-Stack Backend & Frontend Engineering Assignment for Amrutam Pharmaceuticals Pvt. Ltd.

![Amrutam Telemedicine](https://img.shields.io/badge/Status-Complete-emerald)
![Backend](https://img.shields.io/badge/Backend-Django%205.0%20%7C%20DRF-green)
![Frontend](https://img.shields.io/badge/Frontend-React%2018%20%7C%20Vite%20%7C%20Tailwind-blue)
![Database](https://img.shields.io/badge/Database-PostgreSQL%2016-blue)
![Async](https://img.shields.io/badge/Async-Celery%205.4%20%7C%20Redis%207-red)
![Tests](https://img.shields.io/badge/Tests-100%25%20Passing%20(19%2F19)-brightgreen)

---

## 1. Executive Summary & Architecture Overview
The **Amrutam Telemedicine Platform** is an enterprise-grade, transaction-safe clinical healthcare system engineered to deliver authentic Ayurvedic consultations at scale. Engineered to support **100,000 daily consultations**, the platform features a decoupled modular monolith backend in Python/Django REST Framework, PostgreSQL with pessimistic concurrency control, Redis & Celery for asynchronous background jobs, structured JSON logging, and a responsive React (JavaScript, Vite, Tailwind CSS) frontend.

### Key Architectural Pillars
- **Transactional Booking & Zero Double-Booking**: Atomic database transactions (`transaction.atomic()`) with row-level locks (`select_for_update()`) and database check constraints guarantee that competing patients cannot claim the same slot.
- **Idempotency Protection**: Every booking request enforces a unique client `Idempotency-Key` header with SHA-256 payload hashing, preventing duplicate appointments and double-spending across network retries.
- **Strict Role-Based Access Control (RBAC)**: Distinct authorization boundaries for `PATIENT`, `DOCTOR`, and `ADMIN`. Public registration strictly creates `PATIENT` accounts; privilege escalation attempts are rejected.
- **Append-Only Forensic Audit Trail**: Application-level immutable `AuditLog` capturing actor, action, resource, IP, Request ID, and sanitized metadata (automatic redaction of passwords, tokens, and authorization headers).
- **Structured Ayurvedic Prescriptions**: Assigned doctors issue structured digital prescriptions with classical formulations, dosages, durations, and dietary pathya guidelines. Access is strictly tenant-isolated.
- **Observability**: Prometheus metrics (`/metrics`), structured JSON logging with `X-Request-ID` tracing, and health probes (`/health/live`, `/health/ready`).

---

## 2. Mandatory Project Structure

```
amrutam-telemedicine/
├── frontend/                         # React application (Vite + Tailwind CSS + Lucide + Recharts)
│   ├── public/                       # Static public assets and favicon
│   ├── src/
│   │   ├── api/                      # Centralized Axios instance & modular API clients
│   │   │   ├── axios.js
│   │   │   ├── auth.js
│   │   │   ├── users.js
│   │   │   ├── doctors.js
│   │   │   ├── availability.js
│   │   │   ├── bookings.js
│   │   │   ├── consultations.js
│   │   │   ├── prescriptions.js
│   │   │   ├── payments.js
│   │   │   ├── analytics.js
│   │   │   └── audit.js
│   │   ├── components/               # Navbar, Footer, ProtectedRoute
│   │   ├── layouts/                  # AppLayout
│   │   ├── pages/
│   │   │   ├── auth/                 # Login & Register
│   │   │   ├── patient/              # DoctorsDirectory, Appointments, Prescriptions
│   │   │   ├── doctor/               # Dashboard, AvailabilityManager
│   │   │   ├── admin/                # AdminDashboard, AdminAuditLogs
│   │   │   ├── Home.jsx              # Landing page
│   │   │   └── UserProfile.jsx       # Profile settings
│   │   ├── context/                  # AuthContext with token refresh & session handling
│   │   ├── utils/                    # Utility functions (cn.js)
│   │   ├── tests/                    # Vitest frontend tests
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── .env.example
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── README.md
│
├── backend/                          # Django REST API
│   ├── config/                       # Settings, URLs, WSGI, ASGI, Celery
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   └── celery.py
│   ├── apps/
│   │   ├── accounts/                 # Custom User model, PatientProfile, Auth views
│   │   ├── doctors/                  # DoctorProfile, doctor directory, availability views
│   │   ├── availability/             # AvailabilitySlot model with overlap constraints
│   │   ├── bookings/                 # Booking model, transaction-safe booking view
│   │   ├── consultations/            # Consultation state machine (Start, Complete, Cancel)
│   │   ├── prescriptions/            # Structured prescription items & tenant checks
│   │   ├── payments/                 # Simulated payment engine & idempotency
│   │   ├── audit/                    # Append-only AuditLog & middleware
│   │   ├── analytics/                # Aggregations for Recharts dashboard
│   │   └── common/                   # Idempotency, Request-ID, exceptions, health, tasks
│   ├── tests/                        # Comprehensive test suite
│   │   ├── unit/                     # Models, constraints, state transitions
│   │   ├── integration/              # Auth, JWT, registration, doctor search
│   │   ├── security/                 # Multi-tenant isolation & RBAC
│   │   └── concurrency/              # Multi-threaded race condition tests
│   ├── manage.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── .env.example
│   └── README.md
│
├── docs/                             # Technical & Security Documentation
│   ├── architecture.md               # Mermaid diagrams, ER schema, booking sequence, scaling
│   ├── threat-model.md               # STRIDE threat analysis, assets, trust boundaries
│   ├── security-checklist.md         # Implemented controls vs outstanding requirements
│   ├── demo-script.md                # 5-minute evaluator demonstration walkthrough
│   └── verification-report.md        # Actual test counts, concurrency outcomes, build logs
│
├── infra/                            # Infrastructure and Prometheus configurations
│   └── prometheus/
│       └── prometheus.yml
├── .github/
│   └── workflows/
│       └── ci.yml                    # Automated GitHub Actions CI/CD pipeline
├── .gitignore
├── docker-compose.yml                # Multi-container orchestration (DB, Redis, Web, Celery)
└── README.md
```

---

## 3. Technology Stack

### Backend
- **Framework**: Python 3.11, Django 5.0, Django REST Framework 3.15
- **Authentication**: JWT via `djangorestframework-simplejwt` with rotation and blacklisting
- **Relational Storage**: PostgreSQL 16 (production/Docker) & SQLite WAL (local non-daemon dev fallback)
- **Concurrency Control**: `transaction.atomic()`, `select_for_update()`, check constraints
- **Task Queue**: Celery 5.4, Redis 7
- **API Documentation**: OpenAPI 3.0 via `drf-spectacular`
- **Testing**: `pytest`, `pytest-django`, `pytest-cov`, `ThreadPoolExecutor`
- **WSGI / Production**: Gunicorn 22.0, Whitenoise 6.6

### Frontend
- **Core**: React 18, JavaScript & JSX (Strictly no TypeScript, no `.ts`/`.tsx`)
- **Build Tool**: Vite 5.3
- **Styling**: Tailwind CSS 3.4 (Amrutam Ayurvedic herbal palette, accessible contrast)
- **Routing**: React Router 6.24
- **HTTP Client**: Centralized Axios with automatic 401 token refresh queue
- **Icons & Visualizations**: Lucide React, Recharts 2.12
- **Testing**: Vitest, JSDOM, React Testing Library

---

## 4. Quickstart: Local Setup & Running

### Prerequisites
- Python 3.11+
- Node.js 18+ (Node 20+ recommended)
- Git

### Backend Setup
```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment & activate
python -m venv venv
.\venv\Scripts\activate    # Windows
# source venv/bin/activate  # macOS / Linux

# 3. Install dependencies
pip install -r requirements-dev.txt

# 4. Initialize environment
cp .env.example .env

# 5. Run migrations & seed synthetic test data
python manage.py migrate
python manage.py seed_data

# 6. Start Django server
python manage.py runserver 8000
```
Backend will start on: **`http://localhost:8000`**

### Frontend Setup
```bash
# 1. In a new terminal, navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```
Frontend will start on: **`http://localhost:3000`**

---

## 5. Pre-Seeded Synthetic Credentials

The `seed_data` management command populates ready-to-test accounts:

| Role | Email Address | Password | Permissions & Notes |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@amrutam.co.in` | `AdminPassword123!` | Access to Admin Analytics, Recharts telemetry, and Audit Log inspector. |
| **Doctor** | `dr.sharma@amrutam.co.in` | `DoctorPassword123!` | Senior Ayurvedic Vaidya. Manage slots, start/complete consultations, issue prescriptions. |
| **Doctor** | `dr.ananya@amrutam.co.in` | `DoctorPassword123!` | Ayurvedic Dermatology specialist. |
| **Patient** | `patient1@example.com` | `PatientPassword123!` | Rahul Verma. Book slots, pay simulated fees, inspect prescriptions. |
| **Patient** | `patient2@example.com` | `PatientPassword123!` | Sneha Patel. Pre-seeded patient for cross-tenant testing. |

> **Fast Demo Tip**: On the `/login` page, click any of the **Fast Demo Credentials** buttons (Patient, Doctor, Admin) to instantly populate credentials.

---

## 6. Running Automated Tests

### Backend Test Suite (Pytest)
```bash
cd backend
pytest -v
```
**Result**: **19 passed** (100% pass rate).  
Validates:
- Registration, JWT login, token rotation, logout blacklisting
- Overlapping availability slot rejection (`check_slot_end_after_start`)
- Multi-tenant tenant access isolation (Patient A vs Patient B, Doctor A vs Doctor B)
- Privilege escalation prevention (passing `role='ADMIN'` to public registration)
- **Multi-threaded booking race condition**: two simultaneous threads attempting to claim the same slot &rarr; exactly 1 succeeds (201), the other is rejected (409 Conflict)
- **Idempotency tests**: replaying same key with same payload returns cached response; reusing same key with different payload returns 422 Conflict.

### Frontend Test Suite (Vitest)
```bash
cd frontend
npm test
```
**Result**: **3 passed** (100% pass rate).  
Validates login form rendering, registration password mismatch validation, and doctor search controls.

---

## 7. Containerized Infrastructure (Docker Compose)

To run the complete production-grade stack including PostgreSQL 16, Redis 7, Django, Celery worker, and Prometheus:
```bash
docker-compose up --build
```
Services started:
- `amrutam_postgres`: PostgreSQL 16 database with health check
- `amrutam_redis`: Redis 7 in-memory cache and task broker
- `amrutam_backend`: Gunicorn application server on port `8000`
- `amrutam_celery`: Background Celery worker process
- `amrutam_prometheus`: Prometheus scraper on port `9090`

---

## 8. API Endpoints Reference

All endpoints prefixed with `/api/v1/`:

### Authentication & Users
- `POST /api/v1/auth/register`: Public patient self-registration
- `POST /api/v1/auth/login`: User login, issues JWT access & refresh tokens
- `POST /api/v1/auth/refresh`: Refresh token rotation
- `POST /api/v1/auth/logout`: Revoke and blacklist refresh token
- `GET /api/v1/auth/me`: Authenticated user profile and permissions
- `GET /api/v1/users/me`: Retrieve profile
- `PATCH /api/v1/users/me`: Update permitted profile fields

### Doctors & Availability
- `GET /api/v1/doctors`: Search verified doctors (filters: `search`, `specialization`, `min_fee`, `max_fee`, `date`)
- `GET /api/v1/doctors/{id}`: Doctor details
- `GET /api/v1/doctors/{id}/availability`: Available slots for doctor
- `PATCH /api/v1/doctors/me/profile`: Doctor updates professional bio & fee
- `POST /api/v1/doctors/me/availability`: Doctor creates availability slots
- `PATCH /api/v1/doctors/me/availability/{slot_id}`: Cancel availability slot

### Bookings & Concurrency
- `POST /api/v1/bookings`: Transaction-safe booking with `Idempotency-Key` header
- `GET /api/v1/bookings`: List appointments for current user
- `GET /api/v1/bookings/{id}`: Retrieve booking details (tenant-isolated)
- `POST /api/v1/bookings/{id}/cancel`: Cancel booking and release slot

### Consultations & Prescriptions
- `GET /api/v1/consultations`: List consultations
- `GET /api/v1/consultations/{id}`: Consultation details
- `POST /api/v1/consultations/{id}/start`: Assigned doctor starts consultation (`IN_PROGRESS`)
- `POST /api/v1/consultations/{id}/complete`: Assigned doctor completes consultation (`COMPLETED`)
- `POST /api/v1/consultations/{id}/prescriptions`: Issue structured prescription
- `GET /api/v1/prescriptions`: List accessible prescriptions
- `GET /api/v1/prescriptions/{id}`: Retrieve prescription (tenant-isolated)

### Payments & Administration
- `POST /api/v1/payments`: Process simulated payment (idempotent)
- `GET /api/v1/payments/{id}`: Retrieve payment record
- `GET /api/v1/admin/analytics/overview`: High-level operational metrics
- `GET /api/v1/admin/analytics/consultations`: Time-series trends for Recharts
- `GET /api/v1/admin/audit-logs`: Paginated append-only audit trail
- `GET /health/live`: Process liveness check
- `GET /health/ready`: Database connectivity readiness check
- `GET /metrics`: Prometheus metrics

---

## 9. Independent Deployment Guide

### Backend Deployment (Render / Railway / AWS ECS)
1. Set repository root to `backend/`.
2. Configure environment variables:
   - `DATABASE_URL`: Managed PostgreSQL connection string (e.g. Supabase, Render Postgres)
   - `SECRET_KEY`: High-entropy 64-character production key
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `.render.com`, `api.amrutam.yourdomain.com`
   - `CORS_ALLOWED_ORIGINS`: `https://amrutam.yourdomain.com`, `https://amrutam.vercel.app`
3. Build command:
   ```bash
   pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
   ```
4. Start command:
   ```bash
   gunicorn config.wsgi:application --workers 3 --bind 0.0.0.0:$PORT
   ```

### Frontend Deployment (Vercel / Netlify / Cloudflare Pages)
1. Set repository root to `frontend/`.
2. Configure build environment variables:
   - `VITE_API_BASE_URL`: Production backend URL (e.g. `https://amrutam-api.onrender.com/api/v1`)
3. Build command: `npm run build`
4. Output directory: `dist`
5. SPA fallback routing configured in `vite.config.js`.

---

## 10. Five-Minute Evaluator Demonstration
Please refer to [`docs/demo-script.md`](docs/demo-script.md) for the exact, timed five-minute evaluation walkthrough demonstrating:
1. Health and OpenAPI Swagger interactive documentation
2. Patient authentication and doctor discovery
3. Pessimistic slot booking with unique idempotency guarantee
4. Concurrency race condition rejection (409 Conflict)
5. Doctor workspace consultation lifecycle and prescription generation
6. Multi-tenant privacy verification
7. Admin Recharts analytics and forensic audit log inspection.

---

## 11. Authors & License
Developed for the **Amrutam Pharmaceuticals Pvt. Ltd. Full-Stack Backend Developer Assignment**.
Copyright &copy; 2026. All rights reserved.
