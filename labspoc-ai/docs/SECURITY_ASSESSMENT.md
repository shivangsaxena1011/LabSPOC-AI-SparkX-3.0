# LabSPOC AI — Production Security & Governance Assessment (Release 0.8.0)

**Target System:** LabSPOC AI — Spatially Grounded Virtual Lab Ambassador  
**Evaluation Scope:** Release 0.8.0 Production Deployment & Threat Model Assessment  
**Target Environment:** AI & ML Laboratory, Oriental Institute of Science & Technology (OIST), Bhopal  
**Lead Security Engineer:** Lead Software Architect & Security Lead  
**Classification:** Institutional Technical Evaluation  

---

## 1. Executive Summary

This security assessment provides a systematic audit of the security posture, threat model, access control boundaries, cryptographic mechanisms, data privacy controls, and vulnerability surface of LabSPOC AI in its production configuration.

| Security Area | Implementation Status | Assessment Outcome |
| :--- | :--- | :--- |
| **Password Storage** | PBKDF2-HMAC-SHA256 (240,000 rounds, 16-byte random salt) | **STRONG (NIST SP 800-63B Compliant)** |
| **Session Authentication** | HS256 JWT tokens with 12-hour expiration & DB identity checks | **VERIFIED** |
| **Role-Based Authorization** | Three-tier hierarchy (`admin`, `editor`, `viewer`) on all endpoints | **VERIFIED** |
| **API Denial of Service Protection** | Sliding-window rate limiter with reverse-proxy header inspection | **HARDENED** |
| **Injection Mitigations** | 100% SQLAlchemy 2.0 ORM parameterized statements (No raw SQL) | **SAFE** |
| **Input Sanitization** | Regex HTML/script tag stripping on public project submissions | **HARDENED** |
| **File Upload Validation** | Magic binary signature sniffing (PNG, JPEG, WebP) + 25MB ceiling | **HARDENED** |
| **Path Traversal Protection** | StorageAdapter path canonicalization & boundary verification | **HARDENED** |
| **Defensive HTTP Headers** | `nosniff`, `SAMEORIGIN`, `1; mode=block`, `strict-origin-when-cross-origin` | **ACTIVE** |
| **AI Hallucination Guardrails** | Evidence Gate citation verification & honest abstention | **ACTIVE & BENCHMARKED** |
| **Visitor Privacy** | Strict opt-in consent gating; pseudonymized session UUIDs; DPDP Act 2023 alignment; zero direct PII required | **PRIVACY BY DESIGN** |

---

## 2. STRIDE Threat Model & Mitigations

### 2.1 Spoofing Identity
- **Threat:** Malicious actors attempt to forge JWT administrator tokens or guess weak administrator credentials.
- **Defenses Implemented:**
  - `_get_signing_secret()` requires a minimum 256-bit (32 character) secret.
  - Startup sanity check detects default/weak JWT secrets or default passwords in production.
  - Constant-time password verification (`hmac.compare_digest`) prevents timing side-channel attacks.
  - Database queries active status and role on every request; deactivated accounts are immediately locked out.

### 2.2 Tampering with Data
- **Threat:** Unauthorized modification of 3D zone coordinates, equipment hotspots, or laboratory standard operating procedures.
- **Defenses Implemented:**
  - All mutating endpoints (`POST`, `PUT`, `DELETE`) require `require_admin` or `require_superadmin`.
  - Immutable audit logs record `(actor, action, resource_type, resource_id, timestamp)` on every mutation.
  - Document files are indexed with SHA-256 digests; duplicate payloads are rejected or returned idempotently.
  - SQLite foreign key cascades enforced via `PRAGMA foreign_keys=ON`.

### 2.3 Repudiation
- **Threat:** Administrators deny executing destructive operations (e.g., deleting approved research manuals or de-verifying equipment).
- **Defenses Implemented:**
  - Centralized `AuditLog` table stores every administrative action with actor identity, action name, resource ID, and ISO 8601 UTC timestamp.
  - Audit logs are append-only; no API endpoint permits deleting or updating audit logs.

### 2.4 Information Disclosure
- **Threat:** Leakage of Google Gemini API keys, administrative database credentials, or unapproved internal drafts to public visitors.
- **Defenses Implemented:**
  - Sensitive environment variables (`GEMINI_API_KEY`, `JWT_SECRET`, `ADMIN_PASSWORD`) are server-side only; never bundled into Next.js client bundles.
  - Public config endpoint `/api/config/public` returns only institutional metadata (lab name, language codes, model identifier).
  - Unapproved documents (`status != 'approved'`) are strictly excluded from RAG retrieval and vector search.

