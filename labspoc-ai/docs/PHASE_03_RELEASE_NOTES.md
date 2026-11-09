# LabSPOC AI — Phase 03 Release Notes

**Release:** 0.3.0 — Spatial & Equipment Intelligence Foundation  
**Target event:** SparkX 3.0 Beyond Boundaries — 30-Day AI Innovation Challenge  
**Challenge domain:** Domain 03, Smart Campus & Digital Twin  
**Project:** AI-Powered Intelligent Lab SPOC (Virtual Lab Ambassador)  
**Configured pilot:** AI & ML Laboratory, Oriental Institute of Science & Technology, Bhopal

## Challenge alignment

The official SparkX 3.0 page identifies this project as Domain 03, Smart Campus & Digital Twin. Its five functional areas are: AI virtual lab guide, conversational lab assistant, RAG-based lab knowledge system, AI project demonstrator, and visitor interaction/analytics with adaptive presentations. Phase 03 prioritizes the physical/spatial evidence foundation needed to make the virtual guide credible: zones, equipment identities, and photo records linked to equipment.

## Added

- `LabZone` persistent entity with verification state, floor, description and display order.
- `AssetPhoto` persistent entity linked to a registered equipment asset.
- Admin-protected zone create and verify endpoints.
- Admin-protected equipment image upload endpoint for JPG/PNG/WebP, configured upload size limit, signature checks, deduplication and captions.
- Static media delivery from `/media`.
- Release documentation and real-data onboarding workflow.

## API

| Method | Route | Purpose | Access |
|---|---|---|---|
| GET | `/api/zones` | List lab zones | Public |
| POST | `/api/zones` | Create zone | Admin key |
| POST | `/api/zones/{zone_id}/verify` | Verify zone | Admin key |
| GET | `/api/assets/{asset_id}/photos` | List equipment photos | Public |
| POST | `/api/assets/{asset_id}/photos` | Upload equipment photo | Admin key |
| GET | `/media/{stored_filename}` | Retrieve stored photo | Public |

## Evidence and honesty boundaries

- No real lab photographs or equipment specifications were supplied with this release.
- No equipment records are seeded; operators must register verified equipment.
- The current Three.js room is still illustrative and is not a dimensionally accurate digital twin.
- Photo file signatures are checked, but production deployment should add malware scanning, image decoding/re-encoding, EXIF stripping, private storage controls, and a formal retention policy.
- Public `/media` is appropriate only for images approved for public display. Restricted imagery requires authenticated private-object delivery.
- No claims are made about live sensors, GPU inventory, calibration status, or actual laboratory capabilities until evidence is entered and verified.

## Validation

- Python compilation: passed in the build environment.
- API automated tests: 5 passed in the build environment.
- Frontend npm build: not executed in this environment.
- Gemini live inference: requires the participant's API key and runtime smoke test.
- Deployment: not yet verified on a public host.

## Next steps

1. Perform a physical lab walkthrough and create the zone inventory.
2. Register each actual workstation/device with a stable ID and verified details.
3. Photograph wide views and equipment close-ups; remove/obscure personal and restricted information.
4. Upload source documents and record owner, version and review date.
5. Map real zone and asset IDs to surveyed 3D coordinates; replace illustrative scene geometry.
6. Run an end-to-end demo with a visitor persona, a grounded equipment question, a 2/5/15-minute tour, and consent-aware analytics.
