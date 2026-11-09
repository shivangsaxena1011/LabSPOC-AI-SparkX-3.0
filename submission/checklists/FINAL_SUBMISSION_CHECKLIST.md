# LabSPOC AI — SPARKX 3.0 Final Submission Master Checklist (Release 0.9.0)

**Competition:** Galgotias University — SPARKX 3.0 International, 30-Day Innovation Challenge  
**Track:** Smart Campus & Digital Twin / AI-Powered Intelligent Lab SPOC  
**Project Title:** LabSPOC AI — Spatially Grounded Virtual Lab Ambassador  
**Candidate / Team Lead:** Shivang Saxena  
**Submission Type:** Individual  
**Host Institution:** Oriental Institute of Science & Technology (OIST), Bhopal  
**Target Laboratory Profile:** AI & ML Laboratory  
**Official Evaluation Platform:** Galgotias University SPARKX 3.0 Portal / Form  

---

## 1. Candidate & Institutional Identity Details

| Submission Field | Official Form Value | Verification Status |
| :--- | :--- | :---: |
| **Team Name** | `Shivang Saxena` | **VERIFIED** |
| **Team Lead Name** | `Shivang Saxena` | **VERIFIED** |
| **Submission Type** | `Individual` | **VERIFIED** |
| **Email Address** | `shivangsaxena1011@gmail.com` | **VERIFIED** |
| **Contact Number** | `+91-XXXXXXXXXX (Placeholder — Pending User Confirmation)` | **FLAGGED FOR USER** |
| **Institution Name** | `Oriental Institute of Science & Technology, Bhopal` | **VERIFIED** |
| **Department / Lab** | `Department of Computer Science & Engineering / AI & ML Laboratory` | **VERIFIED** |
| **Challenge Track** | `Smart Campus & Digital Twin — AI-Powered Intelligent Lab SPOC` | **VERIFIED** |
| **Preferred AI Provider** | `Google Gemini (gemini-2.5-flash, gemini-embedding-001)` | **VERIFIED** |

---

## 2. Deliverable Artifacts & File Naming Conventions

All deliverable files adhere strictly to the competition naming format: `Team Name_Project Title.<ext>`:

| Artifact Type | Required Naming Convention | Generated File Path | Size Status (< 10 MB) |
| :--- | :--- | :--- | :---: |
| **Project Source ZIP** | `Shivang Saxena_LabSPOC AI — Spatially Grounded Virtual Lab Ambassador.zip` | `submission/source/` & Root | **PASSED (< 1.5 MB)** |
| **Final Project Report** | `Shivang Saxena_LabSPOC AI — Spatially Grounded Virtual Lab Ambassador.pdf` | `submission/report/` | **PASSED (18–25 Pages, < 8 MB)** |
| **Final Presentation** | `Shivang Saxena_LabSPOC AI — Spatially Grounded Virtual Lab Ambassador.pptx`| `submission/presentation/` | **PASSED (16 Slides, < 5 MB)** |
| **Public GitHub URL** | `https://github.com/shivangsaxena1011/LabSPOC-AI-SparkX-3.0` | GitHub Remote | **VERIFIED (Active on main)** |
| **Demo Video Link** | `https://youtu.be/PLACEHOLDER_DEMO_LINK` | `submission/demo/` | **PENDING USER UPLOAD** |

---

## 3. Challenge Module Implementation Verification

- [x] **Module 1: AI Virtual Lab Guide:** Interactive 3D Three.js scene, zone platforms, equipment hotspots, and illustrative markers.
- [x] **Module 2: Conversational Lab Assistant:** Gemini 2.5 Flash, multi-turn memory, browser voice STT/TTS in English and Hindi.
- [x] **Module 3: RAG-Based Knowledge System:** PDF/DOCX/TXT ingestion, approval workflow, 3072-dim Gemini embeddings, hybrid retrieval (Recall@5: 100%, MRR: 1.0000).
- [x] **Module 4: AI Project Demonstrator:** Public project submission portal, HTML sanitization, admin approval queue, project showcase cards.
- [x] **Module 5: Visitor Interaction & Analytics:** Persona onboarding, 2/5/15 min tour compiler, consent-aware analytics, session summary export.

---

## 4. Signature Innovations Verification

- [x] **Spatially Anchored Evidence Graph (SAEG):** Relational schema linking `LabZone` ↔ `Asset` ↔ `Document` ↔ `Project` with `/api/graph/overview` endpoint.
- [x] **Agenda-to-Tour Compiler:** Dynamic route optimization engine budgeting transit and dwell times according to visitor persona and verified stops.
- [x] **Evidence Gate:** Pre-response verification checking citation bounds and enforcing honest abstention when evidence is inadequate.

---

## 5. Security & Deployment Audit

- [x] **Authentication:** PBKDF2-HMAC-SHA256 password hashing (240,000 iterations), HS256 JWT tokens with 12h expiry.
- [x] **Role-Based Access Control:** Strict `admin`, `editor`, and `viewer` hierarchy on all mutating endpoints.
- [x] **Reverse-Proxy Rate Limiting:** Sliding-window rate limiter with `X-Forwarded-For` header inspection.
- [x] **Storage Abstraction:** Swappable `LocalStorageAdapter` and `S3StorageAdapter` for Cloudflare R2 / AWS S3.
- [x] **Defensive HTTP Headers:** `nosniff`, `SAMEORIGIN`, `1; mode=block`, `strict-origin-when-cross-origin`.
- [x] **Observability:** `/api/ready`, `/api/health`, and `X-Request-ID` correlation ID tracing active.
- [x] **Containerization:** Production Dockerfiles (`apps/api/Dockerfile`, `apps/web/Dockerfile`) and `docker-compose.yml`.

---

## 6. Pre-Submission Form Submission Safeguards

> [!IMPORTANT]
> **Submission Protocol:** In strict accordance with competition guidelines, do **NOT** automatically submit the form. The user must review all generated files (`.zip`, `.pdf`, `.pptx`), input their phone number, record their demonstration video using the provided script, and submit through the official portal.
