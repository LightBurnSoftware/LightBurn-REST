# SpurLine v0.3.0

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

SpurLine identifies itself as `"FreeCAD (SpurLine)"` and requests access
via `POST /api/connect` on the local REST API.  A consent dialog appears in
LightBurn / MillMage each time a new secret is needed; the secret is stored
in FreeCAD preferences for reuse across sessions.

- **SpurLine > Reset authorizations** clears stored secrets so the next
  send triggers a fresh consent prompt
- Auth errors are reported with guidance to reset and re-authorize
  (no automatic silent reconnect — each connect shows a consent dialog)

## Grouped shape import

Uploaded profiles are now sent with `X-Group-Shapes: true`, so all shapes
in a multi-copy layout arrive as a single group in LightBurn / MillMage.

## Progress feedback

The send pipeline now shows step-by-step status in the panel label
("Generating profile..." → "Exporting DXF..." → "Uploading to LightBurn...")
and displays FreeCAD's progress indicator in the status bar.

## Bug fixes

- Fixed timing gear creation: FCGear property is `type` (not `belt_type`),
  values are lowercase (`gt2`, `gt3`, `gt5`, `gt8`, `htd3`, `htd5`, `htd8`)
- Fixed gear profile corruption when an active PartDesign body exists —
  temporary gears are now created as standalone Part::FeaturePython objects,
  never added to the active body
- Profile extraction uses `Shape.slice()` instead of boolean `section()`
  with a helper plane — significantly faster for complex shapes
- Holes are composited via `Part::FaceMakerBullseye` in a single pass,
  with a boolean-cut fallback
- Fixed `clear_all_secrets` using `SetString("")` instead of `RemString`
  for reliable in-session clearing

## Dependencies

- FreeCAD 1.0 or 1.1
- [freecad.gears](https://github.com/looooo/freecad.gears) addon
- Python stdlib only (no pip packages required)
