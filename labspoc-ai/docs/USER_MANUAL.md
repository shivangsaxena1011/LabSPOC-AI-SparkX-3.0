# LabSPOC AI — User and Operator Manual

## Visitor workflow
1. Open the web application.
2. Select a visitor profile.
3. Explore the laboratory scene.
4. Select a mapped hotspot when real asset IDs are configured.
5. Ask a question in the assistant.
6. Inspect the evidence status and cited source documents.
7. Generate a time-bounded tour.
8. Browse approved project records.

## Knowledge administrator workflow
1. Obtain authorization to use each laboratory document.
2. Upload PDF, DOCX, TXT or Markdown from the Knowledge page.
3. Review the uploaded file and its extraction quality.
4. Approve only accurate, current, authorized material.
5. Verify a set of known-answer questions against the source.
6. Monitor unanswered questions and stale records.

Important: approval is currently exposed as an API endpoint without authentication. Do not deploy this starter release publicly with institutional data until authentication and authorization are implemented.

## API
Interactive OpenAPI documentation is available at `/docs` while the API is running.

Key endpoints:
- GET `/api/health`
- GET/POST `/api/assets`
- GET `/api/assets/{asset_id}`
- POST `/api/knowledge/upload`
- GET `/api/knowledge/documents`
- POST `/api/knowledge/documents/{doc_id}/approve`
- POST `/api/assistant/query`
- POST `/api/visits`
- POST `/api/tours/plan`
- GET/POST `/api/projects`
- GET `/api/analytics/overview`

## Troubleshooting
- Frontend cannot reach API: verify `NEXT_PUBLIC_API_URL` and CORS origins.
- PDF yields no text: it may be scanned; OCR support is not included in this initial release.
- No answer: ensure a document is approved and contains searchable text.
- Voice unavailable: browser/OS may not support Web Speech; use text input.
- Empty tour: configure actual assets and approve project records first.

## Release 0.2: AI & ML laboratory configuration

1. Copy `apps/api/.env.example` to `apps/api/.env`.
2. Set `LLM_PROVIDER=gemini`, `GEMINI_API_KEY` to a server-side Google AI Studio key, and optionally set `GEMINI_MODEL` (default `gemini-2.5-flash`).
3. Set `ADMIN_API_KEY` to a long random secret. Do not expose it in source control or public client-side environment variables.
4. Set `LAB_NAME=AI & ML Laboratory` and `INSTITUTION_NAME=Oriental Institute of Science & Technology, Bhopal`.
5. Restart the API. `GET /api/health` reports whether Gemini and the admin boundary are configured; it never returns secret values.
6. In the Knowledge section, enter the administrator key, upload authorized lab documents, review each document, and approve only material whose owner and currency have been checked.
7. In Virtual Lab, register actual equipment with stable IDs. Do not treat placeholder 3D geometry as a surveyed digital twin.
8. Test Q&A against known questions and unsupported questions. Confirm that citations point to approved documents and that unsupported details are explicitly marked unverified.

### Admin API header

For write operations, send `X-Admin-Key: <ADMIN_API_KEY>`. Protected endpoints include `POST /api/assets`, `POST /api/knowledge/upload`, `POST /api/knowledge/documents/{id}/approve`, `POST /api/projects`, and `POST /api/projects/{id}/approve`.

### Gemini privacy and cost

Only the user question and the retrieved approved evidence snippets are sent to Gemini. Do not upload personal, confidential, export-controlled, or restricted institutional records without written authorization and an approved data-processing review. Monitor API usage and configure provider-side quotas/budgets.

## Phase 05 — Administrator sign-in

Set `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and a unique `JWT_SECRET` in the API `.env`. Start the API, open the Knowledge section, and sign in. The bootstrap account is created on first login. User-management endpoints are documented at `/docs`; only admins can create accounts or inspect audit logs. Give editors only the access needed for knowledge and content maintenance. Do not share the bootstrap password.

## Phase 06 — Semantic knowledge indexing

Upload a source document; it enters `pending_review`. Review its authority, date, scope, and usage permission before approving it. With Gemini embeddings configured, chunks are embedded during upload. If a document was uploaded before embeddings were configured, or embedding calls were temporarily unavailable, use **Rebuild semantic knowledge index** after approval. Ask test questions and inspect citations. Use `POST /api/knowledge/evaluate` with independently curated expected document IDs to calculate Recall@K and MRR. Do not claim retrieval accuracy until a representative evaluation set has been run and reported with its sample size and methodology.
