# SpurLine

A FreeCAD workbench that generates 2D gear profiles and sends them
directly to **LightBurn** or **MillMage** for laser cutting or CNC milling.

## Supported gear types

| Type | FreeCAD gear | Notes |
|------|-------------|-------|
| Involute spur gear | `CreateInvoluteGear` | Bore + keyway support |
| Involute rack | `CreateInvoluteRack` | Linear, no bore |
| Timing belt pulley | `CreateTimingGear` | gt2, gt3, gt5, gt8, htd3, htd5, htd8 |

## Requirements

- FreeCAD 1.0+
- The **FCGear** (freecad.gears) addon — install via Tools → Addon Manager

## Installation (development)

Symlink this folder into FreeCAD's user `Mod/` directory so edits take
effect on the next FreeCAD restart without copying files:

**Linux / macOS**
```bash
ln -s /path/to/lightburn-rest/examples/spurline ~/.local/share/FreeCAD/Mod/SpurLine
```

**Windows** (run as Administrator in PowerShell)
```powershell
New-Item -ItemType SymbolicLink `
  -Path "$env:APPDATA\FreeCAD\v1-1\Mod\SpurLine" `
  -Target "C:\path\to\lightburn-rest\examples\spurline"
```

> SpurLine lives under `examples/` in the `lightburn-rest` monorepo, so it
> installs by symlink (above) rather than via the FreeCAD Addon Manager.

Then restart FreeCAD and select **SpurLine** from the workbench dropdown.

## Configuration

No manual configuration is required.  When you click **Send to LightBurn**
or **Send to MillMage** for the first time, SpurLine identifies itself as
`"FreeCAD (SpurLine)"` and requests access via the local REST API.  A
consent dialog appears in LightBurn / MillMage — approve it and the
shared secret is stored in FreeCAD's preferences for future sends.

Each call to `/api/connect` produces a new consent prompt and a distinct
secret.  If your stored secret becomes invalid (e.g. the server was
reinstalled), use **SpurLine > Reset authorizations** from the menu to
clear it, then click Send again to re-authorize.

The default port is **19522**.  If LightBurn or MillMage is configured to
listen on a different port, use **SpurLine > Set port...** to change it.

## Project structure

The REST API spec lives at the repo root in [`docs/openapi.yaml`](../../docs/openapi.yaml).

```
examples/spurline/
├── InitGui.py                          ← FreeCAD workbench entry point
├── Init.py                             ← Headless init (no-op)
├── package.xml                         ← Addon metadata
├── freecad/spurline/
│   ├── commands/
│   │   ├── cmd_involute.py             ← Toolbar command: involute gear
│   │   ├── cmd_rack.py                 ← Toolbar command: rack
│   │   ├── cmd_timing.py              ← Toolbar command: timing pulley
│   │   ├── cmd_extract.py             ← Toolbar command: extract from selection
│   │   ├── cmd_port.py                ← Menu command: set port
│   │   └── cmd_settings.py            ← Menu command: reset authorizations
│   ├── ui/
│   │   ├── gear_panel.py              ← Task panel for gear creation
│   │   └── extract_panel.py           ← Task panel for profile extraction
│   ├── core/
│   │   ├── profile_extractor.py       ← Create gear → 2D Part.Face
│   │   ├── selection_extractor.py     ← Existing shape → 2D Part.Face
│   │   └── sheet_composer.py          ← Grid layout + DXF/SVG export
│   ├── api/
│   │   └── client.py                  ← REST client (connect + file upload)
│   └── prefs/
│       └── preferences.py             ← Port + shared secret storage
└── resources/icons/                    ← Toolbar SVG icons
```

## Typical workflow

### Create a new gear profile

1. Switch to the **SpurLine** workbench
2. Click a gear type in the toolbar (involute, rack, or timing pulley)
3. Set teeth count, module, bore diameter, and number of copies
4. Optionally click **Preview in FreeCAD** to inspect and measure the profile
5. Click **Send to LightBurn** or **Send to MillMage**

### Extract profiles from existing objects

1. Open a document with existing objects (FCGear gears, STEP imports, any Part)
2. Select one or more objects in the model tree
3. Click **Extract Profile from Selection** in the toolbar
4. A blue cutting plane appears on the selected objects
5. Use the **Cutting Plane** controls to set the orientation (Top / Front / Right)
   and drag the offset slider to position the slice
6. Set copies per object and optional bore/keyway overrides
7. Click **Preview in FreeCAD** or **Send to LightBurn / MillMage**

### Multi-slice export

To export cross-sections at regular intervals through an object:

1. Follow the steps above to select objects and set the cutting plane orientation
2. Switch to the **Multi-Slice** tab
3. Choose a mode: **Fixed distance** (set mm spacing) or **Slice count** (set
   number of evenly-spaced slices)
4. Click **Preview All Slices** to inspect, or **Send to LightBurn / MillMage**
   to upload each slice as a separate DXF file

## License

GPL-3.0
