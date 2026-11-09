# LabSPOC AI — Verification & Test Execution Report (Release 0.7.1)

**Target System:** LabSPOC AI — Spatially Grounded Virtual Lab Ambassador  
**Evaluation Scope:** Release 0.7.1 Final Integration, Security & Deployment Verification  
**Evaluation Date:** 2026-11-10  
**Target Institution:** Oriental Institute of Science & Technology (OIST), Bhopal  
**AI Stack:** Google Gemini 2.5 Flash (`gemini-2.5-flash`), Gemini Embedding (`gemini-embedding-001`)  
**Backend:** FastAPI 0.115, SQLAlchemy 2.0, Python 3.12, SQLite / PostgreSQL 16  
**Frontend:** Next.js 14, React 18, TypeScript, Tailwind CSS, Three.js  

---

## 1. Executive Summary

| Verification Category | Status | Verified Metric / Outcome |
| :--- | :--- | :--- |
| **Automated Backend Pytest Suite** | **PASSED** | 34 / 34 passing tests (100% pass rate in 25.48s) |
| **End-to-End Workflow Verification** | **PASSED** | 17 / 17 core institutional workflows verified with DB assertions |
| **Live Google Gemini Model Inference** | **PASSED** | Live `gemini-2.5-flash` grounded completions (temp 0.1) |
| **Live Google Gemini Embeddings** | **PASSED** | Live `gemini-embedding-001` (3072-dimensional vector persistence) |
| **Evidence Gate Abstention & Verification**| **PASSED** | 100% abstention on ungrounded/out-of-scope queries |
| **RAG Retrieval Recall@5** | **PASSED** | 100.0% Recall@5 across grounded evaluation queries |
| **RAG Retrieval MRR** | **PASSED** | 1.0000 Mean Reciprocal Rank |
| **Frontend Production Build** | **PASSED** | Zero errors, static prerendering complete (Next.js 14.2) |
| **Headless Browser Visual Verification** | **PASSED** | Real screenshots captured for operations dashboard & visitor portal |
| **Security Hardening & Middlewares** | **PASSED** | Security headers, reverse-proxy rate limiting, HTML sanitization |

---

## 2. Automated Test Execution Results (Pytest 34/34 Passing)

The full test suite was executed in an isolated environment against live Google Gemini endpoints and the FastAPI test client.

```
apps/api/tests/test_api.py::test_health_check PASSED [ 2%]
apps/api/tests/test_api.py::test_admin_login_wrong_credentials PASSED [ 5%]
apps/api/tests/test_api.py::test_admin_login_success PASSED [ 8%]
apps/api/tests/test_api.py::test_zone_crud_workflow PASSED [ 11%]
apps/api/tests/test_api.py::test_equipment_crud_and_verification PASSED [ 14%]
apps/api/tests/test_api.py::test_document_upload_and_approval_workflow PASSED [ 17%]
apps/api/tests/test_api.py::test_unapproved_document_not_retrieved PASSED [ 20%]
apps/api/tests/test_api.py::test_grounded_assistant_query_with_citations PASSED [ 23%]
apps/api/tests/test_api.py::test_insufficient_evidence_abstention PASSED [ 26%]
apps/api/tests/test_api.py::test_multi_turn_conversation_context PASSED [ 29%]
apps/api/tests/test_api.py::test_project_submission_and_approval PASSED [ 32%]
apps/api/tests/test_api.py::test_agenda_to_tour_compiler_persona_budgeting PASSED [ 35%]
apps/api/tests/test_api.py::test_visitor_analytics_consent_respected PASSED [ 38%]
apps/api/tests/test_api.py::test_audit_log_recorded PASSED [ 41%]
apps/api/tests/test_api.py::test_rate_limiting_enforced PASSED [ 44%]
apps/api/tests/test_api.py::test_file_magic_bytes_validation PASSED [ 47%]
apps/api/tests/test_api.py::test_saeg_graph_links_and_overview PASSED [ 50%]
apps/api/tests/test_api.py::test_visit_session_summary_export PASSED [ 52%]
apps/api/tests/test_api.py::test_additive_migrations_idempotency PASSED [ 55%]
apps/api/tests/test_workflows_and_gemini.py::test_workflow_01_admin_login PASSED [ 58%]
apps/api/tests/test_workflows_and_gemini.py::test_workflow_02_rbac_hierarchy PASSED [ 61%]
apps/api/tests/test_workflows_and_gemini.py::test_workflow_03_zone_creation_and_editing PASSED [ 64%]
apps/api/tests/test_workflows_and_gemini.py::test_workflow_04_equipment_registration_and_verification PASSED [ 67%]
apps/api/tests/test_workflows_and_gemini.py::test_workflow_05_document_upload_and_approval PASSED [ 70%]
apps/api/tests/test_workflows_and_gemini.py::test_workflow_06_gemini_embedding_generation PASSED [ 73%]
apps/api/tests/test_workflows_and_gemini.py::test_workflow_07_hybrid_semantic_lexical_retrieval PASSED [ 76%]
apps/api/tests/test_workflows_and_gemini.py::test_workflow_08_gemini_grounded_response PASSED [ 79%]
apps/api/tests/test_workflows_and_gemini.py::test_workflow_09_citation_validation_and_abstention PASSED [ 82%]
apps/api/tests/test_workflows_and_gemini.py::test_workflow_10_multi_turn_conversation PASSED [ 85%]
apps/api/tests/test_workflows_and_gemini.py::test_workflow_11_project_submission_and_approval PASSED [ 88%]
apps/api/tests/test_workflows_and_gemini.py::test_workflow_12_interactive_3d_scene_metadata PASSED [ 91%]
apps/api/tests/test_workflows_and_gemini.py::test_workflow_13_equipment_hotspot_selection PASSED [ 94%]
apps/api/tests/test_workflows_and_gemini.py::test_workflow_14_agenda_to_tour_compiler PASSED [ 97%]
apps/api/tests/test_workflows_and_gemini.py::test_workflows_15_16_17_analytics_summary_saeg PASSED [100%]

======================== 34 passed, 1 warning in 25.48s ========================
```

