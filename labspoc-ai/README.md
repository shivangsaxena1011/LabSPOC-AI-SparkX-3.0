# LabSPOC AI — Spatially Grounded Virtual Lab Ambassador

**SparkX 3.0 · Smart Campus & Digital Twin · AI & ML Laboratory profile**  
**Release 0.7.0 — Phase 07 spatial digital-twin foundation (development build)**

LabSPOC AI is an evidence-aware virtual laboratory ambassador. It combines a visitor portal, equipment/zone records, document-grounded Q&A, visitor tour planning and consent-aware analytics. It is configured for the AI & ML Laboratory at Oriental Institute of Science & Technology, Bhopal; institution-specific records remain empty until verified information is supplied.

## What's included in this release

### Phase 05 — Access control and governance
- Bootstrap admin account via environment variables.
- PBKDF2 password hashing and short-lived HS256 bearer tokens.
- Admin/editor/viewer role model; admin-only user administration and audit-log viewing.
- Account activation checked on protected bearer-token requests.
- Audit events for login attempts, user administration, knowledge approvals and reindex operations.
- Legacy `X-Admin-Key` compatibility remains for migration from earlier releases.

### Phase 06 — Hybrid evidence-grounded RAG
- Gemini embedding integration (default model: `gemini-embedding-001`).
- Persisted per-chunk embeddings.
- Hybrid semantic cosine + lexical retrieval; lexical fallback when embeddings are unavailable.
- Only approved documents are eligible for retrieval.
- Gemini answer generation receives retrieved evidence only; invalid citation indices and unsupported uncited factual outputs are rejected in favor of extractive fallback.
- Admin endpoints for reindexing and retrieval evaluation (Recall@K and MRR against curator-labelled cases).

### Existing product foundations
- Next.js 14, React, TypeScript, Tailwind, Three.js / React Three Fiber frontend.
- FastAPI and SQLAlchemy backend; SQLite local development and PostgreSQL configuration.
- Zone/equipment/photo data foundations, visitor tour planner, approved project gallery, consent-aware analytics.

## Quick start — Windows 11

### 1. Requirements
- Python 3.11+
- Node.js 20+
- npm
- Optional: Docker Desktop for PostgreSQL

### 2. Configure the backend

```powershell
cd apps/api
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `apps/api/.env` and configure at least:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=gemini-embedding-001
ADMIN_USERNAME=admin
ADMIN_PASSWORD=use-a-unique-password-at-least-12-chars
JWT_SECRET=use-a-unique-random-secret-at-least-32-characters
ADMIN_API_KEY=optional-legacy-local-secret
LAB_NAME=AI & ML Laboratory
INSTITUTION_NAME=Oriental Institute of Science & Technology, Bhopal
```

Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey). Never put it in frontend variables or commit `.env`.

Start the API:

```powershell
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 3. Start the frontend (second terminal)

```powershell
cd apps/web
Copy-Item .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000. Visitor experience: http://localhost:3000/visit.

> The package installation and frontend production build could not be verified in the build environment because `npm install` timed out. Run `npm install` and `npm run build` locally before deployment.

## First administrator login

