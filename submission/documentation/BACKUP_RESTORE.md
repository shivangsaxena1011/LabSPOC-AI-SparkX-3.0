# LabSPOC AI — Backup, Restoration & Disaster Recovery Guide (Release 0.8.0)

This document provides operational procedures for routine backups, disaster recovery, integrity verification, and data retention for LabSPOC AI across both SQLite and PostgreSQL environments.

---

## 1. Backup Strategy Overview

| Environment | Database Engine | Backup Method | Recommended Frequency | Retention Window |
| :--- | :--- | :--- | :--- | :--- |
| **Development / Kiosk** | SQLite 3 | Hot `.backup` API / CLI | Daily / Prior to updates | 7 days |
| **Production Cloud** | PostgreSQL 16 | `pg_dump` custom format | Hourly differential, Daily full | 30 days |
| **Media & Documents** | Object Store (S3 / R2) | Bucket versioning & replication | Continuous | Indefinite |

---

## 2. SQLite Backup Procedures (Development & Local Kiosks)

### 2.1 Online Non-Blocking Hot Backup
SQLite provides an atomic online backup API that captures a consistent snapshot without locking write transactions:

```bash
# Using SQLite CLI .backup command:
sqlite3 labspoc.db ".backup 'backups/labspoc_backup_$(date +%Y%m%d_%H%M%S).db'"
```

### 2.2 Backup Integrity Check
Always verify that the generated backup file is structurally sound and free from page corruption:

```bash
sqlite3 backups/labspoc_backup_*.db "PRAGMA integrity_check;"
# Expected output: ok
```

### 2.3 SQLite Restoration
```bash
# 1. Stop the LabSPOC API process/container
# 2. Archive the corrupt/damaged database
mv labspoc.db labspoc.corrupt.bak

# 3. Restore the verified backup
cp backups/labspoc_backup_20261110.db labspoc.db

# 4. Restart the API process
```

---

## 3. PostgreSQL Backup Procedures (Production Deployment)

### 3.1 Full Production Dump (Compressed Archive)
Captures tables, indexes, sequences, and foreign key relationships in custom binary format:

```bash
pg_dump \
  --host=localhost \
  --port=5432 \
  --username=labspoc \
  --format=custom \
  --blobs \
  --verbose \
  --file="backups/labspoc_pg_$(date +%Y%m%d_%H%M%S).dump" \
  labspoc
```

### 3.2 Automated Daily Cron Backup Script (`scripts/backup_postgres.sh`)
```bash
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/var/backups/labspoc"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/labspoc_pg_${TIMESTAMP}.dump"

mkdir -p "${BACKUP_DIR}"

echo "[INFO] Starting LabSPOC database backup to ${BACKUP_FILE}..."
pg_dump -h "${DB_HOST:-postgres}" -U "${DB_USER:-labspoc}" -d "${DB_NAME:-labspoc}" -F c -b -f "${BACKUP_FILE}"

echo "[INFO] Pruning backups older than 30 days..."
find "${BACKUP_DIR}" -type f -name "labspoc_pg_*.dump" -mtime +30 -delete

echo "[INFO] Backup complete. Size: $(du -h "${BACKUP_FILE}" | cut -f1)"
```

### 3.3 PostgreSQL Full Database Restoration
To restore into a fresh or recovered database:

```bash
# 1. Terminate existing client connections
psql -U labspoc -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'labspoc' AND pid <> pg_backend_pid();"

# 2. Drop and recreate database
dropdb -U labspoc labspoc
createdb -U labspoc labspoc

# 3. Restore from custom dump
pg_restore \
  --host=localhost \
  --port=5432 \
  --username=labspoc \
  --dbname=labspoc \
  --verbose \
  --clean \
  --if-exists \
  "backups/labspoc_pg_20261110.dump"

# 4. Verify table row counts
psql -U labspoc -d labspoc -c "SELECT count(*) FROM assets; SELECT count(*) FROM documents;"
```

---

## 4. Persistent Document & Media Recovery

1. **Local Filesystem:**
   When running with `STORAGE_BACKEND=local`, the `./uploads` directory contains all uploaded PDF manuals, DOCX policies, and equipment photos. Back up this directory alongside the database:
   ```bash
   tar -czvf "backups/uploads_$(date +%Y%m%d).tar.gz" uploads/
   ```
2. **Object Storage (Cloudflare R2 / AWS S3):**
   When running with `STORAGE_BACKEND=s3`, document files are persisted outside the container. Enable **Bucket Versioning** in the S3/R2 dashboard to protect against accidental deletions or overwrites.