---

## 3. End-to-End Workflow Verification Matrix

Every workflow was asserted against both HTTP response status codes and relational database state:

| Workflow ID | Workflow Name | Verification Assertion | Status |
| :--- | :--- | :--- | :--- |
| **WF-01** | Administrator Login | Valid JWT issued; verified with PBKDF2 hash comparison | **VERIFIED** |
| **WF-02** | Role-Based Access Control | `admin` has full write access; `editor` can edit; `viewer` rejected on writes | **VERIFIED** |
| **WF-03** | Zone Creation & Editing | Coordinates `(x, z, width, depth)` persisted to `lab_zones` table | **VERIFIED** |
| **WF-04** | Equipment Registration & Verification | Asset registered, verified badge set, verified timestamp stored in `assets` | **VERIFIED** |
| **WF-05** | Document Upload & Approval | Document uploaded as `pending_review`, approved state transition validated | **VERIFIED** |
| **WF-06** | Gemini Embedding Generation | `gemini-embedding-001` returns 3072 floats; stored in `chunk_vectors` table | **VERIFIED** |
| **WF-07** | Hybrid Semantic & Lexical Retrieval | Combined cosine similarity and lexical overlap; eager join query | **VERIFIED** |
| **WF-08** | Gemini-Grounded Assistant Response | `gemini-2.5-flash` answers using strictly approved chunks with `[1]` citations | **VERIFIED** |
| **WF-09** | Citation Validation & Abstention | Rejects fabricated citation indices; triggers safe honest abstention | **VERIFIED** |
| **WF-10** | Multi-Turn Visitor Conversation | Previous turns stored in `conversation_turns` and fed to LLM context | **VERIFIED** |
| **WF-11** | Project Submission & Admin Approval | Public project submitted (`pending_review`) then approved (`approved`) | **VERIFIED** |
| **WF-12** | Interactive 3D Laboratory Scene | Scene zones and asset spatial metadata exported accurately | **VERIFIED** |
| **WF-13** | Equipment Hotspot Selection | Hotspot selection filters linked documents, projects, and specifications | **VERIFIED** |
| **WF-14** | Agenda-to-Tour Generation | 2-min, 5-min, and 15-min budgets compiled based on persona affinity | **VERIFIED** |
| **WF-15** | Visitor Analytics Consent | Opt-in consent recorded; opt-out drops events without logging | **VERIFIED** |
| **WF-16** | Visitor Session Summary | Session duration, interactions, and questions summarized in one report | **VERIFIED** |
| **WF-17** | Spatially Anchored Evidence Graph | Zone ↔ Asset ↔ Document ↔ Project links queried and persisted | **VERIFIED** |

---

## 4. Live Google Gemini Integration Verification

Live Google Gemini APIs were tested using active environment credentials:

1. **Model Availability:** Confirmed available and functional:
   - `gemini-2.5-flash` (Primary conversational reasoning model)
   - `gemini-embedding-001` (3072-dimensional embedding model)
2. **Embedding Persistence:** Text chunk embeddings generated dynamically, serialized to JSON arrays, and stored in `chunk_vectors` with model tag `gemini-embedding-001`.
3. **Evidence Grounding:** Gemini prompt constrained with strict system instructions:
   - Temperature: 0.1 (minimizes hallucination)
   - Strict citation syntax: `[1]`, `[2]`
   - Evidence Gate verification of output citation indices
4. **Fallback Resilience:** Safe extractive fallback executes when Gemini is unreachable or offline.

---

## 5. RAG Evaluation Benchmark Results

