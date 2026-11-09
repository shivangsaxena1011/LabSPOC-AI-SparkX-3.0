# LabSPOC AI — Phase 01 Full Codebase Audit

**Date:** 2026-11-09  
**Auditor:** Lead Software Architect, Security Engineer & QA Lead  
**Target Repository:** LabSPOC AI (Cumulative Phase 07)  
**Project:** Galgotias University — SPARKX 3.0 International 30-Day Innovation Challenge  
**Track:** Smart Campus & Digital Twin / AI-Powered Intelligent Lab SPOC  
**Institution:** Oriental Institute of Science & Technology (OIST), Bhopal  
**Target Laboratory:** AI & ML Laboratory  

---

## 1. Executive Summary

A comprehensive, line-by-line inspection, build verification, and runtime test of the Phase 07 codebase was performed. The repository establishes solid foundational intentions: it uses FastAPI and SQLAlchemy for the backend, Next.js 14 and React Three Fiber for the frontend, Google GenAI SDK for Gemini embeddings and generation, and incorporates access controls, audit logging, and hybrid RAG.

However, the codebase currently suffers from several critical defects, incomplete modules, frontend/backend contract disconnects, and build-breaking TypeScript errors that prevent it from being a production-ready, demonstrable platform.

### Summary of Initial Verification Results
- **Backend Tests:** 13/13 passed in isolated SQLite test harness using `.venv` (Python 3.12).
- **Frontend Dependencies (`npm install`):** Successfully installed 179 packages (with 2 deprecation/security warnings in transitive Three.js dependencies).
- **Frontend Production Build (`npm run build`):** **FAILED**. Type error in `apps/web/src/app/page.tsx:19` (`adminHeaders` union type incompatible with `HeadersInit`).
- **Phase 05 Authentication:** Partially implemented. HS256 JWT implementation is custom/homebrewed; `create_admin_user` and `set_user_status` lack Pydantic schemas; frontend admin token handling was disconnected from asset creation.
- **Phase 06 Hybrid RAG:** Implemented in backend with cosine semantic + lexical fallback. However, retrieval performs in-memory scanning of all document chunks and N+1 queries for chunk vectors. Multi-turn conversation history is not supported.
- **Phase 07 Spatial Digital Twin:** Backend `/api/spatial/scene` works, but frontend visitor experience (`/visit`) completely omits the 3D scene and spatial context. Interactive zone editing is absent from the UI.
- **Project Demonstrator & Registration:** Student and faculty project registration from the frontend is missing entirely; only admins could register via raw API calls.

---

## 2. Directory & Source Inventory

```
labspoc-ai/
├── .gitignore
├── LICENSE (MIT)
├── README.md (Comprehensive documentation, notes npm install timeout in Phase 07)
├── apps/
│   ├── api/
│   │   ├── .env.example
│   │   ├── pytest.ini
│   │   ├── requirements.txt
│   │   ├── requirements-dev.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py (Custom PBKDF2 + HS256 JWT, legacy X-Admin-Key)
│   │   │   ├── config.py (Pydantic BaseSettings)
│   │   │   ├── db.py (SQLAlchemy SessionLocal & engine)
│   │   │   ├── embeddings.py (Gemini embed_content + cosine similarity)
│   │   │   ├── llm.py (Gemini generate_content + evidence gate check)
│   │   │   ├── main.py (Single monolithic router with 25+ endpoints)
│   │   │   ├── models.py (SQLAlchemy 2.0 mapped models)
│   │   │   ├── retrieval.py (Hybrid semantic + lexical retriever)
│   │   │   └── schemas.py (Pydantic models)
│   │   └── tests/
│   │       └── test_api.py (13 unit/integration tests)
│   └── web/
│       ├── .env.local.example
│       ├── next.config.mjs
│       ├── package.json
│       ├── postcss.config.mjs
│       ├── tailwind.config.ts
│       ├── tsconfig.json
│       └── src/
│           ├── app/
│           │   ├── globals.css
│           │   ├── layout.tsx
│           │   ├── page.tsx (Monolithic operations workspace, 65 minified lines)
│           │   └── visit/
│           │       └── page.tsx (Monolithic visitor interface, 33 minified lines)
│           ├── components/
│           │   └── LabScene.tsx (Three.js / React Three Fiber floor-plan component)
│           ├── data/
│           │   └── lab-scene.ts (Fallback static zones)
│           └── lib/
│               └── api.ts (Generic fetch client)
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PHASE_02_RELEASE_NOTES.md
│   ├── PHASE_03_RELEASE_NOTES.md
│   ├── PHASE_04_RELEASE_NOTES.md
│   ├── PHASE_05_06_RELEASE_NOTES.md
│   ├── PHASE_07_RELEASE_NOTES.md
│   ├── SECURITY.md
│   ├── SPARKX_30_DAY_SUBMISSION_CHECKLIST.md
│   └── USER_MANUAL.md
└── infra/
    └── docker-compose.yml (PostgreSQL + API container)
```

