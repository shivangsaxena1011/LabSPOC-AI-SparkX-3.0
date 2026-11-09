# LabSPOC AI — Phase 05 + Phase 06 Release Notes

Release: 0.6.0 (development)
Track: SparkX 3.0 — Smart Campus & Digital Twin
Laboratory profile: AI & ML Laboratory, OIST Bhopal

## Phase 05 — Identity, access and governance

- Bootstrap administrator account configured through `ADMIN_USERNAME` and `ADMIN_PASSWORD`.
- Passwords are stored as PBKDF2-HMAC-SHA256 hashes (240,000 iterations, per-user random salt).
- Short-lived HS256 bearer tokens; set `JWT_SECRET` to a unique random value of at least 32 characters.
- Login and current-session endpoints: `POST /api/auth/login`, `GET /api/auth/me`.
- Role values: `admin`, `editor`, `viewer`. Admin-only account administration and audit-log listing; admin/editor content write access. Viewer tokens cannot use protected write endpoints.
- Account activation is checked on protected requests, so deactivation takes effect for bearer-token requests.
- Audit records for authentication, account administration, knowledge approval and reindex operations.
- Legacy `X-Admin-Key` remains supported for compatibility with earlier local releases. Disable/remove it after migrating all clients to bearer authentication.

## Phase 06 — Evidence-grounded hybrid retrieval

- Gemini embedding model configurable through `EMBEDDING_MODEL` (default `gemini-embedding-001`).
- New document chunks are embedded when Gemini is configured and available.
- Vectors are persisted separately from chunk text in `chunk_vectors`.
- Retrieval combines semantic cosine similarity and lexical overlap; lexical-only fallback remains available if embedding calls fail or Gemini is not configured.
- Only approved documents are eligible for retrieval.
- Gemini generation is supplied only retrieved passages and structured asset facts; model output with out-of-range numeric citation markers or unsupported uncited factual claims is rejected in favor of the extractive fallback.
- Admin reindex endpoint: `POST /api/knowledge/reindex`.
- Admin retrieval evaluation endpoint: `POST /api/knowledge/evaluate`.

## Evaluation endpoint format

```json
{
  "cases": [
    {
      "question": "Which approved manual describes the GPU workstation?",
      "expected_document_ids": ["<curator-labelled-document-id>"]
    }
  ]
}
```

The endpoint returns Recall@K and MRR. These metrics are meaningful only when expected document IDs are curated independently. They are not a claim of achieved benchmark performance.

## Environment configuration

Copy `.env.example` to `.env` and configure:

- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `EMBEDDING_MODEL`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD` (12+ characters; use a unique strong password)
- `JWT_SECRET` (32+ random characters)
- `ADMIN_API_KEY` (optional legacy local compatibility; remove for bearer-only operation)

Generate a secret on Windows PowerShell:

```powershell
-join ((1..48 | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) }))
```

Use a cryptographically secure password manager or secret generator for production secrets. The PowerShell example is suitable for local development only.

## Important limitations

- This is a development release. No institutional SSO, MFA, email verification, password reset flow, refresh-token rotation, rate limiting, or formal security review is included.
- The `viewer` role is defined but a public visitor-facing account workflow is not implemented; visitors remain anonymous sessions.
- Gemini embedding and generation require a valid API key, outbound network access, and a model available to the configured Google project. Provider failures fall back to lexical retrieval/extractive answers.
- Semantic retrieval quality has not been benchmarked on a curated OIST laboratory question set. The evaluation endpoint is a harness, not a benchmark result.
- Existing deployments using SQLite `create_all` receive the new tables automatically; production deployments should adopt Alembic migrations before schema changes.
- Never upload confidential or personal records without institutional authorization and a retention/access policy.
