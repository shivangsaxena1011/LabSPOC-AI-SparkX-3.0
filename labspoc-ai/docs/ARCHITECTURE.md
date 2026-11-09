# Architecture and engineering decisions

## Spatially Anchored Evidence Graph (SAEG)
The initial implementation uses persistent relational IDs rather than claiming a graph database. `SceneHotspot` is represented in the frontend scene configuration and resolves to an `Asset.id`. The asset record can link to evidence documents by metadata and to approved projects. A production data model should add explicit many-to-many association tables for asset-document, asset-project, and asset-publication links.

## Evidence pipeline
Upload -> SHA-256 duplicate check -> text extraction -> chunking -> pending review -> administrator approval -> lexical retrieval -> source-cited extractive response / abstention.

The current release deliberately avoids unsupported generative claims. It is a functional retrieval baseline. Add embeddings/vector search, reranking, claim verification, and configurable LLM synthesis as separately benchmarked services.

## Tour planner
The current planner selects configured assets and approved projects using transparent keyword overlap against agenda/interests and allocates the duration budget. It is not yet an optimized route solver. Add real spatial coordinates, walking/transition costs, required stops, relevance scoring and constraint optimization after receiving a surveyed lab layout.

## Production hardening required
- Authentication and role-based authorization on every admin endpoint.
- Malware scanning and content-disarm pipeline for uploads.
- PostgreSQL migrations (Alembic), backups and restore drills.
- Object storage with private buckets and signed URLs.
- Rate limiting, audit logs, structured observability.
- PII minimization and retention enforcement.
- Embedding/vector index and retrieval benchmark.
- Real lab scene and asset verification workflow.
- Email provider for director digest.
- Automated tests for access control, file parsing, retrieval, abstention and tour constraints.
