# SpurLine v0.2.0

## New: Extract profiles from existing gears

Select one or more gear objects already in your FreeCAD document — from the
FCGear workbench, imported STEP files, or any Part with a 3D shape — and
extract 2D cutting profiles directly.

- **Extract Profile from Selection** toolbar button and menu entry
- Per-object copy count and optional bore/keyway override
- Multi-face sheet layout (each gear type on its own row)
- Handles gears at arbitrary positions: slices at the shape's Z midpoint
  and re-centers the profile at the origin
- Preserves internal features (bore holes, offset holes) from the 3D model
- Preview objects are automatically removed when the panel is closed

## Automatic connection pairing

SpurLine now identifies itself as `"FreeCAD (SpurLine)"` and requests
access via `POST /api/connect` on the local REST API.  No manual URL or
secret entry is needed — a consent dialog appears in LightBurn / MillMage
on first use, and approved connections are remembered across sessions.

- Shared secrets are obtained and stored transparently
- Stale secrets are automatically refreshed on auth failure
- **SpurLine > Reset authorizations** menu entry to clear stored secrets

## Bug fixes and improvements

- Fixed timing gear creation: property is `type` (not `belt_type`), values
  are lowercase (`gt2`, `gt3`, `gt5`, `gt8`, `htd3`, `htd5`, `htd8`)
- Profile extraction uses `Shape.slice()` instead of boolean `section()`
  with a helper plane — significantly faster for complex shapes
- Holes are composited via `Part::FaceMakerBullseye` in a single pass,
  with a boolean-cut fallback

## Dependencies

- FreeCAD 1.0 or 1.1
- [freecad.gears](https://github.com/looooo/freecad.gears) addon
- Python stdlib only (no pip packages required)
