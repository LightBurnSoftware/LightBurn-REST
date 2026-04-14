# SpurLine v0.1.0 — Initial Release

FreeCAD workbench for generating 2D gear profiles and sending them directly to LightBurn or MillMage via their REST API.

## Features

### Gear Profile Generation
- **Involute spur gears** — configurable teeth, module, and pressure angle
- **Involute racks** — configurable teeth, module, and pressure angle
- **Timing belt pulleys** — supports GT2, GT3, T2.5, T5, T10, MXL, XL profiles
- **Center bore** with optional DIN 6885 keyway slot
- **Multi-copy layout** — arrange up to 50 copies in an automatic grid

### FreeCAD Integration
- Installs as a standard FreeCAD workbench (Mod directory symlink or copy)
- Compatible with FreeCAD 1.1
- Requires the [fcgears](https://github.com/looooo/freecad.gears) addon
- Live preview in the 3D viewport — re-preview replaces the previous result
- Task panel UI with parameter fields, live pitch diameter readout, and send buttons

### REST API Client
- Sends DXF files to LightBurn or MillMage over HTTPS
- **HMAC-SHA256 time-based authentication** — computes a Bearer token from the shared secret each minute; the secret is never sent over the wire
- Endpoint URL format: `https://host:port?secret=VALUE` (paste directly from the QR code shown in LightBurn/MillMage)
- Handles HTTP 202 async acceptance, 401/403 auth errors, connection timeouts, and refused connections with user-friendly messages
- Self-signed TLS certificates accepted (typical for LAN use)

### Settings
- **SpurLine > Settings** menu entry for configuring LightBurn and MillMage connection URLs
- Endpoint strings persist across FreeCAD sessions via the built-in preference store
- Auth error during send automatically prompts for endpoint re-entry

## Installation

1. Clone or copy this repository
2. Create a directory junction (Windows) or symlink (Linux/macOS) in your FreeCAD Mod directory:
   - **FreeCAD 1.1 on Windows:** `%APPDATA%\FreeCAD\v1-1\Mod\SpurLine`
   - **FreeCAD 1.0 on Windows:** `%APPDATA%\FreeCAD\Mod\SpurLine`
3. Install the fcgears addon via FreeCAD's Addon Manager if not already present
4. Restart FreeCAD and select the SpurLine workbench from the dropdown

## Dependencies

- FreeCAD 1.0 or 1.1
- [freecad.gears](https://github.com/looooo/freecad.gears) addon
- Python stdlib only (no pip packages required)
