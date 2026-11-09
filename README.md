# LabSPOC AI — Spatially Grounded Virtual Lab Ambassador

**Challenge:** Galgotias University — SPARKX 3.0 International, 30-Day Innovation Challenge  
**Track:** Smart Campus & Digital Twin / AI-Powered Intelligent Lab SPOC  
**Institution:** Oriental Institute of Science & Technology (OIST), Bhopal  
**Laboratory Profile:** AI & ML Laboratory  
**Preferred AI Provider:** Google Gemini (`gemini-2.5-flash`, `gemini-embedding-001`)  
**Release:** 0.7.0 (Production Stabilization & Full Feature Integration)  

---

## Deliverables Index

- [CODEBASE_AUDIT.md](file:///C:/Users/Project/LabSPOC%20AI%20SparkX%203.0/CODEBASE_AUDIT.md): Comprehensive Phase 01 codebase audit and verification report.
- [IMPLEMENTATION_STATUS.md](file:///C:/Users/Project/LabSPOC%20AI%20SparkX%203.0/IMPLEMENTATION_STATUS.md): Challenge modules & signature innovations status matrix.
- [TECHNICAL_DEBT.md](file:///C:/Users/Project/LabSPOC%20AI%20SparkX%203.0/TECHNICAL_DEBT.md): Technical debt assessment and remediation log.
- [Source Code](file:///C:/Users/Project/LabSPOC%20AI%20SparkX%203.0/labspoc-ai):
  - [Backend API (`labspoc-ai/apps/api`)](file:///C:/Users/Project/LabSPOC%20AI%20SparkX%203.0/labspoc-ai/apps/api)
  - [Frontend Web App (`labspoc-ai/apps/web`)](file:///C:/Users/Project/LabSPOC%20AI%20SparkX%203.0/labspoc-ai/apps/web)
  - [Documentation (`labspoc-ai/docs`)](file:///C:/Users/Project/LabSPOC%20AI%20SparkX%203.0/labspoc-ai/docs)

---

## Quick Start & Verification

### 1. Run Automated Backend Tests (19/19 Passing)
```powershell
cd "labspoc-ai\apps\api"
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pytest -v
```

### 2. Verify Frontend Production Build
```powershell
cd "labspoc-ai\apps\web"
npm install
npm run build
npm run dev
```

### 3. Access Portals
- **Operations & Admin Workspace:** `http://localhost:3000`
- **Visitor Experience Portal:** `http://localhost:3000/visit`
- **FastAPI OpenAPI Documentation:** `http://localhost:8000/docs`