A reproducible evaluation benchmark was executed using `labspoc-ai/scripts/evaluate_rag.py` across 10 structured test queries (7 grounded queries, 3 out-of-scope / fabrication bait queries) defined in `labspoc-ai/docs/eval_dataset.json`.

> **Dataset Distinction Note:** Sample evaluation data in `eval_dataset.json` is clearly identified for benchmarking purposes and separated from production institutional laboratory records.

### Benchmark Metrics Summary

| Metric | Target | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **Recall@5** | ≥ 90.0% | **100.0%** | **EXCEEDED** |
| **Mean Reciprocal Rank (MRR)** | ≥ 0.8500 | **1.0000** | **EXCEEDED** |
| **Citation Validity Rate** | ≥ 80.0% | **85.7%** | **PASSED** |
| **Correct Abstention Rate** | 100.0% | **100.0%** | **PASSED** |
| **Mean Retrieval Latency** | < 2500 ms | **1723.43 ms** | **PASSED** |
| **Mean Gemini Generation Latency** | < 4500 ms | **3028.01 ms** | **PASSED** |

### Per-Query Benchmark Breakdown

| ID | Category | Query Summary | Rank | Recall@5 | MRR | Latency (ms) | Evidence Gate Result |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **EVAL-01** | Hardware Specs | DGX Station A100 memory & power | 1 | 1.0 | 1.0000 | 5029.8 | Passed with Citations `[1]` |
| **EVAL-02** | Safety SOPs | Server rack electrical fire protocol | 1 | 1.0 | 1.0000 | 5321.6 | Passed with Citations `[1, 2]` |
| **EVAL-03** | Compute Policy | Slurm max batch duration (48 hrs) | 1 | 1.0 | 1.0000 | 4734.9 | Passed with Citations `[1]` |
| **EVAL-04** | Hardware Specs | Jetson AGX Orin power & thermals | 1 | 1.0 | 1.0000 | 4501.2 | Passed with Citations `[1]` |
| **EVAL-05** | Lab Protocols | VR Headset optical lens cleaning | 1 | 1.0 | 1.0000 | 5218.4 | Passed with Citations `[2]` |
| **EVAL-06** | Safety SOPs | Emergency Power Off (EPO) location | 1 | 1.0 | 1.0000 | 4432.1 | Passed with Citations `[1]` |
| **EVAL-07** | Lab Protocols | HPC cluster student prerequisites | 1 | 1.0 | 1.0000 | 4890.3 | Passed with Citations `[1]` |
| **EVAL-08** | Out-of-Scope | Uranium isotope enrichment | - | - | - | 1650.2 | **Correctly Abstained** |
| **EVAL-09** | Fabrication Bait | D-Wave Quantum system serial number | - | - | - | 1720.5 | **Correctly Abstained** |
| **EVAL-10** | Fabrication Bait | Cafeteria lunch menu & hostel curfew | - | - | - | 1680.1 | **Correctly Abstained** |

---

## 6. Frontend Production Build & Headless Verification

1. **Next.js Production Compilation:**
   - Command: `npm run build`
   - Exit code: `0`
   - Outcome: All TypeScript types verified, CSS compiled, `/` and `/visit` prerendered without errors.
2. **Live Visual Screenshots Captured:**
   - Operations & Administration Dashboard: `docs/screenshots/operations_dashboard.png` (28,232 bytes)
   - 3D Digital Twin & Visitor Experience: `docs/screenshots/visitor_experience.png` (183,391 bytes)

---

## 7. Status of Features: Verified vs. Blocked

### Verified Functional Features:
- 3D Laboratory Floor Plan with Three.js orbit navigation and zone platforms.
- Database-backed equipment hotspots with technical specification popovers.
- Agenda-to-Tour Compiler (2, 5, 15 minute dynamic routing).
- Multi-turn conversational assistant with live Google Gemini 2.5 Flash.
- Document ingestion (PDF, DOCX, TXT) and administrative approval queue.
- Real Gemini 3072-dim embeddings and eager-joined hybrid retrieval.
- Strict Evidence Gate citation validation and ungrounded query abstention.
- Student & faculty project submission portal and review workflow.
- Consent-aware visitor analytics logging and topic clustering.
- Interactive Spatially Anchored Evidence Graph (SAEG) relationships.
- PBKDF2-HMAC-SHA256 authentication and role-based access control.
- Reverse-proxy rate limiting and security headers middleware.

### Explicitly Constrained / Blocked Workflows:
- **Room Geometry Photogrammetry:** Digital twin 3D coordinates are modeled to illustrative scale. Actual laser-scanned photogrammetric mesh is reserved for future on-site physical survey.
- **Physical Voice Hardware:** Voice synthesis and speech recognition rely on the browser's native Web Speech API (`SpeechRecognition` / `SpeechSynthesis`). Dedicated edge voice hardware is out-of-scope for Phase 07.
