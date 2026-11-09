# LabSPOC AI — Phase 04 Release Notes

**Release:** 0.4.0  
**Challenge context:** Galgotias University SparkX 3.0 — 30-Day Innovation Challenge  
**Track:** Smart Campus & Digital Twin / AI-Powered Intelligent Lab SPOC  
**Laboratory profile:** AI & ML Laboratory, Oriental Institute of Science & Technology, Bhopal

## Phase 04 focus: visitor experience, voice and consent-aware interaction

This release adds a visitor-facing route at `/visit`, separate from the laboratory operations workspace.

### Implemented

- Visitor onboarding for undergraduate students, academic visitors, industry executives, research scientists and accreditation reviewers.
- Visit agenda and 2-, 5- and 15-minute time budget selection.
- Language selection for English, Hindi, Bengali, Tamil, Telugu and Marathi.
- Browser speech recognition using the Web Speech API where supported by the browser; text input remains available as fallback.
- Browser text-to-speech using SpeechSynthesis where supported.
- Agenda-to-Tour integration using configured assets and approved projects only.
- Equipment-scoped and general questions through the existing evidence-constrained assistant.
- Approved-project showcase; empty state explains that real project records must be approved before publication.
- Explicit, optional analytics consent. Visitor events are discarded when consent is false.
- Event allowlist and per-visit summary endpoint.

### API additions

- `POST /api/visits/{visit_id}/events`
- `GET /api/visits/{visit_id}/summary`
- `TourRequest.session_id` optional field; tour generation records an event only for an existing opted-in session.

### Routes

- `GET /visit` — visitor-facing guided experience.
- `GET /` — operations workspace.

## Important limitations and honest demo notes

- No real laboratory photographs were provided. The product does not claim to show a photogrammetry-derived or surveyed digital twin. The existing 3D scene remains a conceptual/illustrative spatial interface pending a physical survey.
- The language selector controls the response language hint and browser speech locale. It does not guarantee translation quality, speech availability, or support for every accent/device. The knowledge base must contain approved material for each language if factual responses are expected in that language.
- Voice recognition and speech synthesis are browser-native capabilities, not a server-side speech service. Chrome/Edge support and microphone permission are required for recognition.
- The tour planner is a deterministic baseline over configured assets and approved projects; it is not an optimized indoor navigation engine.
- Visitor analytics are not identity analytics. The event endpoint only accepts an allowlist of coarse event types and stores them only when the visitor has opted in.
- No director email digest, institutional SSO, fine-grained RBAC, real-time sensors, or physical indoor positioning are implemented in this phase.
- Gemini must be configured with a valid API key for live generation. The API retains its evidence-only fallback behavior.

## Verification

Backend test suite: `python -m pytest -q` — 8 tests expected in this release.  
Frontend production build: must be run locally with `npm install` and `npm run build`; not claimed as verified by this release packaging step.

## SparkX judge demonstration flow

1. Open `/visit` and select visitor persona, agenda, duration and language.
2. Start a session with analytics consent either enabled or disabled.
3. Generate a tour. If no verified assets or approved projects exist, demonstrate the honest empty-state response instead of adding fabricated stops.
4. Ask a question for which approved evidence exists; then ask an unsupported question to demonstrate abstention.
5. Demonstrate browser voice input/output if the browser supports it.
6. Finish the visit and show the consent-aware summary.
7. In the operations workspace, show how administrators upload and approve institutional documents and register real equipment.

## Next phase priorities

- Institutional authentication and role-based authorization.
- Admin forms for creating/approving projects and equipment with source metadata.
- Better semantic retrieval, evaluation dataset and retrieval-quality metrics.
- Actual lab survey, verified floor plan and hotspot-to-asset mapping.
- Project media upload and director digest workflow.
