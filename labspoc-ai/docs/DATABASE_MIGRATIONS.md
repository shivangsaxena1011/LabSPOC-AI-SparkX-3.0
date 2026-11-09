# LabSPOC AI — Database Migrations & Schema Architecture (Release 0.8.0)

This document provides complete technical specifications for database schema evolution, additive migrations, relational integrity, connection pooling, and multi-dialect compatibility (SQLite and PostgreSQL).

---

## 1. Schema Design & Relational Entity Model

The LabSPOC AI relational model consists of 14 mapped entities defined in `apps/api/app/models.py`:

```
+-----------------------------------------------------------------------------------------+
|                                    LabZone                                              |
|  id (PK), name, description, x, z, width, depth, color, verified, updated_at            |
+-----------------------------------------------------------------------------------------+
                                           |
                                      (contains)
                                           v
+-----------------------------------------------------------------------------------------+
|                                     Asset                                               |
|  id (PK), name, category, zone_id (FK), description, manufacturer, model,                |
|  specifications, verified_at, updated_at                                                |
+-----------------------------------------------------------------------------------------+
           |                                                      |
    (supported_by)                                          (demonstrated_in)
           v                                                      v
+---------------------+                                +---------------------+
|  AssetDocumentLink  |                                |   AssetProjectLink  |
|  asset_id (FK)      |                                |   asset_id (FK)     |
|  document_id (FK)   |                                |   project_id (FK)   |
+---------------------+                                +---------------------+
           |                                                      |
           v                                                      v
+---------------------+                                +---------------------+
|      Document       |                                |       Project       |
|  id (PK), filename, |                                |  id (PK), title,    |
|  sha256, status,    |                                |  problem_statement, |
|  category, version  |                                |  methodology,       |
+---------------------+                                |  stack, approved    |
           |                                           +---------------------+
      (chunks)
           v
+---------------------+
|    DocumentChunk    |
|  id (PK, autoinc),  |
|  document_id (FK),  |
|  page_number, text  |
+---------------------+
           |
       (vector)
           v
+---------------------+
|     ChunkVector     |
|  chunk_id (PK, FK), |
|  model, vector_json |
+---------------------+
```

Supporting Identity & Observability Tables:
- `User`: `id (PK)`, `username`, `password_hash`, `role`, `active`, `created_at`
- `AuditLog`: `id (PK)`, `actor`, `action`, `resource_type`, `resource_id`, `outcome`, `timestamp`
- `VisitSession`: `id (PK)`, `visitor_token`, `persona`, `duration_minutes`, `consent`, `started_at`
- `AnalyticsEvent`: `id (PK)`, `session_id (FK)`, `event_type`, `target_id`, `created_at`
- `ConversationTurn`: `id (PK)`, `session_id (FK)`, `turn_index`, `question`, `answer`, `citations_json`
- `AssetPhoto`: `id (PK)`, `asset_id (FK)`, `filename`, `storage_name`, `content_type`, `sha256`

---

## 2. Additive Migration Engine (`run_additive_migrations`)

Rather than relying on brittle external migration scripts, LabSPOC AI executes an automated, idempotent migration runner during application startup (`apps/api/app/db.py` / `main.py`).

### Safety Principles:
1. **Zero Data Loss:** Existing tables, rows, and relationships are strictly preserved.
2. **Schema Introspection:** Dynamically queries table metadata via SQLAlchemy `inspect(engine)`:
   - For SQLite: inspects `PRAGMA table_info(table_name)`
   - For PostgreSQL: inspects `information_schema.columns`
3. **Additive DDL Execution:** Detects missing columns or newly introduced metadata attributes and applies precise `ALTER TABLE ... ADD COLUMN` statements.
4. **Idempotency:** Safe to run repeatedly across application restarts or container updates without error.

---

## 3. Database Dialect Parity: SQLite vs. PostgreSQL

| Feature | SQLite (Development / Local Kiosk) | PostgreSQL 16 (Production) |
| :--- | :--- | :--- |
| **Driver** | `sqlite3` (built-in standard library) | `psycopg2-binary` |
| **Connection String** | `sqlite:///./labspoc.db` | `postgresql://user:pass@host:5432/db` |
| **Foreign Key Enforcement** | Enabled via `PRAGMA foreign_keys=ON` event listener | Enforced natively by database engine |
| **Transactions & WAL** | Write-Ahead Logging (`PRAGMA journal_mode=WAL`) | ACID multi-version concurrency control (MVCC) |
| **Connection Pooling** | `StaticPool` or `NullPool` (avoids thread locking) | `QueuePool` with pool pre-ping & max overflow |

---

## 4. Performance Indexes

The following indexes are verified during schema initialization for low-latency queries:

```sql
-- Fast asset lookup by spatial zone
CREATE INDEX IF NOT EXISTS idx_assets_zone_id ON assets(zone_id);

-- Fast chunk retrieval by document
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id);

-- High-speed analytics aggregation
CREATE INDEX IF NOT EXISTS idx_analytics_session_id ON analytics_events(session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics_events(event_type);

-- Relational graph traversal
CREATE INDEX IF NOT EXISTS idx_asset_doc_asset ON asset_document_links(asset_id);
CREATE INDEX IF NOT EXISTS idx_asset_proj_asset ON asset_project_links(asset_id);
```

---

## 5. Rollback & Disaster Recovery Playbook

If a deployment or schema alteration requires rolling back:
1. **SQLite Rollback:**
   ```bash
   cp backups/labspoc_backup_pre_deploy.db labspoc.db
   ```
2. **PostgreSQL Rollback:**
   ```bash
   # Terminate active backend connections, drop database, recreate from dump
   dropdb -h localhost -U labspoc labspoc
   createdb -h localhost -U labspoc labspoc
   pg_restore -h localhost -U labspoc -d labspoc backups/labspoc_pre_deploy.dump
   ```
