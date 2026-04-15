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
ln -s /path/to/SpurLine ~/.local/share/FreeCAD/Mod/SpurLine
```

**Windows** (run as Administrator in PowerShell)
```powershell
New-Item -ItemType SymbolicLink `
  -Path "$env:APPDATA\FreeCAD\v1-1\Mod\SpurLine" `
  -Target "C:\path\to\SpurLine"
```

Then restart FreeCAD and select **SpurLine** from the workbench dropdown.

## Configuration

No manual configuration is required.  When you click **Send to LightBurn**
or **Send to MillMage** for the first time, SpurLine identifies itself as
`"FreeCAD (SpurLine)"` and requests access via the local REST API.  A
consent dialog appears in LightBurn / MillMage — approve it once and the
connection is remembered across sessions.

If you need to re-authorize (e.g. after revoking access), use
**SpurLine > Reset authorizations** from the menu.

## Project structure

```
SpurLine/
├── InitGui.py                          ← FreeCAD workbench entry point
├── Init.py                             ← Headless init (no-op)
├── package.xml                         ← Addon Manager metadata
├── openapi.yaml                        ← LightBurn / MillMage REST API spec
├── freecad/spurline/
│   ├── commands/
│   │   ├── cmd_involute.py             ← Toolbar command: involute gear
│   │   ├── cmd_rack.py                 ← Toolbar command: rack
│   │   ├── cmd_timing.py              ← Toolbar command: timing pulley
│   │   ├── cmd_extract.py             ← Toolbar command: extract from selection
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
│       └── preferences.py             ← Shared secret storage
└── resources/icons/                    ← Toolbar SVG icons
```

## Typical workflow

### Create a new gear profile

1. Switch to the **SpurLine** workbench
2. Click a gear type in the toolbar (involute, rack, or timing pulley)
3. Set teeth count, module, bore diameter, and number of copies
4. Optionally click **Preview in FreeCAD** to inspect and measure the profile
5. Click **Send to LightBurn** or **Send to MillMage**

### Extract profiles from existing gears

1. Create or open a document with existing gear objects (e.g. from the FCGear workbench)
2. Select one or more gear objects in the model tree
3. Click **Extract Profile from Selection** in the toolbar
4. Set copies per gear and optional bore/keyway overrides
5. Click **Preview in FreeCAD** or **Send to LightBurn / MillMage**

## License

MIT
