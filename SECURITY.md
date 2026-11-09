# LabSPOC AI — Security Architecture & Governance Report (Release 0.7.1)

**Target System:** LabSPOC AI — Institutional Laboratory Intelligence Platform  
**Target Environment:** AI & ML Laboratory, Oriental Institute of Science & Technology (OIST), Bhopal  
**Evaluation Scope:** Release 0.7.1 Security Hardening & Threat Model Assessment  

---

## 1. Authentication & Identity Management

### PBKDF2-HMAC-SHA256 Password Storage
- Passwords are never stored in plaintext.
- Password hashing employs `PBKDF2-HMAC-SHA256` using:
  - 240,000 hash iterations.
  - Cryptographically secure 16-byte random salt generated per user via `os.urandom(16)`.
  - Constant-time comparison (`hmac.compare_digest`) to prevent timing attacks.

### JSON Web Token (JWT) Bearer Authentication
- Tokens are signed using the `HS256` algorithm with a minimum 256-bit secret key (`JWT_SECRET`).
- Token expiration is enforced (default 12 hours) via the `exp` claim.
- Token validation verifies signature, expiry, and queries the database on every authenticated request to guarantee that the account remains `is_active` and possesses the requisite role.

### Role-Based Access Control (RBAC) Matrix

| Endpoint Group | `admin` | `editor` | `viewer` | Public Visitor |
| :--- | :---: | :---: | :---: | :---: |
| **Zone Management (`POST`, `PUT`, `DELETE`)** | Allowed | Denied | Denied | Denied |
| **User Administration & Audit Logs** | Allowed | Denied | Denied | Denied |
| **Equipment Hotspots & Specifications** | Allowed | Allowed | Denied | Read-Only |
| **Document Upload & Approval** | Allowed | Allowed | Denied | Denied |
| **Project Submission Approval** | Allowed | Allowed | Denied | Denied |
| **Public Project Submission** | Allowed | Allowed | Allowed | Rate-Limited |
| **Conversational Queries & 3D Explorer** | Allowed | Allowed | Allowed | Allowed |

---

## 2. Network, Headers & Middlewares

### Security Headers Middleware
All HTTP responses from the FastAPI backend enforce defensive security headers:
- `X-Content-Type-Options: nosniff` (mitigates MIME-sniffing exploits).
- `X-Frame-Options: SAMEORIGIN` (prevents clickjacking attacks).
- `X-XSS-Protection: 1; mode=block` (activates browser XSS filters).
- `Referrer-Policy: strict-origin-when-cross-origin` (prevents referrer leakages).

### Reverse-Proxy Aware Rate Limiting
- Employs a sliding-window in-memory rate limiter per IP address.
- Correctly inspects `X-Forwarded-For` and `X-Real-IP` request headers when deployed behind reverse proxies (Nginx, Traefik, AWS ALB) with fallback to direct client socket IP.
- Default limit: 120 requests per minute for general routes; 60 requests per minute for public project submissions. Exceeding limits returns `HTTP 429 Too Many Requests`.

### Cross-Origin Resource Sharing (CORS)
- CORS origins are strictly configurable via the `CORS_ORIGINS` environment variable (defaults to `http://localhost:3000`).
- Wildcard `*` origins are disabled by default.

---

## 3. Input Validation & Abuse Protection

### Public Project Submission Sanitization
- Public project submissions undergo strict regex-based HTML/script tag stripping:
  ```python
  clean_title = re.sub(r'<[^>]*>', '', title).strip()
  ```
- All submissions are quarantined with initial status `pending_review` and require administrative approval before publication or inclusion in RAG evidence.

### Document and File Upload Protection
- **Extension Whitelist:** Only `.pdf`, `.docx`, `.txt`, and `.md` are permitted for knowledge ingestion.
- **Magic-Byte Sniffing:** Physical equipment photo uploads require binary header inspection (`verify_file_magic`) validating PNG (`89 50 4E 47`), JPEG (`FF D8 FF`), and WebP signatures.
- **Payload Size Limits:** Uploads exceeding `MAX_UPLOAD_SIZE_MB` (default 25 MB) are rejected before memory allocation.
- **Path Traversal Mitigation:** Uploaded filenames are sanitized and assigned random UUID keys in storage, preventing path traversal attacks.

### SQL Injection Prevention
- 100% of database interactions are authored via SQLAlchemy 2.0 ORM models and parameterized core expressions (`select(...)`, `execute(...)`).
- Raw string formatting inside SQL statements is strictly prohibited.

---

## 4. AI & Retrieval Safeguards (Evidence Gate)

### Strict Document Governance
- Documents uploaded by editors remain `pending_review` until formally approved by an administrator.
- Unapproved documents are strictly excluded from embedding generation, hybrid search, and LLM context.

### Citation Verification & Hallucination Prevention
- The Google Gemini prompt is strictly constrained to approved retrieved snippets with temperature 0.1.
- Gemini is mandated to format evidence strictly as numeric brackets: `[1]`, `[2]`.
- The **Evidence Gate** intercepts the generated response before transmission:
  - If citation numbers exceed the count of supplied chunks, the response is rejected.
  - If the model makes factual claims without citations or abstention phrasing, the response is rejected.
  - When evidence is insufficient, the system abstains honestly with verified fallback messaging.

---

## 5. Visitor Privacy & Data Retention

- **Opt-In Analytics Consent:** Visitors choose whether to allow analytics tracking during onboarding. When consent is denied (`consent: false`), no event records or question logs are persisted.
- **No PII Collection:** Visitor sessions are identified by transient client tokens; no personal identification, email addresses, or biometric data are gathered.
- **Session Summaries:** Visitors can export a transparent local summary of their session history and interactions.
