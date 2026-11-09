# Security and privacy notes

This repository is an initial development release, not a security-certified institutional deployment.

Before public deployment:
1. Add authentication (OIDC/SAML or institutional identity provider).
2. Enforce role-based authorization on document upload, approval, asset editing, project approval, and analytics.
3. Scan uploads for malware; validate MIME type and file size; isolate parsing.
4. Store confidential files in private object storage.
5. Apply document-level access controls during retrieval.
6. Add rate limiting, audit logs, secret rotation and TLS.
7. Implement visitor consent, retention, export and deletion workflows.
8. Review privacy obligations and institutional policies.
9. Do not ingest unpublished patent or research material without owner authorization.
10. Never expose raw internal document chunks to unauthorized visitors.

## Release 0.2 administrator boundary

All write operations that change the institutional knowledge base (asset creation, document upload/approval, project creation/approval) require the `X-Admin-Key` header. Configure a long random `ADMIN_API_KEY`; if it is unset, write operations fail closed with HTTP 503. A missing or incorrect key returns HTTP 401. The comparison uses a constant-time comparison.

This is a development/staging access boundary, not institutional identity management. Before public institutional deployment, replace the shared key with SSO/OIDC, individual administrator identities, role-based permissions, audit trails, key rotation, and secret management. Never put the Gemini API key in the frontend or commit `.env` files.

Gemini is invoked only after approved knowledge passages and/or a structured asset record have been retrieved. The prompt explicitly restricts generation to that evidence. If Gemini is unavailable, the API falls back to its extractive evidence response. Provider errors are not exposed to visitors. This is a mitigation, not a guarantee against hallucination; validate answers with a representative benchmark before deployment.

## Phase 05 identity and access controls

The API supports bootstrap administrator credentials (`ADMIN_USERNAME`, `ADMIN_PASSWORD`), PBKDF2-HMAC-SHA256 password hashing with per-user salts, HS256 bearer tokens, and `admin` / `editor` / `viewer` role values. `JWT_SECRET` must be a unique secret of at least 32 characters. Protected bearer-token requests check that the account remains active and that its role has not changed. Admin-only routes manage users and inspect audit records. Content write routes accept admin/editor tokens.

`X-Admin-Key` remains supported as a compatibility path for older releases. It is a shared privileged secret and should be removed from production after clients migrate to bearer tokens. No SSO, MFA, password reset, refresh-token rotation, or formal security audit is included.

## Phase 06 retrieval safeguards

Only approved document chunks enter retrieval. When Gemini is configured, query and chunk embeddings are used for hybrid semantic/lexical ranking. If embeddings are unavailable, retrieval falls back to lexical overlap. Gemini receives only retrieved evidence and structured lab facts. The response gate rejects invalid numeric citation references and unsupported uncited factual answers, then uses an extractive fallback. These measures reduce risk but do not prove answer correctness or eliminate hallucinations; human review and a curated evaluation set are required.
