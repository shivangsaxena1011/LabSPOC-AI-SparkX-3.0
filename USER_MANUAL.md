# LabSPOC AI — Institutional User & Operator Manual (Release 0.7.1)

**Target System:** LabSPOC AI — Spatially Grounded Virtual Lab Ambassador  
**Target Laboratory Profile:** AI & ML Laboratory, Oriental Institute of Science & Technology (OIST), Bhopal  
**Platform Version:** Release 0.7.1  

---

## Part 1: Visitor Guide (`/visit`)

The Visitor Experience portal is designed for prospective students, faculty researchers, industry visitors, and accreditation reviewers exploring the AI & ML Laboratory.

### 1.1 Visitor Onboarding & Persona Selection
1. Navigate to the Visitor Experience portal (`/visit`).
2. Select your visitor persona from the onboarding dialog:
   - **Prospective Student / Undergraduate:** Highlights student projects, workstation access, and hands-on learning resources.
   - **Academic / Faculty Visitor:** Prioritizes compute infrastructure, research equipment, and curriculum integration.
   - **Industry Executive / Partner:** Emphasizes high-performance computing capabilities, patentable innovations, and industry collaboration.
   - **Research Scientist / Fellow:** Focuses on DGX Station specs, Slurm allocation policies, and edge AI testbeds.
   - **Accreditation / Compliance Reviewer:** Centers on lab safety protocols, equipment calibration records, and verification status.
3. Choose your primary visit objective and available time budget (**2 minutes**, **5 minutes**, or **15 minutes**).
4. Review the **Analytics Privacy Notice** and toggle consent for anonymized visit analytics.

### 1.2 Interactive 3D Scene Navigation
- **Rotate / Orbit:** Click and drag the left mouse button (or swipe on touch displays) to orbit the laboratory camera.
- **Pan:** Right-click and drag (or two-finger drag) to pan across laboratory zones.
- **Zoom:** Use the mouse scroll wheel (or pinch-to-zoom) to inspect equipment details.
- **Hotspot Inspection:** Click on glowing equipment beacons to highlight the asset, inspect manufacturer specifications, view verified photos, and filter relevant assistant knowledge.
- *Note:* The 3D geometry is explicitly marked as illustrative pending an on-site photogrammetric mesh survey.

### 1.3 Conversational Assistant (Text & Voice)
- Type questions into the chat bar or click the **Microphone** icon to use browser-supported voice input (Web Speech API).
- Select between **English** and **Hindi (हिन्दी)** language modes.
- Every response from LabSPOC AI is verified by the **Evidence Gate**:
  - Statements citing approved documents display bracketed citations `[1]`, `[2]` linking directly to verified manuals or SOPs.
  - If a requested detail (e.g., pricing, out-of-scope hardware, speculative benchmarks) is unverified in approved records, the assistant abstains honestly.

### 1.4 Agenda-to-Tour Execution
- Click **"Compile Tour"** to generate a sequenced itinerary tailored to your persona and selected time limit.
- Click **"Next Stop"** or **"Previous Stop"** to guide the 3D camera to each verified laboratory zone and highlighted asset.

### 1.5 Session Summary Export
- Click **"Finish Visit"** or **"Export Summary"** to generate a transparent record of visited hotspots, compiled itinerary stops, and questions asked during the session.

---

## Part 2: Administrator & Operator Manual (`/`)

The Operations & Administration Workspace is designed for laboratory technicians, faculty in-charge, and lab administrators managing assets, knowledge documents, and student projects.

### 2.1 Administrator Authentication & RBAC
1. Click **"Admin Access"** on the operations workspace.
2. Enter your credentials to acquire an authenticated HS256 JWT bearer token.
3. Roles are strictly enforced:
   - **`admin`**: Full authority to create/edit/delete zones, manage users, approve documents/projects, and inspect audit logs.
   - **`editor`**: Authority to register equipment, upload documents, and approve submissions.
   - **`viewer`**: Read-only inspection privileges across the operations dashboard.

### 2.2 Zone Configuration & Geometry Editor
- **View Zones:** Inspect all mapped laboratory zones (Server Rack Bay, Edge AI Bench, High-Performance Workstation Cluster, VR/CV Testing Area).
- **Edit Coordinates:** Adjust zone placement `(x, z)` and footprint `(width, depth)` directly from the UI.
- Changes are instantly persisted to `lab_zones` and reflected in the 3D scene with audit logging.

### 2.3 Equipment Hotspot Registration & Verification
- **Asset Registration:** Register laboratory equipment with persistent UUIDs, model numbers, manufacturer, and spatial zone association.
- **Verification Workflow:** Mark equipment as formally verified with a single click. Verified assets display a green verified badge and are prioritized in visitor tours.
- **Visual Evidence Upload:** Upload JPEG/PNG/WebP photographs of physical equipment. The backend verifies magic binary headers to ensure valid image payloads.

### 2.4 Document Governance & RAG Ingestion Pipeline
1. Navigate to the **Knowledge Management** tab.
2. Upload laboratory manuals, standard operating procedures (SOPs), or equipment data sheets (`.pdf`, `.docx`, `.txt`, `.md`).
3. Uploaded documents enter the **`pending_review`** queue.
4. **Administrative Review:** Inspect extracted text chunks and chunk counts.
5. Click **"Approve Document"** to promote the file to `approved` status:
   - Triggers the generation of 3072-dimensional vector embeddings via `gemini-embedding-001`.
   - Embeddings are persisted in the `chunk_vectors` table.
   - Document immediately becomes active in hybrid semantic/lexical search.

### 2.5 Student & Faculty Project Showcase Review
- Review student and faculty innovations submitted via the public submission portal.
- Review problem statement, methodology, technology stack, and demonstration links.
- Click **"Approve Project"** to publish the project to the public demonstrator showcase and link it within the Spatially Anchored Evidence Graph (SAEG).

### 2.6 Spatially Anchored Evidence Graph (SAEG) Explorer
- Navigate to the **SAEG Graph** tab to visualize relational connections between:
  - Physical Zones ↔ Equipment Assets ↔ Approved Documents ↔ Research Projects.
- Verify that every piece of high-value equipment is linked to verified operating procedures and approved demonstration projects.

### 2.7 Consent-Aware Analytics & FAQ Topic Clusters
- Review anonymized visitor session analytics (visitor personas, average dwell time, hotspot engagement rates).
- Inspect automatically clustered frequently asked question topics to identify areas where laboratory documentation should be expanded.
