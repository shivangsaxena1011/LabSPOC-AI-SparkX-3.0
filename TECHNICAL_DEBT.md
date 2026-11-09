# LabSPOC AI — Technical Debt & Architectural Assessment

**Assessment Date:** 2026-11-09  
**System:** LabSPOC AI v0.7.0  

---

## 1. High Priority Code Issues (Immediate Remediation Required)

1. **Frontend Production Build Failure (`page.tsx:19`):**
   - In `apps/web/src/app/page.tsx`, `adminHeaders()` returns a union of incompatible object shapes for `HeadersInit`:
     `{ Authorization: string; "X-Admin-Key"?: undefined } | { "X-Admin-Key": string; Authorization?: undefined }`
   - Next.js type checker halts the build with exit code 1.
   - **Resolution:** Explicitly type the return as `Record<string, string>`.

2. **Frontend Monolithic Code Compression:**
   - Both `apps/web/src/app/page.tsx` (65 lines) and `apps/web/src/app/visit/page.tsx` (33 lines) are collapsed, unformatted blocks with minified state identifiers (`a, p, d, x, s, v`).
   - This makes debugging difficult and makes extending components (like adding the 3D scene to `/visit`, photo uploads, or project registration) brittle.
   - **Resolution:** Refactor into modular, cleanly structured React components (`EquipmentCard`, `ZoneEditor`, `ProjectForm`, `ChatThread`, `PhotoGallery`, `MetricsOverview`).

3. **Disabled Asset Registration in Admin Mode:**
   - On the Operations page, `addAsset` button checks `disabled={!adminKey ...}` instead of `(!adminKey && !adminToken)`. A logged-in administrator with a bearer token is locked out of adding assets through the UI unless they also know the legacy key.
   - **Resolution:** Support both `adminToken` and `adminKey` consistently across all admin action triggers.

4. **N+1 Retrieval Query Pattern:**
   - In `apps/api/app/retrieval.py`, `vector = db.get(ChunkVector, chunk.id)` is called inside a Python loop iterating over every chunk.
   - For an institutional knowledge base with hundreds or thousands of pages, this causes quadratic database lookups.
   - **Resolution:** Perform an eager joined query or batch prefetch of `ChunkVector` rows with `DocumentChunk`.

5. **Lack of Conversational Multi-Turn Context:**
   - The conversational assistant accepts `session_id`, but does not save questions or answers into a conversation table.
   - Subsequent user questions ("What about its power requirements?", "How do I book it?") have zero context of the prior turns.
   - **Resolution:** Add a `ConversationTurn` model and include the last $N$ turns in the grounding prompt.

6. **Missing Public Project Registration Endpoint:**
   - Students and faculty cannot submit projects because `POST /api/projects` requires admin authorization.
   - **Resolution:** Allow public project submission with status `pending_approval`. Only `POST /api/projects/{id}/approve` requires admin credentials.

---

## 2. Security & Governance Debt

1. **Unvalidated Dict Payloads in Admin Routes:**
   - `POST /api/admin/users` and `PATCH /api/admin/users/{user_id}/status` accept raw `payload: dict` rather than Pydantic schemas, bypassing type and length validation.
2. **Missing Rate Limiting:**
   - Endpoints `/api/auth/login` and `/api/assistant/query` have no rate limiting, leaving them susceptible to brute-force credential attacks or Gemini token exhaustion.
3. **Audit Log Incompleteness:**
   - Zone layout updates and asset creations lack complete actor tracking when using legacy admin key.
4. **Secret Management:**
   - `auth.py` falls back to `settings.admin_api_key` if `JWT_SECRET` is empty. The application should warn or generate a strong fallback secret rather than failing silently or insecurely.

---

## 3. Digital Twin & Spatial Debt

1. **Visitor Scene Disconnect:**
   - The interactive 3D laboratory scene is completely absent from the visitor experience (`/visit`).
   - The visitor cannot see the digital twin, cannot click hotspots, and cannot visualize the room layout during a tour.
2. **Zone Coordinate Boundaries:**
   - Currently, zone coordinates are bounded in Pydantic schema (`ge=-8, le=8`), but the frontend 3D scene grid is fixed at 12x9 without visual boundary cues.
3. **Illustrative Room Clarification:**
   - Explicit disclaimers are present in backend metadata, but the frontend needs clear institutional banners indicating that room coordinates are illustrative pending an on-site physical survey.
