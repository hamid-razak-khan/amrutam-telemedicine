# Amrutam Telemedicine Platform: Security Verification Checklist

This security checklist documents the implemented security controls, their technical enforcement mechanisms, and outstanding production requirements in accordance with OWASP Top 10, clinical data protection standards, and assignment specifications.

---

## 1. Implemented Security Controls

| Domain | Security Control | Technical Implementation | Status |
| :--- | :--- | :--- | :--- |
| **Authentication** | Password Security | Django PBKDF2 with SHA-256 password hashing. Minimum length (8 chars), similarity, common password, and numeric validators enabled. | **IMPLEMENTED** |
| **Authentication** | Multi-Factor Authentication (MFA) | TOTP (RFC 6238) via `pyotp` with QR code generation, secret key setup, backup recovery codes (`MFARecoveryCode`), and login challenge verification (`MFAVerifyLoginView`). | **IMPLEMENTED** |
| **Authentication** | JWT Token Lifecycle | Short-lived Access Tokens (30 min) with Refresh Token rotation (7 days) and server-side blacklisting on logout via `rest_framework_simplejwt.token_blacklist`. | **IMPLEMENTED** |
| **Authentication** | Brute-Force Throttling | DRF Throttling: Anonymous requests throttled at 120/min, authenticated requests throttled at 600/min. | **IMPLEMENTED** |
| **Authorization** | Role-Based Access Control | Strict role separation (`PATIENT`, `DOCTOR`, `ADMIN`). Public registration strictly restricted to `PATIENT`. Privilege escalation attempts rejected. | **IMPLEMENTED** |
| **Authorization** | Doctor Licensing & Approval | Self-registered doctors are assigned `STATUS_PENDING`. Must be reviewed and approved by platform admin before practicing or creating slots. Removed doctors lose practice access immediately. | **IMPLEMENTED** |
| **Authorization** | Resource-Level Isolation | Patient A cannot retrieve Patient B's records or prescriptions; Doctor A cannot access Doctor B's consultations or slots. Verified via automated test suites. | **IMPLEMENTED** |
| **Integrity** | Double-Booking Prevention | Pessimistic locking (`select_for_update()`) combined with PostgreSQL partial unique constraints (`unique_active_consultation_per_slot`, `unique_active_doctor_appointment_time`). | **IMPLEMENTED** |
| **Integrity** | Idempotency Protection | SHA-256 payload hashing and client `Idempotency-Key` tracking preventing double-charging and duplicate bookings across network retries. | **IMPLEMENTED** |
| **Integrity** | 10-Minute Hold Reservation | Pending-payment reservations hold slots for 10 minutes; expired holds are dynamically released and cleaned up via `release_expired_reservations`. | **IMPLEMENTED** |
| **Auditability** | Append-Only Audit Trail | Application-level immutable `AuditLog` capturing actor, action, resource, IP, Request ID, and sanitized payload. Overridden `delete()` and `save()` reject tampering. | **IMPLEMENTED** |
| **Data Protection** | Sensitive Log Redaction | `JSONFormatter` and `sanitize_metadata` strip passwords, tokens, auth headers, and CVVs before writing to logs. | **IMPLEMENTED** |
| **Input Validation** | API Schema Enforcement | DRF Serializers and Zod schemas enforce type constraints, regex matching, fee bounds, and payload boundaries. | **IMPLEMENTED** |
| **Infrastructure** | Container Isolation | Backend Docker container runs under unprivileged non-root user `appuser:appgroup`. | **IMPLEMENTED** |
| **Transport** | Secure Headers | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `HSTS`, and configurable CORS origins. | **IMPLEMENTED** |
| **Tracing** | Distributed Tracing | `X-Request-ID` assigned or propagated across all API requests and captured in structured logs. | **IMPLEMENTED** |

---

## 2. Outstanding Production Requirements (Cloud Deployment)

| Requirement | Proposed Production Mitigation | Target Environment |
| :--- | :--- | :--- |
| **Database Encryption at Rest** | Enable AWS RDS KMS encryption (AES-256) for PostgreSQL tablespaces and automated snapshot volumes. | Managed Cloud (AWS/GCP/Supabase) |
| **Secrets Manager Integration** | Integrate AWS Secrets Manager or HashiCorp Vault for dynamic database credentials and JWT signing key rotation. | Production Kubernetes / ECS |
| **PostgreSQL Engine Triggers** | Implement database-level row-level security (RLS) triggers to reject `UPDATE` or `DELETE` on the `audit_auditlog` table by database superusers. | Managed PostgreSQL 16 |
| **WAF & DDoS Mitigation** | Configure Cloudflare / AWS WAF for Layer 7 DDoS mitigation and automated IP rate-limiting. | Production CDN / Edge |
| **Automated Vulnerability Scanning** | Enable GitHub Dependabot and Snyk in CI/CD pipeline for real-time package CVE detection. | GitHub Actions CI |
