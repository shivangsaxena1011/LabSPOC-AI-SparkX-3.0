# LabSPOC AI — Phase 07 Release Notes

**Release:** 0.7.0  
**Challenge:** Galgotias University SparkX 3.0 — 30-Day Innovation Challenge  
**Track:** Smart Campus & Digital Twin / AI-Powered Intelligent Lab SPOC  
**Laboratory profile:** AI & ML Laboratory, OIST Bhopal

## Scope

Phase 07 advances the spatial digital-twin foundation. It is deliberately a **configurable illustrative floor plan**, not a photogrammetry-derived, surveyed, or sensor-connected digital twin. This is the honest approach while institutional photographs and a measured floor plan are unavailable.

## Implemented

- Persistent zone spatial coordinates (`x`, `z`, `width`, `depth`).
- Additive startup migration for existing `lab_zones` tables.
- `GET /api/spatial/scene` returns zones, associated assets, verification state, counts, and an explicit survey disclaimer.
- `PATCH /api/zones/{zone_id}/layout` lets an authorized administrator/editor update validated scene geometry.
- Interactive React Three Fiber floor-plan view with orbit/zoom, zone selection, equipment markers, verification colors, and asset counts.
- The scene consumes database records rather than a hard-coded list of lab equipment.
- Empty-state illustrative zones remain available so the visitor interface can be explored before real data is entered.

## API

### `GET /api/spatial/scene`

Public read endpoint. Returns `scene_type`, `is_surveyed`, `disclaimer`, and zones. Each zone includes spatial dimensions and associated asset summaries.

### `PATCH /api/zones/{zone_id}/layout`

Requires admin/editor authentication. Example body:

```json
{"x":-2.0,"z":1.5,"width":3.0,"depth":2.0}
```

Coordinates are bounded by schema validation to keep the model within the current scene bounds.

## Existing database compatibility

At API startup, missing spatial columns are added to the existing `lab_zones` table using an additive migration. Existing zone records receive safe default dimensions and coordinates. Back up production data before upgrades.

## Limitations and required institutional inputs

- Room geometry and coordinates are illustrative until measured and approved by OIST.
- No real photographs, 360-degree panoramas, CAD/BIM, point cloud, photogrammetry, or live IoT telemetry are included.
- Asset-zone association uses the existing asset `zone` field matching zone name or ID.
- The 3D view is a lightweight floor-plan visualization, not a physically accurate engineering model.
- Before public deployment, review the API security configuration, storage strategy, institutional authorization, and data retention policy.

## Verification

Automated tests cover the scene endpoint, explicit survey status, admin-protected layout updates, coordinate persistence, and authorization. Frontend dependency installation/build and browser-level 3D interaction still need to be verified in the target environment.
