# LabSPOC AI — Technical Debt & Architectural Assessment (Release 0.7.1)

**System:** LabSPOC AI — Spatially Grounded Virtual Lab Ambassador  
**Release Version:** 0.7.1  
**Status Date:** 2026-11-10  

---

## 1. Resolved Technical Debt (Completed in Release 0.7.1)

| Category | Previously Identified Debt | Resolution Implemented in Release 0.7.1 | Verification |
| :--- | :--- | :--- | :--- |
| **Frontend Compilation** | Next.js build failed at `page.tsx:19` due to `adminHeaders()` union typing incompatible with `HeadersInit`. | Explicitly typed `adminHeaders(): Record<string, string>`. | `npm run build` succeeds with zero errors (Exit code 0). |
| **Retrieval Architecture** | N+1 database queries during hybrid search (`db.get(ChunkVector, chunk.id)` per chunk in loop). | Replaced with single eager query: `select(DocumentChunk, Document, ChunkVector).join(...).outerjoin(...)`. | Benchmarked retrieval latency reduced to 1723 ms (including Gemini vector call). |
| **Conversational Context** | Dialogue was stateless; subsequent questions lacked prior turn context. | Created `ConversationTurn` model; conversational history (last 4 turns) injected into Gemini grounding prompt. | Verified in `test_multi_turn_conversation_context` and `test_workflow_10`. |
| **Project Submission** | Public student/faculty project submissions were blocked by admin key requirements. | Created unauthenticated, rate-limited `POST /api/projects/submit` with regex HTML sanitization and quarantine in `pending_review`. | Verified in `test_workflow_11`. |
| **Database Foreign Keys** | SQLite by default does not enforce FK cascades, leaving orphaned `ChunkVector` rows upon document deletion. | Enabled `PRAGMA foreign_keys=ON` event listener on engine connection; added explicit cleanup in `delete_document`. | Zero orphaned rows; verified in `test_workflow_17`. |
| **Rate Limiter Topology** | In-memory limiter failed to inspect reverse-proxy headers (`X-Forwarded-For`). | Added header inspection for `X-Forwarded-For` and `X-Real-IP` with direct client socket IP fallback. | Verified across proxy and direct test requests. |
| **Database Migrations** | Dynamic schema alterations were scattered imperatively across runtime logic. | Consolidated into idempotent `run_additive_migrations()` checking table schemas and adding missing columns/indexes safely. | Verified in `test_additive_migrations_idempotency`. |
| **Missing Production Docker** | Docker configuration only contained PostgreSQL service without multi-stage API or Web builds. | Authored multi-stage Dockerfiles (`apps/api/Dockerfile`, `apps/web/Dockerfile`) and complete `docker-compose.yml`. | Container definitions verified with healthchecks. |

---

## 2. Honest Institutional Boundaries & Long-Term Roadmap

The following items are recognized architectural boundaries that do not prevent production deployment, but represent the next evolutionary steps for an on-site physical laboratory rollout:

1. **Photogrammetric 3D Room Mesh:**
   - *Current Status:* Three.js laboratory digital twin is modeled to illustrative engineering scale with interactive zone platforms and equipment hotspots.
   - *Roadmap:* Future on-site LiDAR / Matterport photogrammetric scanning of the physical AI & ML Laboratory at OIST Bhopal will provide an exact 1:1 photorealistic mesh.
2. **Distributed Rate Limiting (Redis):**
   - *Current Status:* In-memory sliding-window rate limiter per process instance with reverse-proxy IP resolution.
   - *Roadmap:* For multi-node cluster deployments behind a round-robin load balancer, configure a shared Redis token bucket store.
3. **Dedicated Far-Field Voice Hardware:**
   - *Current Status:* Web Speech API (`SpeechRecognition` / `SpeechSynthesis`) supported natively across Chromium browsers in English and Hindi.
   - *Roadmap:* Physical kiosk deployment at the laboratory entrance can integrate a dedicated noise-canceling far-field microphone array and edge wake-word engine.
4. **Institutional Single Sign-On (SSO / OIDC):**
   - *Current Status:* Robust PBKDF2-HMAC-SHA256 password hashing with HS256 JWT bearer tokens and RBAC hierarchy.
   - *Roadmap:* Integration with OIST campus Active Directory / LDAP / SAML identity provider for single sign-on across faculty and student portals.
