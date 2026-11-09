# LabSPOC AI — Demonstration Video Plan & Recording Script

**Competition:** Galgotias University — SPARKX 3.0 International, 30-Day Innovation Challenge  
**Track:** Smart Campus & Digital Twin / AI-Powered Intelligent Lab SPOC  
**Project:** LabSPOC AI — Spatially Grounded Virtual Lab Ambassador  
**Institution:** Oriental Institute of Science & Technology (OIST), Bhopal  
**Target Laboratory:** AI & ML Laboratory  
**Presenter / Team Lead:** Shivang Saxena  
**Target Duration:** 5 minutes 45 seconds  
**Resolution:** 1080p (1920x1080, 60fps)  

---

## Timeline & Scene-by-Scene Director's Cut

### Scene 1: Introduction & Institutional Challenge (0:00 – 0:25)
- **On-Screen Display:** Title slide with SPARKX 3.0 branding, OIST Bhopal insignia, and project title.
- **Action:** Introduce the core problem: University laboratories house high-value AI compute (DGX Stations, edge clusters, VR testbeds), but institutional visitors, prospective researchers, and accreditation reviewers lack an intelligent, spatially aware, and evidence-grounded guide.
- **Visual Transition:** Cut to the browser showing the landing page at `http://localhost:3000`.

### Scene 2: Visitor Onboarding & Persona Selection (0:25 – 1:05)
- **On-Screen Display:** Navigate to `/visit`. The Visitor Onboarding modal appears.
- **Action:**
  1. Demonstrate selecting the **"Research Scientist / Fellow"** persona.
  2. Select the **"15 Minutes"** deep-dive time budget.
  3. Select primary interests: **"High-Performance Computing"** and **"Edge AI Embedded Systems"**.
  4. Highlight the **Analytics Consent Toggle**: show that privacy is opt-in, explaining our compliance with Indian DPDP Act principles.
  5. Click **"Begin Laboratory Experience"**.

### Scene 3: Interactive 3D Digital Twin Navigation (1:05 – 1:45)
- **On-Screen Display:** 3D Three.js / React Three Fiber laboratory scene renders smoothly with orbit controls.
- **Action:**
  1. Orbit the camera around the laboratory floor plan using left-click drag.
  2. Zoom into the **High-Performance Compute Bay** and **Edge AI Workbench**.
  3. Point out the clear badge: **"Illustrative Layout"** — explain our honest engineering boundary: room geometry is modeled to illustrative scale pending an on-site photogrammetric scan.
  4. Click on the glowing equipment beacon for the **NVIDIA DGX Station A100**.
  5. The camera transitions smoothly, highlighting the asset card with verified specifications (320GB GPU memory, 4x A100 GPUs).

### Scene 4: Conversational Assistant & Voice Interaction (1:45 – 2:35)
- **On-Screen Display:** The assistant panel on the right side of the visitor portal.
- **Action:**
  1. Click the **Microphone** button to demonstrate browser-native speech recognition in English:
     *"What are the power requirements and cooling guidelines for the DGX Station?"*
  2. Switch the language toggle to **Hindi (हिन्दी)** and demonstrate a multilingual query:
     *"इस प्रयोगशाला में कौन-कौन से रिसर्च प्रोजेक्ट चल रहे हैं?"*
  3. Show the instant response generated in clear Devanagari script.

### Scene 5: RAG Grounding, Citations & Evidence Gate (2:35 – 3:20)
- **On-Screen Display:** The assistant's answer output with bracketed citation markers `[1]`, `[2]`.
- **Action:**
  1. Highlight that every factual claim has an interactive citation pill linking directly to the approved SOP.
  2. Demonstrate the **Evidence Gate Abstention**: Ask an ungrounded / fabrication bait question:
     *"Can you tell me the cafeteria lunch menu and the serial number of the Quantum Annealer in Room 302?"*
  3. Show the assistant's clear, honest abstention:
     *"The requested information is not verified in approved laboratory documentation."*
  4. Explain the innovation: LabSPOC AI refuses to hallucinate specifications.

### Scene 6: AI Project Demonstrator Showcase (3:20 – 4:00)
- **On-Screen Display:** Scroll to the Approved Research Projects section on `/visit`.
- **Action:**
  1. Showcase verified student and faculty capstone projects:
     - Autonomous Agricultural Drone Weed Detection (Edge Jetson AGX Orin)
     - Brain MRI Segmentation using 3D U-Net (DGX A100)
  2. Show problem statement, methodology, tech stack, and demonstration GitHub links.
  3. Explain that projects are linked directly into the Spatially Anchored Evidence Graph.

### Scene 7: Agenda-to-Tour Compiler (4:00 – 4:40)
- **On-Screen Display:** Click **"Compile Tour Itinerary"**.
- **Action:**
  1. Demonstrate the compiler generating an optimal stop itinerary fitted exactly into the selected time budget.
  2. Click **"Next Stop"**: The 3D camera glides to Stop 1 (DGX Station A100), then Stop 2 (Jetson AGX Orin Workbench).
  3. Explain the transit budgeting algorithm: stops are prioritized by persona affinity and only include verified assets.

### Scene 8: Administrator Workspace & Visitor Analytics (4:40 – 5:15)
- **On-Screen Display:** Navigate to `/` (Operations Workspace) and authenticate.
- **Action:**
  1. Show the **3D Zone Layout Editor**: Adjust `(x, z, width, depth)` sliders and show real-time 3D updates.
  2. Show the **Knowledge Governance Queue**: Review an uploaded PDF and click **"Approve Document"** to trigger live 3072-dim Gemini embeddings.
  3. Show the **Visitor Analytics & FAQ Clusters**: Demonstrate consent-aware metrics and aggregated question clusters.

### Scene 9: Innovation Summary & Conclusion (5:15 – 5:45)
- **On-Screen Display:** Return to full camera / summary slide.
- **Action:** Summarize the core contributions: Spatially Anchored Evidence Graph, Agenda-to-Tour Compiler, and Evidence Gate. Conclude with thanks to Galgotias University SPARKX 3.0 organizers and faculty mentors at OIST Bhopal.
