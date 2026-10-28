# Amrutam Telemedicine Platform: Threat Model & STRIDE Security Analysis

## 1. Scope & Primary Assets
The platform handles highly sensitive clinical and financial interactions. Key assets requiring strict confidentiality, integrity, and availability include:
- **Electronic Health Records (EHR)**: Chief complaints, clinical notes, and Ayurvedic diagnoses.
- **Medical Prescriptions**: Structured medication formulations, dosages, and dietary recommendations.
- **Personally Identifiable Information (PII)**: Patient full names, contact numbers, email addresses, blood groups, and emergency contacts.
- **Financial Transactions**: Payment statuses, provider transaction IDs, and idempotency tracking keys.
- **Authentication & Session Tokens**: Passwords hashes (PBKDF2-SHA256), JWT access tokens, and refresh session states.
- **System Audit Trail**: Append-only logs recording clinical actions, logins, and permission rejections.

---

## 2. Trust Boundaries & Attack Surfaces
- **Untrusted Zone**: Public Internet, web browsers, public API callers.
- **Demilitarized Zone (DMZ)**: Reverse proxy / load balancer terminating TLS 1.3.
- **Application Boundary**: Django REST Framework API running authenticated middleware, RBAC checks, and rate limiters.
- **Secure Persistence Boundary**: Private network hosting PostgreSQL 16 and Redis 7, inaccessible from the public internet.

---

## 3. Threat Actors
1. **Malicious Public Actors**: Automated bots, credential-stuffing crawlers, and scrapers attempting denial-of-service or privilege escalation.
2. **Untrusted Patients**: Malicious or inquisitive patients attempting to enumerate other patients' bookings, medical histories, or prescriptions.
3. **Compromised Doctors**: Rogue practitioners attempting to view patient consultations assigned to other doctors or modify unauthorized availability slots.
4. **Internal Staff / Operators**: Operators attempting to view or tamper with immutable audit logs or bypass billing transactions.

---

## 4. STRIDE Threat Analysis & Mitigations

| Category | Threat Scenario | Impact | Implemented Mitigation |
| :--- | :--- | :--- | :--- |
| **Spoofing** | Public user attempts to register with role `ADMIN` or `DOCTOR`. | Privilege escalation, administrative compromise. | Strict registration serialization: `UserRegisterSerializer` hardcodes `role=PATIENT`. Public input parameters cannot alter account role. |
| **Spoofing** | Replay of stolen JWT access or refresh token after user logout. | Unauthorized session takeover. | Token rotation and server-side blacklisting (`rest_framework_simplejwt.token_blacklist`). Blacklisted tokens are rejected with HTTP 401. |
| **Tampering** | Competing patients send concurrent booking requests for the same slot. | Double-booking race condition, clinical conflict. | Database row locking (`select_for_update()`) inside `transaction.atomic()`. Only the first transaction commits; competing requests receive HTTP 409 Conflict. |
| **Tampering** | Altering audit logs to cover unauthorized clinical actions. | Loss of forensic integrity. | Append-only model integrity: `AuditLog.save()` and `AuditLog.delete()` explicitly raise exceptions if record is modified or deleted. |
| **Repudiation** | Doctor denies issuing an erroneous prescription. | Legal liability and clinical dispute. | Prescriptions permanently capture `doctor_id`, `consultation_id`, and `created_at`. An immutable `PRESCRIPTION_CREATED` audit event is recorded. |
| **Information Disclosure** | Patient A attempts to retrieve Patient B's prescription or booking. | Severe HIPAA / DISHA medical data privacy breach. | Resource-level permission check: `ConsultationDetailView` and `PrescriptionDetailView` verify `obj.patient == request.user`. Returns 403 Forbidden. |
| **Information Disclosure** | Sensitive passwords or JWT tokens written to server log files. | Credential exposure to log aggregation operators. | Custom `JSONFormatter` and `sanitize_metadata` redact any dictionary keys containing `password`, `token`, `secret`, `authorization`, or `cvv`. |
| **Denial of Service** | Volumetric brute-force login attempts or endpoint flooding. | Exhaustion of server CPU and database connections. | DRF throttling configured: Anonymous rate `120/min`, Authenticated rate `600/min`. Password validators enforce minimum length and complexity. |
| **Elevation of Privilege** | Normal patient invokes doctor endpoints (e.g. `/doctors/me/availability`). | Unauthorized doctor schedule manipulation. | Custom permission classes (`IsDoctor`, `IsAdminUserRole`) strictly enforced at the view class level. Verified in automated security test suite. |

---

## 5. Idempotency & Payment Replay Analysis
- **Problem**: Network timeouts during booking or payment initiation can cause client retries, potentially double-charging patients or creating ghost bookings.
- **Mitigation**:
  1. All booking creations require the `Idempotency-Key` HTTP header.
  2. The server computes a SHA-256 fingerprint of the request body.
  3. If a retry arrives with the **same key and payload**, the server returns the cached completed booking response without creating duplicates.
  4. If a retry arrives with the **same key but a different payload**, the server immediately rejects the request with HTTP 422 Unprocessable Entity.

---

## 6. Residual Risks & Outstanding Production Roadmap
1. **Hardware Security Keys (WebAuthn / FIDO2)**: While software-based TOTP (RFC 6238) MFA is fully implemented, hardware FIDO2 keys (e.g. YubiKey) can be added for high-security administrator accounts.
2. **Database Encryption at Rest**: Enable AWS KMS or LUKS volume-level disk encryption for PostgreSQL persistent volumes.
3. **Database Audit Triggers**: Add PostgreSQL engine-level triggers to enforce append-only audit log rules at the storage engine level in addition to application-level checks.