### 2.5 Denial of Service (DoS) & Rate Limiting Hardening
- **Threat:** High-frequency API calls exhausting Google Gemini API quotas, header spoofing via untrusted proxy headers, or crashing backend database connection pools.
- **Defenses Implemented:**
  - Sliding-window rate limiting (120 req/min for general endpoints; 60 req/min for public submissions; 20 req/min for login attempts).
  - **Spoof-Resistant Proxy Verification:** `get_client_ip()` strictly validates the direct connection peer against a configured trusted proxy set (`127.0.0.1`, `::1`, `localhost`). Forwarded headers (`X-Forwarded-For`, `X-Real-IP`) are rejected when arriving from untrusted external clients, preventing client header spoofing.
  - **Single-Node vs Multi-Node Scope:** The current in-memory sliding window provides zero-latency protection per application process. For multi-replica clustered deployments, horizontal synchronization is documented via a shared Redis token-bucket architecture.
  - File upload ceiling capped at 25 MB (`max_upload_mb`).

### 2.6 Elevation of Privilege
- **Threat:** A user with role `viewer` attempts to call document approval or zone layout modification routes.
- **Defenses Implemented:**
  - `require_admin` dependency checks `payload.get("role") in {"admin", "editor"}`.
  - Superadmin operations (user creation, password reset) require `role == "admin"`.
  - Viewers attempting write operations receive `HTTP 403 Forbidden` (verified in `test_viewer_role_cannot_use_protected_write_routes`).

---

## 3. Cryptographic and Secrets Governance

1. **Password Storage Standards:**
   - Algorithm: `PBKDF2-HMAC-SHA256`
   - Iterations: 240,000 rounds
   - Salt: 16 cryptographically random bytes generated via `secrets.token_hex(16)`
   - Comparison: Constant-time `hmac.compare_digest`
2. **Session Token Standards:**
   - Algorithm: `HS256` (HMAC with SHA-256)
   - Expiration: Configurable via `access_token_minutes` (default 120 minutes)
   - Claim Payload: `{"sub": user_id, "username": username, "role": role, "iat": now, "exp": now + ttl}`
3. **Secret Rotation Playbook:**
   - Rotating `JWT_SECRET`: Invalidate all active user sessions by updating `JWT_SECRET`. Legitimate users re-authenticate at `/api/auth/login`.
   - Rotating `GEMINI_API_KEY`: Update `GEMINI_API_KEY` in environment; restart backend container; verify with `/api/ready`.

---

## 4. Object Storage & File Security

1. **Path Traversal Mitigation:**
   - `LocalStorageAdapter` inspects target paths with `os.path.resolve()` and asserts that the canonical path begins with the base storage directory.
   - Any attempt to escape the directory (e.g. `../etc/passwd`) raises an explicit `ValueError: Path traversal detected` (verified in `test_local_storage_adapter`).
2. **Binary Signature Verification:**
   - Image uploads require magic byte inspection:
     - JPEG: `FF D8 FF`
     - PNG: `89 50 4E 47 0D 0A 1A 0A`
     - WebP: `RIFF` header + `WEBP` magic chunk at byte offset 8–11
3. **MIME Whitelisting:**
   - Document knowledge uploads permit only `.pdf`, `.docx`, `.txt`, and `.md`. Executables, shell scripts, and HTML files are rejected with `HTTP 415 Unsupported Media Type`.

---

## 5. Visitor Privacy, Data-Flow Governance & Retention Policy

- **No Direct Personal Identifiers Required or Solicited:** The platform does not require user registration for visitors, and does not solicit, require, or store personal identifiers such as full names, phone numbers, email addresses, student IDs, or biometric profiles in any structured data schema.
- **Pseudonymization under Ephemeral Session UUIDs:** All interactive visitor state (selected persona, declared agenda, conversation history, and telemetry) is tied exclusively to a randomly generated, unlinked UUID (`session_id`).
- **Strict Opt-In Telemetry (DPDP Act 2023 Conformance):** Telemetry tracking (e.g. `zone_view`, `hotspot_select`, `tour_started`) is strictly conditional on explicit visitor consent at onboarding. If the visitor selects non-consent, telemetry events are dropped in memory without disk persistence.
- **Visitor-Supplied Free-Text Handling:** Visitor agendas and conversational questions are processed in memory for retrieval and contextual answering, stored only under the ephemeral session identifier to enable the departure session review, and never shared with third-party tracking networks.
- **Departure Transparency:** Visitors can inspect and copy their complete session interactions and verified citations prior to departure via the `/visit` Session Summary view.
- **Rate-Limiter Privacy & Proxy Protection:** IP addresses used by the in-memory rate-limiter sliding window are stored ephemerally in RAM and evicted after 60 seconds; trusted reverse proxies are strictly validated to prevent IP spoofing or untrusted header injection.
- **Audit Log Immutability:** Administrative changes (asset updates, document uploads, approvals) are permanently recorded in `audit_logs` with timestamps, actor usernames, and actions for institutional governance.
