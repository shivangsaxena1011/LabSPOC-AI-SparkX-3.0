# LabSPOC AI — Spatially Grounded Virtual Lab Ambassador

**Competition:** Galgotias University — SPARKX 3.0 International, 30-Day Innovation Challenge  
**Track:** Smart Campus & Digital Twin / AI-Powered Intelligent Lab SPOC  
**Institution:** Oriental Institute of Science & Technology (OIST), Bhopal  
**Target Laboratory Profile:** AI & ML Laboratory  
**Preferred AI Provider:** Google Gemini (`gemini-2.5-flash`, `gemini-embedding-001`)  
**Architecture:** Python FastAPI Backend, Next.js 14, React 18, TypeScript, Tailwind CSS, Three.js / React Three Fiber  
**Release:** 0.7.0 — Production Stabilization & Feature Integration  

---

## Executive Overview

**LabSPOC AI** is an institutional laboratory intelligence platform and digital twin ambassador designed specifically for the AI & ML Laboratory at Oriental Institute of Science & Technology (OIST), Bhopal. Unlike standard conversational bots or static web showcases, LabSPOC AI enforces **strict evidence-first grounding**:
1. It navigates a database-backed **3D digital twin** of laboratory zones and equipment hotspots.
2. It generates **verifiably grounded responses** using Google Gemini constrained strictly to approved laboratory manuals, SOPs, and technical records.
3. It passes every AI response through an **Evidence Gate** that detects insufficient evidence and abstains honestly rather than inventing specifications.
4. It compiles **time-boxed visitor tour itineraries** (2, 5, or 15 minutes) customized to visitor personas and interest objectives.
5. It hosts an **AI Project Demonstrator** with student/faculty registration and administrative review workflows.
6. It tracks **consent-aware visitor analytics** and clusters frequently asked question topics.

---

## Core Challenge Modules

### Module 1: AI Virtual Lab Guide
- **Interactive 3D Digital Twin:** Rendered with Three.js / React Three Fiber, featuring orbit controls, dynamic lighting, zone platforms, and interactive equipment hotspots.
- **Configurable Laboratory Zones:** Persistent coordinates (`x`, `z`, `width`, `depth`) with an in-app administrator geometry editor and audit logging.
- **Database-Backed Equipment Hotspots:** Click-to-inspect hotspots with technical specs, manufacturer details, model numbers, and verification status badges.
- **Visual Evidence & Photo Support:** Dedicated photo upload and gallery viewer for physical equipment verification.
- **Honest Prototype Boundary:** Room geometry is explicitly labeled as *illustrative* pending an on-site photogrammetric survey.

### Module 2: Conversational Lab Assistant
- **Gemini-Powered Dialogue:** Multi-turn conversational interface powered by Google Gemini with temperature control (0.1) for rigorous factual grounding.
- **Browser-Supported Voice:** Web Speech API recognition (Speech-to-Text) and speech synthesis (Text-to-Speech) supporting English and Hindi (हिन्दी).
- **Multi-Turn Context:** Full dialogue session memory stored in `conversation_turns` table to maintain context across turns.
- **Honest Abstention:** Explicit abstention when approved institutional evidence is insufficient.

### Module 3: RAG-Based Lab Knowledge System
- **Multi-Format Ingestion:** Ingests PDF (via `pypdf`), DOCX (via `python-docx`), TXT, and Markdown files with SHA-256 deduplication and max upload limits.
- **Document Governance:** Strict two-step lifecycle (`pending_review` → `approved`). Only approved documents are eligible for vector embedding and retrieval.
- **Optimized Hybrid Retrieval:** Joint semantic cosine search (`gemini-embedding-001`) + lexical term overlap with single-query eager fetching (eliminating N+1 database queries).
- **Offline Retrieval Evaluation:** Built-in benchmarking harness computing **Recall@K** and **Mean Reciprocal Rank (MRR)**.

### Module 4: AI Project Demonstrator
- **Student & Faculty Project Registration:** Public submission portal (`POST /api/projects/submit`) for students and faculty innovators.
- **Administrative Approval Queue:** Administrator review workflow (`POST /api/projects/{id}/approve`) to publish verified innovations.
- **Project Showcase:** Highlights problem statement, methodology, technology stack, societal impact, and live demonstration links.

### Module 5: Visitor Interaction & Analytics
- **Visitor Onboarding:** Persona selection (Undergraduate, Academic visitor, Industry executive, Research scientist, Accreditation reviewer), visit objectives, and time limits (2, 5, 15 min).
- **Consent-Aware Analytics:** Strict opt-in privacy mechanism; interaction events are recorded only with explicit visitor consent.
- **FAQ Topic Clustering:** Aggregates and clusters frequently asked question topics and hotspot targets.
- **Visit Summary:** One-click session report generation with copyable text and event timeline.

---

## Signature Innovations

