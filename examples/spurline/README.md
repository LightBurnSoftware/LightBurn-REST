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

## Install

> **Demo workbench.** This is an early demo, installed by hand (steps below) —
> not through the FreeCAD Addon Manager. More features are planned.

SpurLine must end up as a `SpurLine` folder inside FreeCAD's user `Mod`
directory. Pick **one** of the two methods below, then restart FreeCAD.

**1. Find your FreeCAD `Mod` directory:**

| OS | Path |
|----|------|
| Windows | `%APPDATA%\FreeCAD\Mod` |
| Linux | `~/.local/share/FreeCAD/Mod` |
| macOS | `~/Library/Application Support/FreeCAD/Mod` |

Not sure? In FreeCAD open the **Python console** (View → Panels → Python console)
and run `import FreeCAD; print(FreeCAD.getUserAppDataDir())` — `Mod` is inside
that folder (create the `Mod` folder if it isn't there).

**2a. Symlink it** (best if you'll edit the code — changes apply on the next
restart). Run from the repository root:

Linux / macOS:
```bash
ln -s "$PWD/examples/spurline" ~/.local/share/FreeCAD/Mod/SpurLine
```
Windows (PowerShell, **as Administrator**):
```powershell
New-Item -ItemType SymbolicLink `
  -Path "$env:APPDATA\FreeCAD\Mod\SpurLine" `
  -Target "$PWD\examples\spurline"
```

**2b. Or just copy it** into `Mod\SpurLine`. Run from the repository root:

Linux / macOS:
```bash
cp -r examples/spurline ~/.local/share/FreeCAD/Mod/SpurLine
```
Windows (PowerShell):
```powershell
Copy-Item examples\spurline "$env:APPDATA\FreeCAD\Mod\SpurLine" -Recurse
```

**3. Restart FreeCAD** and select **SpurLine** from the workbench dropdown.

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

The default ports are **19520** (LightBurn) and **19521** (MillMage).  If you
have changed the port in the app's Settings, use **SpurLine > Set port...** to
match it (you pick which application).

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

GPL-3.0 — see [LICENSE](LICENSE).