---

## 3. Detailed Audit Findings by Subsystem

### 3.1 Frontend (`apps/web`)
1. **Build Failure (CRITICAL):**
   `apps/web/src/app/page.tsx:19` defines:
   ```typescript
   const adminHeaders = () => adminToken ? { "Authorization": `Bearer ${adminToken}` } : { "X-Admin-Key": adminKey };
   ```
   This TypeScript union type fails during `npm run build` because Next.js type-checking expects `HeadersInit` (`Record<string, string> | string[][] | Headers`), and TypeScript flags undefined property incompatibility.
2. **Missing 3D Scene in Visitor Experience (`/visit`):**
   The core competition track is *Smart Campus & Digital Twin*. In `/visit`, the visitor has no 3D canvas or spatial orientation. The visitor only sees a standard `<select>` dropdown with asset IDs.
3. **Broken / Inconsistent UI Actions:**
   - On the Operations page (`/`), the "Register asset" button has:
     `disabled={!adminKey || !assetId.trim() || !assetName.trim()}`
     When an administrator signs in with username/password (bearer token `adminToken`), `adminKey` remains empty, leaving the "Register asset" button permanently disabled!
   - In `Virtual Lab` view, selecting an asset renders raw JSON stringified in `<pre>` tags instead of an institutional equipment detail panel with status, specs, photos, SOP links, and verification dates.
   - There is no zone management UI to adjust coordinates, floor, or dimensions, even though the backend supports `PATCH /api/zones/{zone_id}/layout`.
   - Asset photo upload and viewing are completely missing from the UI despite backend model and endpoint support.
   - Project registration form is missing; visitors/students cannot submit projects.
4. **Code Quality and Maintainability:**
   Both `page.tsx` and `visit/page.tsx` are unformatted, dense single-line concatenations with minified state variables (`a, p, d, x, s, v`). This severely impedes maintainability, error tracing, and extensibility.

### 3.2 Backend (`apps/api`)
1. **Schema Validation Gaps:**
   - `POST /api/admin/users` accepts `payload: dict` rather than a validated Pydantic schema (`UserCreate`).
   - `PATCH /api/admin/users/{user_id}/status` accepts `payload: dict` rather than `UserStatusUpdate`.
   - `POST /api/assets` specifications field is stored as stringified JSON without schema validation.
2. **N+1 Retrieval and Scaling Issue:**
   `retrieval.py` executes:
   ```python
   rows = db.execute(select(DocumentChunk, Document).join(Document, ...)).all()
   for chunk, doc in rows:
       vector = db.get(ChunkVector, chunk.id)  # N+1 query in a loop!
   ```
   Loading all chunks into memory and querying the database for each chunk vector in a loop will cause high latency and memory exhaustion as documents grow.
3. **Conversational Multi-Turn Memory Omission:**
   `QueryRequest` accepts `session_id`, but `ask` in `main.py` never retrieves previous conversation turns or session dialogue history. Every question is evaluated in complete isolation.
4. **Project Demonstrator Restrictions:**
   `POST /api/projects` requires `require_admin`. Consequently, student and faculty innovators cannot submit projects for review. Project submission should be open or role-governed, while project *approval* (`POST /api/projects/{id}/approve`) must remain admin-only.
5. **Absence of Structured Logging & Request Validation Limits:**
   - Logging relies on unstructured standard output.
   - Missing rate limiting middleware to prevent brute-force attacks on `/api/auth/login` and `/api/assistant/query`.
   - Lack of standard API envelope/error formatting.