### A. Spatially Anchored Evidence Graph (SAEG)
Persistent relational graph linking:
```
Zone (Spatial Coordinates) ──contains──> Equipment Asset (Persistent ID)
                                          ├──supported_by──> Document (Manual / SOP / Spec Sheet)
                                          └──demonstrated_in─> Approved Project
```
Exposed via dedicated `/api/graph/overview` and `/api/graph/links` endpoints.

### B. Agenda-to-Tour Compiler
Intelligent route solver that compiles a custom itinerary based on:
- Visitor Persona (affinity weighting for students, researchers, or executives).
- Available Time Budget (strict 2-min, 5-min, or 15-min allocation).
- Verified Equipment and Approved Projects only.

### C. Evidence Gate
Automated verification pipeline that inspects every AI response before display:
- Validates citation bracket indices `[1]`, `[2]` against the exact range of retrieved evidence.
- Detects factual assertions made without evidence and forces fallback or abstention.
- Exposes structured gate metadata (`verified_grounding`, `abstention_triggered`, `citations_validated`) in the API response.

---

## Security Architecture

1. **Authentication:** PBKDF2-HMAC-SHA256 password hashing (240,000 rounds) with individual hex salts and HS256 JWT bearer tokens.
2. **Role-Based Authorization:** Strict `admin`, `editor`, and `viewer` hierarchy on all management endpoints.
3. **Rate Limiting:** Sliding-window rate limiter protecting authentication and query endpoints against brute-force attacks.
4. **File Validation:** Magic-byte sniffing for image uploads and strict extension whitelisting (.pdf, .docx, .txt, .md) with size limits.
5. **No Secret Exposure:** Administrative credentials and Gemini API keys are strictly server-side and never exposed to client code.
6. **Additive Database Migrations:** Idempotent migration runner (`run_additive_migrations`) updates existing SQLite/PostgreSQL schemas without data loss.

---

## Repository Documentation Index

- [`CODEBASE_AUDIT.md`](file:///C:/Users/Project/LabSPOC%20AI%20SparkX%203.0/CODEBASE_AUDIT.md): Comprehensive Phase 01 codebase audit and verification report.
- [`IMPLEMENTATION_STATUS.md`](file:///C:/Users/Project/LabSPOC%20AI%20SparkX%203.0/IMPLEMENTATION_STATUS.md): Challenge modules & signature innovations status matrix.
- [`TECHNICAL_DEBT.md`](file:///C:/Users/Project/LabSPOC%20AI%20SparkX%203.0/TECHNICAL_DEBT.md): Technical debt assessment and remediation log.
- [`docs/ARCHITECTURE.md`](file:///C:/Users/Project/LabSPOC%20AI%20SparkX%203.0/labspoc-ai/docs/ARCHITECTURE.md): Architectural decisions and data models.
- [`docs/SECURITY.md`](file:///C:/Users/Project/LabSPOC%20AI%20SparkX%203.0/labspoc-ai/docs/SECURITY.md): Security analysis and governance notes.
- [`docs/USER_MANUAL.md`](file:///C:/Users/Project/LabSPOC%20AI%20SparkX%203.0/labspoc-ai/docs/USER_MANUAL.md): Institutional user manual for visitors and lab administrators.

---

## Repository Structure

```
.
├── CODEBASE_AUDIT.md            # Comprehensive Phase 01 codebase audit
├── IMPLEMENTATION_STATUS.md     # Module and innovation delivery status
├── TECHNICAL_DEBT.md            # Technical debt identification & resolutions
├── README.md                    # Project documentation
├── apps/
│   ├── api/                     # Python FastAPI backend
│   │   ├── app/
│   │   │   ├── auth.py          # HS256 JWT & PBKDF2 authentication
│   │   │   ├── config.py        # Settings & environment variables
│   │   │   ├── db.py            # Database session & engine
│   │   │   ├── embeddings.py    # Gemini embeddings & cosine similarity
│   │   │   ├── llm.py           # Grounded answer generation & Evidence Gate
│   │   │   ├── main.py          # FastAPI application & router endpoints
│   │   │   ├── models.py        # SQLAlchemy relational models
│   │   │   ├── retrieval.py     # Eager-joined hybrid semantic/lexical retriever
│   │   │   └── schemas.py       # Pydantic request & response models
│   │   └── tests/
│   │       └── test_api.py      # Automated pytest suite (19 test cases)
│   └── web/                     # Next.js 14 frontend
│       └── src/
│           ├── app/
│           │   ├── page.tsx     # Operations & administration workspace
│           │   └── visit/
│           │       └── page.tsx # Visitor experience portal
│           ├── components/
│           │   └── LabScene.tsx # 3D Three.js / React Three Fiber floor plan
│           └── lib/
│               └── api.ts       # Type-safe API client
└── docs/                        # Architecture, user manual & release notes
```

---

## License
MIT License — See `LICENSE`.
