# LabSPOC AI — Phase 02 release notes

**Workspace:** AI & ML Laboratory, Oriental Institute of Science & Technology, Bhopal  
**Release:** 0.2.0

## Implemented in this phase

- Workspace identity and provider configuration are exposed through a non-secret public configuration endpoint.
- Gemini server-side integration (`google-genai`) is available when `LLM_PROVIDER=gemini` and `GEMINI_API_KEY` are configured.
- Gemini receives only retrieved approved passages and/or a structured asset record. The system asks it to answer only from that evidence and to state when a fact is not verified.
- Provider failure or missing configuration falls back to the previous extractive response; it does not silently invent an answer.
- Write routes require `X-Admin-Key`; missing server configuration fails closed, and incorrect keys return 401.
- Document and project approval endpoints are protected. Asset creation, document upload, and project creation are protected.
- Frontend administrator-key field, document approval action, and basic asset registration form are wired to the protected API.
- Security and operator documentation updated.

## Validation performed

- Python syntax compilation: passed.
- API test suite: 4 passed.
- Manual API smoke test: health endpoint returned 200; incorrect admin key returned 401; valid admin key allowed asset creation (temporary test record removed).
- Frontend dependency installation/build: not completed in this environment because `npm install` timed out. Run install and production build locally before deployment.
- Live Gemini call: not tested because no API key was supplied. Configure a key and verify with a real test question before claiming Gemini inference is operational.

## Remaining product work

- Replace shared admin key with institutional SSO/OIDC, role-based access control, and audit logs.
- Add database migrations (Alembic) before schema evolution in persistent deployments.
- Add semantic embeddings/vector search, reranking, retrieval evaluation, and source-level versioning.
- Add photo/panorama asset storage and map verified lab images to persistent asset IDs.
- Replace illustrative 3D geometry with a surveyed scene or real approved 360° photographs.
- Complete voice interaction, language selection/translation QA, project submission/review UI, and visitor digest.
- Add upload malware scanning, object storage, rate limits, retention policy, backups, observability, and deployment hardening.

This is a development release, not a claim of production certification or complete implementation of all challenge modules.
