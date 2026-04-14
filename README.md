# SpurLine

A FreeCAD workbench that generates 2D gear profiles and sends them
directly to **LightBurn** or **MillMage** for laser cutting or CNC milling.

## Supported gear types

| Type | FreeCAD gear | Notes |
|------|-------------|-------|
| Involute spur gear | `CreateInvoluteGear` | Bore + keyway support |
| Involute rack | `CreateInvoluteRack` | Linear, no bore |
| Timing belt pulley | `CreateTimingGear` | GT2, GT3, T5, T2.5, T10, MXL, XL |

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
  -Path "$env:APPDATA\FreeCAD\Mod\SpurLine" `
  -Target "C:\path\to\SpurLine"
```

Then restart FreeCAD and select **SpurLine** from the workbench dropdown.

## Configuration

On first use, click **Send to LightBurn** or **Send to MillMage**.
If no endpoint is configured, the token dialog will open automatically.

Enter the endpoint string in the format provided by LightBurn / MillMage:

```
https://<host IP>:<port>:<token>
```

Example:
```
https://192.168.1.50:1234:mySecretToken
```

The string is saved in FreeCAD's preferences and never needs to be
entered again unless you change it.

## Project structure

```
SpurLine/
├── InitGui.py                      ← FreeCAD workbench entry point
├── Init.py                         ← Headless init (no-op)
├── package.xml                     ← Addon Manager metadata
├── freecad/spurline/
│   ├── commands/
│   │   ├── cmd_involute.py         ← Toolbar command: involute gear
│   │   ├── cmd_rack.py             ← Toolbar command: rack
│   │   └── cmd_timing.py           ← Toolbar command: timing pulley
│   ├── ui/
│   │   ├── gear_panel.py           ← Main Qt task panel
│   │   └── token_dialog.py         ← Endpoint configuration dialog
│   ├── core/
│   │   ├── profile_extractor.py    ← 3D gear → 2D Part.Face
│   │   └── sheet_composer.py       ← Grid layout + DXF/SVG export
│   ├── api/
│   │   └── client.py               ← REST POST client
│   └── prefs/
│       └── preferences.py          ← FreeCAD ParamGet wrapper
└── resources/icons/                ← Toolbar SVG icons
```

## Typical workflow

1. Switch to the **SpurLine** workbench
2. Click a gear type in the toolbar (involute, rack, or timing pulley)
3. Set teeth count, module, bore diameter, and number of copies
4. Optionally click **Preview in FreeCAD** to inspect and measure the profile
5. Click **Send to LightBurn** or **Send to MillMage**

## License

MIT
