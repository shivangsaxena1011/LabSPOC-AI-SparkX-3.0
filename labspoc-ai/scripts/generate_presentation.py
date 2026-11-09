import sys
import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)  # 16:9 Widescreen

    # Color Palette: Deep Slate, Vibrant Cyan, Pure White, Light Slate, Emerald
    BG_COLOR = RGBColor(15, 23, 42)       # Slate 900
    CARD_BG = RGBColor(30, 41, 59)        # Slate 800
    TEXT_MAIN = RGBColor(248, 250, 252)   # Slate 50
    TEXT_MUTED = RGBColor(148, 163, 184)  # Slate 400
    ACCENT_CYAN = RGBColor(56, 189, 248)  # Sky 400
    ACCENT_BLUE = RGBColor(37, 99, 235)   # Blue 600
    ACCENT_GREEN = RGBColor(52, 211, 153) # Emerald 400

    def add_base_slide(title_text: str, category_text: str = "SPARKX 3.0 INTERNATIONAL INNOVATION CHALLENGE"):
        slide = prs.slides.add_slide(prs.slide_layouts[6]) # blank layout

        # Background
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.fill.background()

        # Header Category Pill
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = ACCENT_CYAN

        # Header Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.5), Inches(0.7))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_MAIN

        # Decorative line
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.45), Inches(11.733), Inches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = RGBColor(51, 65, 85)
        line.line.fill.background()

        # Footer
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.0), Inches(11.733), Inches(0.35))
        tf_f = footer_box.text_frame
        p_f = tf_f.paragraphs[0]
        p_f.text = "LabSPOC AI · OIST Bhopal AI & ML Laboratory · Galgotias University SPARKX 3.0 · Candidate: Shivang Saxena"
        p_f.font.size = Pt(9)
        p_f.font.color.rgb = TEXT_MUTED

        return slide

    def add_card(slide, left, top, width, height, title, points, accent_color=ACCENT_CYAN):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = RGBColor(71, 85, 105)
        card.line.width = Pt(1)

        tb = slide.shapes.add_textbox(Inches(left + 0.25), Inches(top + 0.2), Inches(width - 0.5), Inches(height - 0.4))
        tf = tb.text_frame
        tf.word_wrap = True

        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(15)
        p_t.font.bold = True
        p_t.font.color.rgb = accent_color
        p_t.space_after = Pt(12)

        for pt in points:
            p = tf.add_paragraph()
            p.text = f"•  {pt}"
            p.font.size = Pt(11)
            p.font.color.rgb = TEXT_MAIN
            p.space_after = Pt(8)

    # -------------------------------------------------------------
    # SLIDE 1: Title Slide
    # -------------------------------------------------------------
    slide1 = prs.slides.add_slide(prs.slide_layouts[6])
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = BG_COLOR
    bg1.line.fill.background()

    tb1 = slide1.shapes.add_textbox(Inches(1.0), Inches(1.2), Inches(11.333), Inches(5.0))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "GALGOTIAS UNIVERSITY — SPARKX 3.0 INTERNATIONAL"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p.space_after = Pt(14)

    p2 = tf1.add_paragraph()
    p2.text = "LabSPOC AI"
    p2.font.size = Pt(44)
    p2.font.bold = True
    p2.font.color.rgb = TEXT_MAIN
    p2.space_after = Pt(4)

    p3 = tf1.add_paragraph()
    p3.text = "Spatially Grounded Virtual Lab Ambassador & Intelligence Platform"
    p3.font.size = Pt(20)
    p3.font.bold = True
    p3.font.color.rgb = ACCENT_CYAN
    p3.space_after = Pt(28)

    p4 = tf1.add_paragraph()
    p4.text = "Track: Smart Campus & Digital Twin — AI-Powered Intelligent Lab SPOC\n" \
              "Host Institution: Oriental Institute of Science & Technology (OIST), Bhopal\n" \
              "Target Laboratory: AI & ML Laboratory (High-Performance Computing & Edge AI)\n" \
              "Project Lead & Presenter: Shivang Saxena (Individual Submission)\n" \
              "Preferred AI Provider: Google Gemini (2.5 Flash & Embedding-001)"
    p4.font.size = Pt(13)
    p4.font.color.rgb = TEXT_MUTED

    slide1.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 1):\n"
        "Welcome judges and organizers to the SPARKX 3.0 International 30-Day Innovation Challenge. "
        "I am Shivang Saxena from OIST Bhopal presenting LabSPOC AI. "
        "This project reimagines institutional laboratory intelligence by combining a 3D digital twin, "
        "hybrid RAG, and an automated Evidence Gate powered by Google Gemini."
    )

    # -------------------------------------------------------------
    # SLIDE 2: Problem Statement & Institutional Context
    # -------------------------------------------------------------
    slide2 = add_base_slide("Problem Statement: The Institutional Knowledge Disconnect")
    add_card(slide2, 0.8, 1.7, 3.6, 5.0, "High-Value Infrastructure", [
        "University AI/ML labs house expensive compute (NVIDIA DGX, Jetson clusters, VR bays).",
        "Physical facilities represent massive capital investments for academic institutions.",
        "Equipment capabilities, power constraints, and safety SOPs remain siloed in paper binders."
    ])
    add_card(slide2, 4.8, 1.7, 3.6, 5.0, "The Visitor Engagement Gap", [
        "Prospective researchers, accreditation teams (NBA/NAAC), and industry executives tour labs without specialized guides.",
        "Generic human tours miss critical technical specifications and student research outcomes.",
        "Manual tour coordination places excessive administrative burdens on faculty in-charge."
    ])
    add_card(slide2, 8.8, 1.7, 3.6, 5.0, "The Hallucination Danger", [
        "Generic chatbot solutions frequently hallucinate hardware specs, licensing, and safety protocols.",
        "Unverified AI answers create legal, safety, and institutional compliance liabilities.",
        "Institutions require 100% evidence-grounded AI that abstains when facts are unverified."
    ], accent_color=ACCENT_GREEN)

    slide2.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 2):\n"
        "Modern university labs represent critical research investments. However, knowledge remains trapped in manuals, "
        "and human guides are not always on-call. When institutions deploy generic conversational bots, they risk hallucinations "
        "on safety procedures or hardware specs. We need an ambassador anchored directly to physical space and verified evidence."
    )

    # -------------------------------------------------------------
    # SLIDE 3: Target Users & Personas
    # -------------------------------------------------------------
    slide3 = add_base_slide("Target Users: Persona-Tailored Spatial Intelligence")
    add_card(slide3, 0.8, 1.7, 2.7, 5.0, "Undergraduate Scholars", [
        "Objective: Explore research opportunities & workstation access.",
        "Needs: Lab access policies, prerequisite safety orientation, ongoing student projects.",
        "Tour Priority: Edge AI Workbench, VR Testing Bay, Student Capstones."
    ])
    add_card(slide3, 3.8, 1.7, 2.7, 5.0, "Research Scientists", [
        "Objective: High-performance compute & model training.",
        "Needs: DGX Station A100 specs, Slurm queue limits, memory bounds.",
        "Tour Priority: Compute Bay, GPU scheduling, publication links."
    ])
    add_card(slide3, 6.8, 1.7, 2.7, 5.0, "Industry Executives", [
        "Objective: Technology partnerships & sponsored R&D.",
        "Needs: Applied demonstration outcomes, patentable IP, cluster capacity.",
        "Tour Priority: High-impact demonstrator capstones, faculty contact."
    ])
    add_card(slide3, 9.8, 1.7, 2.7, 5.0, "Accreditation Teams", [
        "Objective: Compliance audit & safety verification.",
        "Needs: Verification badges, equipment inspection logs, emergency EPO locations.",
        "Tour Priority: Safety SOPs, calibration logs, verified assets."
    ], accent_color=ACCENT_GREEN)

    slide3.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 3):\n"
        "A key innovation is persona-driven intelligence. A researcher wants Slurm queue rules and GPU memory, "
        "while an accreditation reviewer wants safety SOPs and maintenance logs. LabSPOC AI tailors the experience "
        "to five distinct personas with exact time budgets."
    )

    # -------------------------------------------------------------
    # SLIDE 4: Existing Approaches & Research Gap
    # -------------------------------------------------------------
    slide4 = add_base_slide("Literature Review & The Architectural Research Gap")
    add_card(slide4, 0.8, 1.7, 5.6, 5.0, "Existing Paradigms in Academia", [
        "Static Web Showcases: Institutional websites provide static HTML bullet points with no interactive 3D embodiment or Q&A.",
        "Generic Virtual Tours: Matterport or 360-photo tours offer passive panoramic viewing with zero semantic query intelligence.",
        "Generic LLM Chatbots: Ungrounded bots hallucinate institutional policies, invent equipment specs, and lack spatial grounding.",
        "Standalone RAG Systems: Retrieve textual documents but have no concept of physical space, room coordinates, or visitor agendas."
    ])
    add_card(slide4, 6.8, 1.7, 5.6, 5.0, "The LabSPOC AI Integration Contribution", [
        "Spatial-Semantic Triangulation: Anchoring vector retrieval to physical 3D zone coordinates and equipment persistent IDs.",
        "Evidence Gate Enforcement: Intercepting LLM generations to validate citation indices against retrieved chunks with mandatory abstention.",
        "Dynamic Agenda Compilation: Optimizing visitor itineraries based on time budget (2, 5, 15 min), persona affinity, and verified assets.",
        "Demonstrated Project Synergy: Linking approved student and faculty capstones directly to the equipment used to build them."
    ], accent_color=ACCENT_GREEN)

    slide4.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 4):\n"
        "Existing systems exist in silos: 360-degree tours have no intelligence, and chatbots have no spatial awareness. "
        "Our core research contribution is the tight integration of physical space, verified evidence, and time-budgeted agendas."
    )

    # -------------------------------------------------------------
    # SLIDE 5: Proposed Solution
    # -------------------------------------------------------------
    slide5 = add_base_slide("Proposed Solution: LabSPOC AI Core Architecture")
    add_card(slide5, 0.8, 1.7, 3.6, 5.0, "Interactive 3D Digital Twin", [
        "Three.js / React Three Fiber floor plan.",
        "Configurable spatial zones (x, z, width, depth).",
        "Database-backed equipment hotspots with live specs.",
        "Transparent illustrative boundary labeling.",
        "Smooth orbit, pan, and zoom controls."
    ])
    add_card(slide5, 4.8, 1.7, 3.6, 5.0, "Evidence-Grounded RAG", [
        "Two-stage document governance (Review -> Approved).",
        "Google Gemini 3072-dimensional vector embeddings.",
        "Eager-joined hybrid semantic and lexical retrieval.",
        "Evidence Gate citation index verification.",
        "Safe extractive fallback on ungrounded queries."
    ], accent_color=ACCENT_GREEN)
    add_card(slide5, 8.8, 1.7, 3.6, 5.0, "Institutional Intelligence", [
        "Agenda-to-Tour Compiler (2, 5, 15 min routing).",
        "Multilingual dialogue (English & Hindi) with voice.",
        "Spatially Anchored Evidence Graph (SAEG).",
        "Public Project Demonstrator review workflow.",
        "Consent-aware visitor analytics & FAQ clusters."
    ])

    slide5.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 5):\n"
        "Here is the high-level solution architecture. It bridges three pillars: an interactive 3D digital twin, "
        "a rigorous evidence-grounded RAG pipeline with Google Gemini, and institutional operations tools for lab administrators."
    )

    # -------------------------------------------------------------
    # SLIDE 6: System Architecture Flow
    # -------------------------------------------------------------
    slide6 = add_base_slide("System Architecture & End-to-End Data Flow")
    add_card(slide6, 0.8, 1.7, 11.6, 5.0, "Architectural Pipeline (Stateless Frontend -> Resilient Backend -> AI & Storage)", [
        "1. Presentation Layer: Next.js 14 + React 18 + Tailwind CSS + Three.js / React Three Fiber with client-side Web Speech API.",
        "2. API Gateway & Security: FastAPI 0.115 + Uvicorn with correlation tracking (X-Request-ID), sliding-window rate limiting, and security headers.",
        "3. Identity & Access: PBKDF2-HMAC-SHA256 password hashing + HS256 JWT tokens + three-tier RBAC (admin, editor, viewer).",
        "4. Knowledge Engine: PDF/DOCX/TXT parser -> chunking (1000 chars, 150 overlap) -> Gemini Embeddings (3072 dims) -> SQLite/Postgres persistence.",
        "5. Evidence Gate: Evaluates model citations -> validates bounds -> enforces honest abstention if evidence is insufficient.",
        "6. Storage Layer: Swappable StorageAdapter supporting local storage and Cloudflare R2 / AWS S3 object stores with path traversal protection."
    ], accent_color=ACCENT_CYAN)

    slide6.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 6):\n"
        "Our architecture enforces clean separation of concerns. The frontend is fully statically optimized. "
        "The backend is asynchronous and stateless, with request correlation IDs and an S3-compatible storage adapter for cloud resilience."
    )

    # -------------------------------------------------------------
    # SLIDE 7: Signature Innovation A - SAEG
    # -------------------------------------------------------------
    slide7 = add_base_slide("Signature Innovation A: Spatially Anchored Evidence Graph (SAEG)")
    add_card(slide7, 0.8, 1.7, 5.6, 5.0, "Relational Graph Topology", [
        "LabZone (Spatial Coordinates: x, z, width, depth)",
        "  └── contains ──> Asset (Persistent UUID, Model, Specs)",
        "                     ├── supported_by ──> Document (SOP, Manual)",
        "                     └── demonstrated_in ──> Approved Project",
        "Endpoints: /api/graph/overview & /api/graph/links",
        "Eliminates isolated hardware records; every asset is connected to verified documentation and real capstones."
    ])
    add_card(slide7, 6.8, 1.7, 5.6, 5.0, "Institutional Value", [
        "Accreditation Traceability: Instant proof of calibration, safety compliance, and verified equipment operating procedures.",
        "Demonstrated Utility: Proves research ROI by showing exactly which publications and student capstones utilized each GPU cluster.",
        "Fast Relational Traversals: Built with SQLAlchemy foreign keys and optimized indexes (idx_asset_doc_asset, idx_asset_proj_asset).",
        "Verified Integrity: Enforced cascade deletions and zero orphan vectors."
    ], accent_color=ACCENT_GREEN)

    slide7.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 7):\n"
        "Our first signature innovation is SAEG. Instead of a separate graph database, we built an optimized relational graph "
        "linking zones, assets, documents, and projects. It provides instant traceability for accreditation reviewers."
    )

    # -------------------------------------------------------------
    # SLIDE 8: Signature Innovation B - Tour Compiler
    # -------------------------------------------------------------
    slide8 = add_base_slide("Signature Innovation B: Agenda-to-Tour Compiler")
    add_card(slide8, 0.8, 1.7, 5.6, 5.0, "Route Optimization Engine", [
        "Inputs: Visitor Persona + Interest Objectives + Time Limit (2, 5, or 15 minutes).",
        "Persona Affinity Weighting: Research scientists prioritize compute clusters; students prioritize workstation bays and projects.",
        "Strict Time Budgeting: Dynamic transit buffers and stop dwell allocations guarantee tour finishes within the selected time window:",
        "    t_stop * N + t_transit * (N - 1) <= T_budget",
        "Verified Stops Only: Unverified assets or pending documents are strictly excluded from generated itineraries."
    ])
    add_card(slide8, 6.8, 1.7, 5.6, 5.0, "Visitor Experience Impact", [
        "2-Minute Executive Briefing: High-speed snapshot of top laboratory compute assets and flagship student outcomes.",
        "5-Minute Standard Tour: Balanced overview covering all major lab zones with technical highlights.",
        "15-Minute Deep Dive: Comprehensive walkthrough with equipment specifications, project demonstrations, and SOP details.",
        "Interactive 3D Guidance: Camera smoothly animates to each stop as the visitor progresses through the tour."
    ], accent_color=ACCENT_GREEN)

    slide8.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 8):\n"
        "Our second signature innovation is the Agenda-to-Tour Compiler. Visitors rarely have unlimited time. "
        "Our compiler generates tailored itineraries respecting strict 2, 5, or 15-minute limits using persona affinity weighting."
    )

    # -------------------------------------------------------------
    # SLIDE 9: Signature Innovation C - Evidence Gate
    # -------------------------------------------------------------
    slide9 = add_base_slide("Signature Innovation C: Evidence Gate & Grounded RAG")
    add_card(slide9, 0.8, 1.7, 5.6, 5.0, "The Evidence Gate Mechanism", [
        "Pre-Response Interception: Analyzes Gemini text completions before delivery to the visitor.",
        "Citation Index Bounds Check: Verifies all [1], [2] markers reference genuine retrieved chunk IDs.",
        "Uncited Assertion Rejection: Detects factual claims made without evidence or abstention phrasing.",
        "Honest Abstention Protocol: If retrieved evidence is inadequate or query is out-of-scope, the gate triggers explicit abstention.",
        "No Hallucinated Specs: The model explicitly refuses to invent prices, serial numbers, or safety protocols."
    ])
    add_card(slide9, 6.8, 1.7, 5.6, 5.0, "Benchmark Evaluation Results", [
        "Tested across 10 structured benchmark queries (7 grounded, 3 ungrounded/bait):",
        "•  Recall@5: 100.0% (All relevant evidence retrieved in top 5)",
        "•  Mean Reciprocal Rank (MRR): 1.0000 (Top evidence ranked at #1)",
        "•  Citation Validity Rate: 85.7% (Strict bracket matching)",
        "•  Correct Abstention Rate: 100.0% (Zero hallucinations on out-of-scope queries)",
        "•  Mean Retrieval Latency: 1723.4 ms (Includes live vector call)",
        "•  Mean Gemini Generation Latency: 3028.0 ms (Live gemini-2.5-flash)"
    ], accent_color=ACCENT_GREEN)

    slide9.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 9):\n"
        "Our third innovation is the Evidence Gate. In university administration, wrong information is dangerous. "
        "Our Evidence Gate achieved 100% correct abstention on out-of-scope queries during benchmark testing."
    )

    # -------------------------------------------------------------
    # SLIDE 10: The Five Core Challenge Modules
    # -------------------------------------------------------------
    slide10 = add_base_slide("Complete Delivery of the Five SPARKX 3.0 Modules")
    add_card(slide10, 0.8, 1.7, 2.2, 5.0, "M1: 3D Lab Guide", [
        "Three.js digital twin.",
        "Zone layout editor.",
        "Equipment hotspots.",
        "Verified badges.",
        "Photo evidence gallery."
    ])
    add_card(slide10, 3.2, 1.7, 2.2, 5.0, "M2: AI Assistant", [
        "Gemini 2.5 Flash.",
        "Multi-turn dialogue context.",
        "English & Hindi voice.",
        "Interactive citations.",
        "Evidence Gate."
    ])
    add_card(slide10, 5.6, 1.7, 2.2, 5.0, "M3: Knowledge RAG", [
        "PDF/DOCX/TXT parser.",
        "Approval workflow.",
        "3072-dim embeddings.",
        "Hybrid retrieval.",
        "Recall & MRR harness."
    ])
    add_card(slide10, 8.0, 1.7, 2.2, 5.0, "M4: Demonstrator", [
        "Public project portal.",
        "Admin approval queue.",
        "Methodology & stack.",
        "Live URL links.",
        "SAEG graph integration."
    ])
    add_card(slide10, 10.4, 1.7, 2.2, 5.0, "M5: Analytics", [
        "Persona onboarding.",
        "2/5/15 min tour compiler.",
        "Consent-aware tracking.",
        "FAQ topic clustering.",
        "Session summary export."
    ], accent_color=ACCENT_GREEN)

    slide10.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 10):\n"
        "We have achieved 100% completion across all five challenge modules. None of these are mockups: "
        "every module is backed by live database models, API routes, and frontend components."
    )

    # -------------------------------------------------------------
    # SLIDE 11: Technology Stack & Engineering
    # -------------------------------------------------------------
    slide11 = add_base_slide("Full-Stack Engineering & Production Standards")
    add_card(slide11, 0.8, 1.7, 3.6, 5.0, "Frontend Stack", [
        "Next.js 14.2 (App Router, Static Prerendering).",
        "React 18 + TypeScript (Strict typing).",
        "Tailwind CSS (Responsive slate design system).",
        "Three.js / React Three Fiber (3D WebGL scenes).",
        "Lucide React Icons + W3C Web Speech API."
    ])
    add_card(slide11, 4.8, 1.7, 3.6, 5.0, "Backend Stack", [
        "Python 3.12 + FastAPI 0.115 (Async ASGI).",
        "SQLAlchemy 2.0 (Mapped models & expressions).",
        "Pytest 8.3 + Starlette TestClient (40 tests).",
        "Boto3 (S3/Cloudflare R2 Object Storage adapter).",
        "PyPDF & Python-Docx (Multi-format parsers)."
    ])
    add_card(slide11, 8.8, 1.7, 3.6, 5.0, "Database & AI Stack", [
        "PostgreSQL 16 (Production via psycopg2).",
        "SQLite 3 (Development & Kiosk via WAL).",
        "Google Gemini 2.5 Flash (Grounded dialogue).",
        "Google Gemini Embedding-001 (3072 dims).",
        "Idempotent Additive Database Migrations."
    ], accent_color=ACCENT_GREEN)

    slide11.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 11):\n"
        "Our technology stack leverages enterprise-grade modern tools. Next.js 14 provides static optimization, "
        "FastAPI provides sub-millisecond asynchronous routing, and PostgreSQL/SQLite provides dual-engine flexibility."
    )

    # -------------------------------------------------------------
    # SLIDE 12: Live Application Screenshots & Walkthrough
    # -------------------------------------------------------------
    slide12 = add_base_slide("Live Application Walkthrough: Operations & Visitor Portal")
    add_card(slide12, 0.8, 1.7, 5.6, 5.0, "Operations Workspace (http://localhost:3000)", [
        "Unified Administrator Dashboard: Real-time inventory cards for assets, projects, documents, and recorded sessions.",
        "Interactive 3D Zone Editor: Live slider adjustments for zone coordinates (x, z) and footprints (width, depth).",
        "Knowledge Ingestion Queue: Two-stage document review with chunk counts and instant vector indexing.",
        "Project Review Portal: Approve or reject student research submissions with HTML sanitization.",
        "System Observability: Authenticated telemetry via /api/admin/system/metrics."
    ])
    add_card(slide12, 6.8, 1.7, 5.6, 5.0, "Visitor Experience Portal (/visit)", [
        "Visitor Onboarding Dialog: Persona selection, time budgeting, and opt-in analytics consent notice.",
        "Interactive 3D Digital Twin: Orbit, pan, and zoom across zones; click beacons to focus equipment.",
        "Multilingual Voice Assistant: Seamless English and Hindi speech recognition and text-to-speech.",
        "Agenda-to-Tour Compiler: Guided camera progression across time-boxed stops with transit budgeting.",
        "Session Summary Export: Copyable report of visited stops, inspected assets, and answers."
    ], accent_color=ACCENT_GREEN)

    slide12.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 12):\n"
        "Here are the two core user interfaces: the Operations Workspace for laboratory managers, "
        "and the Visitor Experience portal for prospective researchers, students, and accreditation teams."
    )

    # -------------------------------------------------------------
    # SLIDE 13: Testing Methodology & Test Results
    # -------------------------------------------------------------
    slide13 = add_base_slide("Testing Methodology & Automated Verification")
    add_card(slide13, 0.8, 1.7, 5.6, 5.0, "Automated Test Suite (40/40 Passed)", [
        "Execution Time: 27.80 seconds (100% pass rate).",
        "Workflow Tests (WF-01 to WF-17): Verified admin login, RBAC hierarchy, zone editing, equipment verification, document approval, project submission, and SAEG graph links.",
        "Production Deployment Tests: Verified /api/ready, /api/health, X-Request-ID correlation headers, and StorageAdapter path traversal protections.",
        "Eager Retrieval Test: Verified elimination of N+1 database queries during vector search.",
        "Frontend Production Build: Clean Next.js compilation (Exit code 0) with zero TypeScript/lint errors."
    ])
    add_card(slide13, 6.8, 1.7, 5.6, 5.0, "RAG Evaluation Benchmark Table", [
        "Tested against 10 reference questions in docs/eval_dataset.json:",
        "•  Recall@5: 100.0% (Target: >= 90.0%) -> EXCEEDED",
        "•  MRR: 1.0000 (Target: >= 0.8500) -> EXCEEDED",
        "•  Citation Validity: 85.7% (Target: >= 80.0%) -> PASSED",
        "•  Correct Abstention: 100.0% (Target: 100.0%) -> PASSED",
        "•  Retrieval Latency: 1723.4 ms (Target: < 2500 ms) -> PASSED",
        "•  Gemini Latency: 3028.0 ms (Target: < 4500 ms) -> PASSED"
    ], accent_color=ACCENT_GREEN)

    slide13.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 13):\n"
        "We do not claim our system works without proof. We built an automated test suite of 40 tests, all passing, "
        "and ran a reproducible RAG evaluation benchmark achieving 100% Recall@5 and 100% correct abstention."
    )

    # -------------------------------------------------------------
    # SLIDE 14: Security Architecture & Privacy
    # -------------------------------------------------------------
    slide14 = add_base_slide("Security Architecture, RBAC & Privacy Governance")
    add_card(slide14, 0.8, 1.7, 5.6, 5.0, "Authentication & Defense-in-Depth", [
        "PBKDF2-HMAC-SHA256: 240,000 hash iterations with 16-byte random salts and constant-time comparison.",
        "HS256 JWT Bearer Tokens: 256-bit secret, 12h expiry, database active-user checks on every call.",
        "Three-Tier RBAC: admin (full mutation), editor (content upload/verify), viewer (read-only).",
        "Reverse-Proxy Rate Limiting: Sliding window inspecting X-Forwarded-For to protect against DoS.",
        "Input Sanitization: Regex HTML stripping on project submissions; magic binary header sniffing on image uploads."
    ])
    add_card(slide14, 6.8, 1.7, 5.6, 5.0, "Data Privacy & Governance (DPDP Act 2023)", [
        "Zero PII Collection: No names, phone numbers, email addresses, or biometric data stored from visitors.",
        "Opt-In Consent Gating: Interaction events dropped in-memory if consent toggle is disabled.",
        "Immutable Audit Logs: Append-only audit records tracking user, action, resource, and timestamp.",
        "Defensive Security Headers: nosniff, SAMEORIGIN, 1; mode=block, strict-origin-when-cross-origin."
    ], accent_color=ACCENT_GREEN)

    slide14.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 14):\n"
        "Security is central to LabSPOC AI. We implement NIST-compliant PBKDF2 password hashing, "
        "reverse-proxy rate limiting, magic-byte upload validation, and strict adherence to India's DPDP Act."
    )

    # -------------------------------------------------------------
    # SLIDE 15: Production Deployment & Cost Analysis
    # -------------------------------------------------------------
    slide15 = add_base_slide("Production Deployment Architecture & Cost Evaluation")
    add_card(slide15, 0.8, 1.7, 5.6, 5.0, "Sustainable Zero-Cost Student Budget Model", [
        "Frontend: Vercel (Edge CDN, 100 GB bandwidth/mo) -> $0.00 / month.",
        "Backend API: Render (Docker web service, 750 free hours/mo) -> $0.00 / month.",
        "Relational Database: Neon (Serverless Postgres 16, 0.5 GB storage) -> $0.00 / month.",
        "Object Storage: Cloudflare R2 (10 GB storage, zero egress fees) -> $0.00 / month.",
        "AI Reasoning: Google AI Studio (15 RPM free tier) -> $0.00 / month.",
        "TOTAL OPERATIONAL COST: $0.00 / month during evaluation."
    ])
    add_card(slide15, 6.8, 1.7, 5.6, 5.0, "Institutional Deployment Milestones", [
        "Milestone 1 (Complete): Cloud deployment configuration via Docker Compose & multi-stage Dockerfiles.",
        "Milestone 2 (Campus Pilot): Deploy interactive touch kiosk running LabSPOC AI at the AI & ML Lab entrance.",
        "Milestone 3 (Physical Digital Twin): Photogrammetric LiDAR scan of Room 302 to replace illustrative 3D geometry.",
        "Milestone 4 (Identity Federation): OIDC / SAML single sign-on with campus LDAP/Active Directory."
    ], accent_color=ACCENT_GREEN)

    slide15.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 15):\n"
        "We designed this deployment for sustainability. The entire stack fits within free tier limits of Vercel, "
        "Render, Neon, and Cloudflare R2, costing $0.00 per month while remaining scalable for full university adoption."
    )

    # -------------------------------------------------------------
    # SLIDE 16: Conclusion & Defense Q&A
    # -------------------------------------------------------------
    slide16 = add_base_slide("Conclusion: Transforming Laboratory Intelligence")
    add_card(slide16, 0.8, 1.7, 11.6, 5.0, "Summary of Accomplishments & Institutional Impact", [
        "•  Delivered a genuinely functional, secure, and deployable institutional digital twin platform for OIST Bhopal.",
        "•  Implemented all 5 Challenge Modules and 3 Signature Innovations without simulated mocks or fake APIs.",
        "•  Backed by 40 automated passing tests (100% pass rate) and benchmarked RAG evaluation (100% Recall@5, 1.0000 MRR).",
        "•  Honest engineering boundaries: Illustrative 3D geometry explicitly declared; zero hallucination tolerance via Evidence Gate.",
        "•  Ready for live juror evaluation, local kiosk demonstration, and cloud container deployment.",
        "\nThank you to the organizers of Galgotias University SPARKX 3.0 and faculty mentors at OIST Bhopal.",
        "I welcome questions from the jury."
    ], accent_color=ACCENT_CYAN)

    slide16.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 16):\n"
        "In conclusion, LabSPOC AI delivers an institutional-grade virtual ambassador that is verifiable, secure, "
        "and grounded in physical reality. Thank you for your time, and I am ready to answer your technical questions."
    )

    # Output path
    out_path = Path("submission/presentation/Shivang Saxena_LabSPOC AI — Spatially Grounded Virtual Lab Ambassador.pptx")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))
    print(f"Successfully generated 16-slide presentation: {out_path} ({out_path.stat().st_size} bytes)")

if __name__ == "__main__":
    create_deck()
