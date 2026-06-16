# SpurLine v0.4.0

## Interactive cutting plane

The "Extract Profile from Selection" panel now shows a visible, semi-transparent
cutting plane on the selected objects.  Controls in the panel let you position
it without leaving the task panel:

- **Top / Front / Right** preset buttons switch the plane orientation
- **Offset slider** drags the plane along its normal axis
- The plane is sized and centered automatically to the combined bounding box
  of all selected objects
- Supports objects inside containers (App::Part, PartDesign::Body) via
  global placement transforms

## Multi-slice export

A new **Multi-Slice** tab sends cross-sections at regular intervals as
separate DXF uploads:

- **Fixed distance** mode: set mm spacing between slices
- **Slice count** mode: set the number of evenly-spaced slices
- Per-slice progress feedback during upload
- Slice offsets are inset by 0.01 mm from bounding box faces to avoid
  tangent-plane failures

## Arbitrary-plane slicing

The extraction engine now supports slicing at any position and orientation,
not just the Z midpoint.  The shape is transformed into the cutting plane's
local coordinate system and sliced at Z=0, reusing the fast native
`Shape.slice()` path.

## Bug fixes

- Fixed objects inside containers (App::Part, PartDesign::Body) not aligning
  with the cutting plane — now uses `getGlobalPlacement()` for bounding box
  computation and shape extraction
- Fixed repository URL in package.xml

## Dependencies

- FreeCAD 1.0 or 1.1
- [freecad.gears](https://github.com/looooo/freecad.gears) addon
- Python stdlib only (no pip packages required)