### 3.3 Security Audit
1. **Token Secret Enforcement:**
   `auth.py` raises HTTP 503 if `JWT_SECRET` is shorter than 32 characters, but falls back to `settings.admin_api_key`. If neither is configured with 32+ characters, auth fails. A clear default/fallback or guided configuration is needed.
2. **Missing Rate Limiting:**
   No rate limiting on authentication attempts (`/api/auth/login`) or LLM queries (`/api/assistant/query`), leaving the system open to credential stuffing and API key exhaustion.
3. **File Upload Security:**
   Document upload verifies file extensions and max size, and photo upload verifies magic bytes. However, uploads lack content disinfection, virus scanning, or SVG blocking (preventing XSS).
4. **Authorization Consistency:**
   Dependency types are inconsistently annotated (`_: bool = Depends(require_admin)` vs `actor: dict = Depends(require_admin)`).

---

## 4. Test Suite Baseline Execution

### Backend Pytest Results
Command: `.venv\Scripts\pytest -v`  
Status: **13 passed in 11.06s**  
- `test_health`: PASSED
- `test_unknown_question_abstains`: PASSED
- `test_admin_write_routes_fail_closed_without_key`: PASSED
- `test_admin_write_routes_reject_wrong_key`: PASSED
- `test_zone_inventory_requires_admin_and_persists`: PASSED
- `test_visitor_events_respect_analytics_consent`: PASSED
- `test_visitor_events_are_recorded_after_consent`: PASSED
- `test_visitor_event_allowlist_rejects_unknown_event`: PASSED
- `test_admin_login_and_bearer_authentication`: PASSED
- `test_knowledge_evaluation_requires_admin`: PASSED
- `test_viewer_role_cannot_use_protected_write_routes`: PASSED
- `test_spatial_scene_returns_explicit_illustrative_status`: PASSED
- `test_zone_layout_update_requires_admin_and_persists_coordinates`: PASSED

### Frontend Build Results
Command: `npm run build`  
Status: **FAILED (Exit code 1)**  
Error:
```
Type error: Type '{ Authorization: string; "X-Admin-Key"?: undefined; } | { "X-Admin-Key": string; Authorization?: undefined; }' is not assignable to type 'HeadersInit | undefined'.
```
Location: `apps/web/src/app/page.tsx:19`

---

## 5. Audit Recommendations & Remediation Plan
1. **Stabilize Core:** Fix the TypeScript typing error in `apps/web/src/app/page.tsx` and refactor monolithic pages into clean, modular, maintainable components.
2. **Complete Module 1 (3D Virtual Lab Guide):**
   - Bring `LabScene` into `/visit` so visitors experience the digital twin.
   - Add rich Equipment Detail Panels (specs, status, photos, manuals).
   - Add interactive Zone Layout Manager for administrators.
   - Add Asset Photo upload and gallery viewer.
3. **Complete Module 2 (Conversational Assistant):**
   - Implement multi-turn conversational context storage.
   - Support Hindi and English with intelligent voice handling.
   - Add Evidence Gate inspectability.
4. **Complete Module 3 (RAG Knowledge System):**
   - Implement eager vector pre-loading to eliminate N+1 database queries.
   - Add frontend Knowledge Document manager with approval/unapproval and chunk inspector.
   - Add offline Retrieval Evaluation UI (Recall@K and MRR).
5. **Complete Module 4 (Project Demonstrator):**
   - Add public student/faculty project registration form.
   - Admin approval queue with status badges.
   - Project detail modal with project-grounded Q&A.
6. **Complete Module 5 (Visitor Interaction & Analytics):**
   - Add FAQ clustering and analytics.
   - Add analytics export and detailed timeline reporting.
7. **Signature Innovations:**
   - Implement **Spatially Anchored Evidence Graph (SAEG)** relational endpoints (`/api/graph/...`).
   - Implement **Agenda-to-Tour Compiler** with persona-based relevance weighting and constraint satisfaction.
   - Implement verifiable **Evidence Gate** structure in every assistant response.
8. **Security & Production Hardening:**
   - Add rate limiting, structured logging, Pydantic request models, and clean migration support.