1. Start the backend with `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `JWT_SECRET` set.
2. Open the **Knowledge** section in the workspace.
3. Sign in using the bootstrap username and password.
4. Upload authorized PDF, DOCX, TXT or MD knowledge documents.
5. Review each upload and approve it only after checking source authority, currentness and permission to use it.
6. Select **Rebuild semantic knowledge index** after configuring Gemini embeddings or after approving older documents.

The bootstrap admin account is created on first successful login if it does not exist. Password hashes, not plaintext passwords, are stored in the users table.

## Key API routes

| Route | Purpose | Access |
|---|---|---|
| `POST /api/auth/login` | Obtain bearer token | Public |
| `GET /api/auth/me` | Inspect current user | Bearer token |
| `POST /api/admin/users` | Create users | Admin |
| `GET /api/admin/users` | List users | Admin |
| `PATCH /api/admin/users/{id}/status` | Activate/deactivate account | Admin |
| `GET /api/admin/audit-logs` | Inspect audit records | Admin |
| `POST /api/knowledge/upload` | Upload authorized knowledge | Admin/editor or legacy key |
| `POST /api/knowledge/documents/{id}/approve` | Approve source for retrieval | Admin/editor or legacy key |
| `POST /api/knowledge/reindex` | Generate missing Gemini embeddings | Admin/editor or legacy key |
| `POST /api/knowledge/evaluate` | Evaluate retrieval against labelled cases | Admin/editor or legacy key |
| `POST /api/assistant/query` | Evidence-grounded question answering | Public visitor route |

## Retrieval evaluation

Example request to `POST /api/knowledge/evaluate`:

```json
{
  "cases": [
    {
      "question": "Which approved manual describes the GPU workstation?",
      "expected_document_ids": ["replace-with-curated-document-id"]
    }
  ]
}
```

The endpoint returns Recall@K and MRR. Expected document IDs must be independently labelled by a human reviewer. Do not report metrics from placeholder labels as product performance. Build a test set with equipment questions, multi-hop SOP questions, ambiguous queries, outdated/conflicting source cases, and questions that should abstain.

## Security and deployment notes

- `ADMIN_API_KEY` is retained only for backward compatibility. Remove it after all clients use bearer tokens; otherwise it remains a privileged alternative credential.
- Use HTTPS, a secret manager, persistent encrypted database/media storage, backups, rate limits, request-size limits, and institutional access policies before a public deployment.
- No SSO, MFA, password reset, refresh-token rotation, email verification, formal threat model, or penetration test is included in this development release.
- `viewer` is a defined account role but the anonymous visitor portal does not require visitor accounts.
- Existing deployments should use Alembic migrations before schema evolution. `Base.metadata.create_all` creates new tables but is not a migration system.

## Honest prototype boundaries

- The 3D room remains illustrative, not a surveyed digital twin. No lab photos were provided. Do not claim spatial accuracy or actual equipment mapping until a lab survey and approved asset inventory are available.
- No institutional equipment, GPU models, publications, project outcomes, SOPs or live sensor telemetry are preloaded.
- Gemini embeddings and generation require a valid key, network access and model availability. Failures use lexical retrieval/extractive fallback.
- Hybrid retrieval is implemented, but retrieval quality has not been benchmarked on an OIST-labelled dataset. The evaluation endpoint is a measurement harness, not proof of achieved accuracy.
- Citation checks reduce some unsupported model output but do not guarantee factual correctness. Human review remains necessary for safety-critical or operational guidance.
- Browser speech depends on browser/device support and is not a guaranteed production voice service.
- This is a development release, not a production-certified institutional platform.

## Test suite

```powershell
cd apps/api
pip install -r requirements-dev.txt
pytest -q
```

Phase 05/06 local automated suite: **10 tests passed** at packaging time. Live Gemini embedding/generation, frontend production build, PostgreSQL migration path and public deployment remain unverified.

## Documentation
- `docs/ARCHITECTURE.md`
- `docs/SECURITY.md`
- `docs/USER_MANUAL.md`
- `docs/PHASE_05_06_RELEASE_NOTES.md`
- `docs/SPARKX_30_DAY_SUBMISSION_CHECKLIST.md`

## License
MIT — see `LICENSE`.


## Phase 07 — Spatial Digital Twin Foundation

Phase 07 adds database-backed spatial zones and a dynamic React Three Fiber floor-plan explorer. Read `docs/PHASE_07_RELEASE_NOTES.md` before using it. The current scene is explicitly illustrative and is not a surveyed representation of the physical OIST laboratory.

- `GET /api/spatial/scene` returns zones and associated equipment.
- `PATCH /api/zones/{zone_id}/layout` updates spatial dimensions (admin/editor only).
- Existing SQLite/PostgreSQL installations receive additive spatial columns at startup.

Do not claim physical digital-twin accuracy until the room has been measured and the layout approved by the institution.
