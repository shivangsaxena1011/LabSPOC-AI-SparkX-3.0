# LabSPOC AI — Production Deployment & Operations Guide (Release 0.7.1)

This document provides complete deployment specifications, container orchestration instructions, environment configurations, and backup/restoration procedures for LabSPOC AI.

---

## 1. Architecture & Deployment Topologies

LabSPOC AI supports two deployment topologies:

### A. Development / Lightweight Edge Deployment (SQLite)
- Single-node deployment using embedded SQLite with Write-Ahead Logging (WAL) and foreign key enforcement (`PRAGMA foreign_keys=ON`).
- Suitable for local development, rapid prototyping, and on-premises kiosk hardware without external database dependencies.

### B. High-Availability Institutional Production Deployment (PostgreSQL + Docker Compose)
- Multi-container topology orchestrated via Docker Compose:
  - `labspoc-postgres`: PostgreSQL 16 Alpine container with persistent named volume.
  - `labspoc-api`: FastAPI backend running in an unprivileged container with Python 3.12-slim.
  - `labspoc-web`: Next.js 14 frontend running in a standalone Node.js 20 Alpine container.
- Shared bridge network (`labspoc_net`) with isolated database port binding.

---

## 2. Container Orchestration (Docker Compose)

The multi-container production stack is defined in `docker-compose.yml` (at repository root and in `infra/docker-compose.yml`).

### Container Services Definition

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:16-alpine
    container_name: labspoc-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-labspoc}
      POSTGRES_USER: ${POSTGRES_USER:-labspoc}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-change-this-local-password}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-labspoc} -d ${POSTGRES_DB:-labspoc}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - labspoc_net

  api:
    build:
      context: ./labspoc-ai/apps/api
      dockerfile: Dockerfile
    container_name: labspoc-api
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-labspoc}:${POSTGRES_PASSWORD:-change-this-local-password}@postgres:5432/${POSTGRES_DB:-labspoc}
      GEMINI_API_KEY: ${GEMINI_API_KEY:-}
      JWT_SECRET: ${JWT_SECRET:-change-me-in-production-min-32-chars-key}
      ENVIRONMENT: production
      CORS_ORIGINS: '["http://localhost:3000","http://127.0.0.1:3000"]'
      UPLOAD_DIR: /app/uploads
    ports:
      - "8000:8000"
    volumes:
      - api_uploads:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')\" || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 15s
    networks:
      - labspoc_net

  web:
    build:
      context: ./labspoc-ai/apps/web
      dockerfile: Dockerfile
    container_name: labspoc-web
    restart: unless-stopped
    environment:
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL:-http://localhost:8000}
      PORT: 3000
    ports:
      - "3000:3000"
    depends_on:
      - api
    networks:
      - labspoc_net

volumes:
  postgres_data:
  api_uploads:

networks:
  labspoc_net:
    driver: bridge
```

---

## 3. Environment Variables Reference

### Backend Configuration (`apps/api`)

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `DATABASE_URL` | No | `sqlite:///./labspoc.db` | SQLAlchemy connection string (SQLite or PostgreSQL) |
| `GEMINI_API_KEY` | Recommended | None | Google Gemini API key for embeddings and grounded reasoning |
| `JWT_SECRET` | Production | `labspoc-super-secret-key-change-in-production-2026` | 256-bit secret key for signing admin and visitor JWTs |
| `ENVIRONMENT` | No | `development` | Environment mode (`development`, `staging`, `production`) |
| `CORS_ORIGINS` | No | `["http://localhost:3000"]` | JSON array of permitted HTTP origins |
| `RATE_LIMIT_PER_MINUTE`| No | `120` | Max API requests permitted per minute per IP address |
| `ADMIN_USERNAME` | No | `admin` | Default initial bootstrap admin username |
| `ADMIN_PASSWORD` | No | `admin123` | Default initial bootstrap admin password (change immediately) |
| `UPLOAD_DIR` | No | `uploads` | Filesystem path for document and asset photo storage |
| `MAX_UPLOAD_SIZE_MB` | No | `25` | Maximum document upload size in megabytes |

### Frontend Configuration (`apps/web`)

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Base URL of the backend FastAPI service |
| `PORT` | No | `3000` | Port for the Next.js production server |

---

## 4. Additive Database Migrations

LabSPOC AI incorporates an automated, idempotent migration runner (`run_additive_migrations` in `apps/api/app/db.py`) that executes automatically on startup:

- **Safety Guarantee:** Existing tables and data are strictly preserved.
- **Additive DDL:** Inspects columns across SQLite (`PRAGMA table_info`) and PostgreSQL (`information_schema.columns`) and dynamically issues additive `ALTER TABLE` statements for any newly introduced fields.
- **Index Optimization:** Automatically creates missing performance indexes for frequently queried foreign keys (`asset_document_links`, `asset_project_links`, `document_chunks`, `chunk_vectors`).

---

## 5. Database Backup and Recovery Procedures

### SQLite Backup & Recovery

1. **Online Non-Blocking Backup (Hot Backup):**
   ```bash
   sqlite3 labspoc.db ".backup 'backups/labspoc_backup_$(date +%Y%m%d_%H%M%S).db'"
   ```

2. **Integrity Verification:**
   ```bash
   sqlite3 backups/labspoc_backup.db "PRAGMA integrity_check;"
   ```

3. **Restoration:**
   ```bash
   # Stop application services, then copy backup into position:
   cp backups/labspoc_backup.db labspoc.db
   ```

### PostgreSQL Backup & Recovery

1. **Full Database Dump:**
   ```bash
   pg_dump -h localhost -p 5432 -U labspoc -F c -b -v -f "backups/labspoc_pg_$(date +%Y%m%d_%H%M%S).dump" labspoc
   ```

2. **Schema-Only Dump:**
   ```bash
   pg_dump -h localhost -p 5432 -U labspoc --schema-only -f "backups/schema_only.sql" labspoc
   ```

3. **Restoration:**
   ```bash
   # Restore to target database with schema recreation:
   pg_restore -h localhost -p 5432 -U labspoc -d labspoc -v "backups/labspoc_pg.dump"
   ```

---

## 6. Health Monitoring and Structured Logging

- **Health Endpoint:** `GET /api/health` returns HTTP 200 with JSON payload:
  ```json
  {
    "status": "ok",
    "service": "LabSPOC AI API",
    "version": "0.7.1",
    "laboratory": "AI & ML Laboratory",
    "institution": "Oriental Institute of Science & Technology, Bhopal",
    "llm_provider": "gemini",
    "gemini_configured": true,
    "admin_configured": true
  }
  ```
- **Reverse Proxy Headers:** The API inspects `X-Forwarded-For` and `X-Real-IP` when deployed behind Nginx, Traefik, or Cloudflare, maintaining accurate rate limiting and client IP logs.
- **Structured Audit Logging:** Administrative actions (zone modification, document approval, equipment verification) are recorded immutably in the `audit_logs` table.
