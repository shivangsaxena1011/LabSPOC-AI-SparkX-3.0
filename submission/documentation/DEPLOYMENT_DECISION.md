# LabSPOC AI — Production Deployment Architecture & Cost Evaluation (Release 0.8.0)

**Competition:** Galgotias University — SPARKX 3.0 International, 30-Day Innovation Challenge  
**Project:** LabSPOC AI — Spatially Grounded Virtual Lab Ambassador  
**Track:** Smart Campus & Digital Twin / AI-Powered Intelligent Lab SPOC  
**Institution:** Oriental Institute of Science & Technology (OIST), Bhopal  
**Target Laboratory Profile:** AI & ML Laboratory  
**Project Lead:** Shivang Saxena  

---

## 1. Executive Summary & Cost Model

As a student-led institutional laboratory innovation challenge entry, the deployment architecture for LabSPOC AI must balance **five core engineering criteria**:
1. **Zero / Minimal Ongoing Cost:** Sustainable within free-tier student allowances without recurring financial burden.
2. **High Availability & Reliability:** 99.9% uptime during juror evaluation and live campus kiosk demonstrations.
3. **Data Residency & Privacy Compliance:** Adherence to institutional data governance standards and Ministry of Electronics and Information Technology (MeitY) guidelines.
4. **Persistent Asset & Vector Storage:** Guaranteed preservation of approved laboratory SOPs, equipment metadata, and 3072-dimensional vector embeddings across container restarts.
5. **Cold-Start Resilience:** Fast frontend rendering and responsive backend response times.

### Comprehensive Provider Matrix & Cost Projection

| Component | Selected Primary Provider | Evaluated Alternatives | Free-Tier Allocation | Projected Cost (Demonstration Phase) |
| :--- | :--- | :--- | :--- | :---: |
| **Frontend Web** | **Vercel** | Cloudflare Pages, Netlify | 100 GB bandwidth/mo, unlimited builds | **\$0.00 / month** |
| **Backend API** | **Render (Web Service)** | Railway, Fly.io, Koyeb | 750 free instance hours/month | **\$0.00 / month** |
| **Database** | **Neon (Serverless Postgres)**| Supabase, Aiven, ElephantSQL | 0.5 GB storage, autoscaling compute | **\$0.00 / month** |
| **Object Storage**| **Cloudflare R2** | AWS S3, MinIO, Backblaze B2 | 10 GB storage, zero egress fees | **\$0.00 / month** |
| **AI Reasoning** | **Google Gemini API** | OpenAI GPT-4o, Anthropic Claude | 15 RPM free tier on AI Studio | **\$0.00 / month** |
| **TOTAL** | — | — | — | **\$0.00 / month** |

---

## 2. In-Depth Provider Evaluation & Selection Rationales

### 2.1 Frontend Hosting: Vercel
- **Selection Rationale:** Native Next.js 14 optimization. Vercel automatically deploys static pages (`/` and `/visit`) to global Edge CDN points of presence, providing sub-50ms Time to First Byte (TTFB) in India (Mumbai/Delhi edge nodes).
- **Alternative Considered (Cloudflare Pages):** Excellent edge performance and zero bandwidth limits, but requires custom Next.js OpenNext adapters which introduce edge runtime incompatibilities with Three.js WebGL bundles.
- **Alternative Considered (Netlify):** Comparable feature set, but Vercel's build pipeline and zero-config incremental static regeneration provide superior developer velocity.

### 2.2 Backend API Hosting: Render
- **Selection Rationale:** Native Docker container execution from GitHub repository commits. Render supports background worker processes, custom Dockerfiles, automated HTTPS certificate provisioning via Let's Encrypt, and health check integration with `/api/health`.
- **Alternative Considered (Railway):** Extremely fast startup times and built-in metric graphs; however, Railway's free trial credit ($5 one-time) expires after 30 days, creating financial exposure for long-term academic maintenance.
- **Alternative Considered (Fly.io):** Excellent global Anycast routing, but requires dedicated credit card verification and CLI deployment workflows that complicate student handover.

### 2.3 Relational Database: Neon
- **Selection Rationale:** Modern serverless PostgreSQL 16 with instant branching, connection pooling via PgBouncer, and automated point-in-time recovery. Neon's free tier provides 0.5 GB of storage—sufficient for tens of thousands of equipment records, document chunks, and audit logs.
- **Alternative Considered (Supabase):** Excellent Postgres ecosystem, but automatically pauses free projects after 7 days of inactivity, introducing cold-start failures during juror review. Neon handles scale-to-zero with automatic wake-up upon connection.
- **Alternative Considered (Self-Hosted PostgreSQL in Docker):** Supported directly in our `docker-compose.yml` for local campus servers, but requires an always-on institutional VM with open inbound ports.

### 2.4 Object Storage: Cloudflare R2 (S3-Compatible)
- **Selection Rationale:** Full S3 API compatibility natively supported by our `S3StorageAdapter` via `boto3`. Cloudflare R2 eliminates all egress bandwidth fees (unlike AWS S3), preventing unexpected billing spikes from public document downloads.
- **Alternative Considered (AWS S3):** Industry standard, but carries egress data transfer fees and complex IAM policy configuration.
- **Alternative Considered (Local Container Filesystem):** Flawed for cloud containers because ephemeral filesystems discard uploaded documents upon container redeployment.

### 2.5 AI Provider: Google Gemini
- **Selection Rationale:** Official preferred provider for SPARKX 3.0. `gemini-2.5-flash` provides rapid conversational inference (1.5–3.0s latency) with high factual obedience at temperature 0.1. `gemini-embedding-001` generates rich 3072-dimensional vector embeddings with strong semantic representation for engineering terminology.

---

## 3. Data Residency & Institutional Governance Considerations

1. **Academic Data Sovereignty:** The AI & ML Laboratory at OIST Bhopal maintains research data that may involve pre-publication student capstones. All raw research project submissions remain quarantined in `pending_review` until signed off by faculty mentors.
2. **Indian Data Protection (DPDP Act 2023):** LabSPOC AI implements **Privacy by Design**:
   - Zero storage of personally identifiable information (PII).
   - Explicit opt-in consent toggles for visitor analytics.
   - Transparent local session summary downloads before visitor departure.
3. **Hybrid Edge-Cloud Topology:** For strict institutional environments where no cloud database is permitted, LabSPOC AI runs self-contained on a local laboratory workstation using SQLite and local disk storage via single-command Docker Compose.
