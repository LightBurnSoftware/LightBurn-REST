# SpurLine — Project Handoff for Claude Code

This document gives you full context to continue developing SpurLine
without needing any prior conversation history.  Read it top to bottom
before touching any files.

---

## What SpurLine is

A **FreeCAD 1.0+ workbench** that:

1. Generates 2D gear profiles using the `freecad.gears` (FCGear) addon
2. Allows the user to configure a bore hole and optional keyway slot
3. Arranges one or more copies in a grid layout on a "sheet"
4. Exports the result to **DXF or SVG**
5. **POSTs the file bytes** to a localhost REST API listener running inside
   LightBurn or MillMage (laser/CNC machine software)

SpurLine is the **HTTP client**.  LightBurn and MillMage each run their
own HTTPS listener.  The user configures each target once; SpurLine
remembers the endpoint string in FreeCAD's built-in preferences store.

---

## Supported gear types

| Gear type | fcgears command class | Notes |
|---|---|---|
| Involute spur gear | `CreateInvoluteGear` | Bore + keyway supported |
| Involute rack | `CreateInvoluteRack` | Linear — no bore/keyway |
| Timing belt pulley | `CreateTimingGear` | GT2, GT3, T5, T2.5, T10, MXL, XL |

Bevel gears were explicitly **excluded** — only 2D-machinable profiles
are in scope.

---

## Key design decisions (already made — do not revisit)

| Decision | Choice | Reason |
|---|---|---|
| Deployment model | FreeCAD workbench (GUI, inside FreeCAD) | Not CLI/headless |
| FreeCAD version target | 1.0+ only | No 0.21 compatibility shim needed |
| Qt binding | PySide2 with `try/except` fallback to PySide6 | FC 1.0 ships PySide2 |
| HTTP client | `urllib` stdlib — no extra dependencies | Keep install simple |
| Preference storage | `FreeCAD.ParamGet` | Built-in, no extra files |
| Endpoint string format | `https://<host>:<port>:<token>` | Single field, copy-paste from machine software |
| Endpoint parsing | Split on **last** colon to extract token | Handles IPv4, IPv6, hostnames equally |
| Export format | DXF primary, SVG secondary | Both supported by LightBurn + MillMage |
| Multi-copy layout | Simple grid (ceil(sqrt(n)) columns), 15% spacing | Fast and predictable |
| Error categories | (1) Connection/timeout  (2) Auth failure (401/403) | Maps cleanly to HTTP |
| Auth error UX | Popup dialog asking user to enter/correct endpoint string | Re-tries send after save |
| Send trigger | Separate "Send to LightBurn" / "Send to MillMage" buttons | User can preview in FreeCAD first |
| SSL | Self-signed certs accepted (LAN use case) | `ssl.CERT_NONE` — revisit if needed |

---

## Endpoint string format (critical — read carefully)

The user enters a string like:

```
https://192.168.1.50:1234:mySecretToken
```

This is **not** a standard URL — there is a third colon-delimited segment
for the token.  Python's `urllib.parse.urlparse()` cannot handle this.

**Parsing strategy** — split on the **last** colon only:

```python
rest = raw[len("https://"):]        # "192.168.1.50:1234:mySecretToken"
url_suffix, token = rest.rsplit(":", 1)
url = f"https://{url_suffix}"       # "https://192.168.1.50:1234"
```

This is implemented in `freecad/spurline/prefs/preferences.py`
and validated in `freecad/spurline/ui/token_dialog.py`.

---

## Project file structure

```
SpurLine/
├── InitGui.py                          ← FreeCAD scans this on startup
├── Init.py                             ← Headless init (intentionally empty)
├── package.xml                         ← Addon Manager metadata
├── README.md
├── freecad/
│   ├── __init__.py                     ← Namespace package (do not add logic)
│   └── spurline/
│       ├── __init__.py
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── cmd_involute.py         ← Registers SpurLine_Involute command
│       │   ├── cmd_rack.py             ← Registers SpurLine_Rack command
│       │   └── cmd_timing.py           ← Registers SpurLine_Timing command
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── gear_panel.py           ← Main Qt task panel (left dock)
│       │   └── token_dialog.py         ← Endpoint config dialog
│       ├── core/
│       │   ├── __init__.py
│       │   ├── profile_extractor.py    ← 3D gear → 2D Part.Face
│       │   └── sheet_composer.py       ← Grid layout + DXF/SVG export
│       ├── api/
│       │   ├── __init__.py
│       │   └── client.py               ← REST POST client (partially stubbed)
│       └── prefs/
│           ├── __init__.py
│           └── preferences.py          ← FreeCAD ParamGet wrapper
└── resources/
    └── icons/
        ├── spurline.svg                ← Workbench icon (placeholder)
        ├── involute.svg                ← Toolbar icon (placeholder)
        ├── rack.svg                    ← Toolbar icon (placeholder)
        └── timing.svg                  ← Toolbar icon (placeholder)
```

---

## Module responsibilities (one paragraph each)

### `InitGui.py`
Defines and registers `SpurLineWorkbench`.  `Initialize()` is called
lazily on first activation and imports the three command modules.
Toolbar and menu are both populated with the same command list.

### `commands/cmd_*.py`
Each file defines and registers exactly one FreeCAD command class.
`Activated()` opens `GearPanel` pre-configured with a `gear_type` string.
`IsActive()` greys out the button when no document is open.

### `ui/gear_panel.py`  ← most complex file
The Qt task panel embedded in FreeCAD's left Task dock.  Contains:
- Parameter widgets (teeth, module, pressure angle, belt type, bore, keyway, copies)
- Visibility rules: module/pressure hidden for timing; bore/keyway hidden for rack
- Live pitch-diameter label that updates on every spinbox change
- "Preview in FreeCAD" button — calls `ProfileExtractor` + `SheetComposer.place_in_document()`
- "Send to LightBurn" and "Send to MillMage" buttons — call `_send(target)`
- `_send()` orchestrates: extract → export to bytes → POST → handle result
- Error dialogs: generic `QMessageBox.critical` for connection errors;
  `TokenDialog` for auth errors (which retries after the user saves)
- `accept()` / `reject()` satisfy FreeCAD's task panel protocol but
  Send buttons are the real exit path

### `ui/token_dialog.py`
Modal `QDialog` for entering the endpoint string.  Validates format
before saving.  Pre-fills with the currently stored value if any.
Calls `SpurLinePrefs().set_endpoint()` on accept.

### `core/profile_extractor.py`
Pure geometry — no UI, no file I/O, no network.  `extract(params)`:
1. Creates a minimal-height (1mm) 3D gear via `freecad.gears`
2. Slices at Z=0 with `shape.section(plane)` to get a 2D profile
3. Cuts bore hole (circle subtraction)
4. Cuts keyway slot (rectangle subtraction, DIN 6885 proportions: height = 0.6 × width)
5. Removes the 3D solid from the document
6. Returns a `Part.Face`

**Known issue to verify**: The fcgears property name for tooth count
is `num_teeth` on current master but `teeth` on some older installed
versions.  Check with `print(dir(gear_obj))` in FreeCAD's Python console
after creating a test gear.

### `core/sheet_composer.py`
Takes a `Part.Face` and a copy count.  Grid positions are computed as
`cols = ceil(sqrt(copies))`, spacing = 1.15× bounding box size.

Three public methods:
- `place_in_document(face, copies)` — adds `Part::Feature` objects to
  the active document for visual preview
- `to_dxf_bytes(face, copies) → bytes` — exports via temp file, returns bytes
- `to_svg_bytes(face, copies) → bytes` — same for SVG
- `export_to_file(face, copies, path)` — writes directly to disk

**Important**: `import Draft` must precede `import importDXF` or the
DXF library won't initialise.  This is already in the code.

### `api/client.py`  ← **PARTIALLY STUBBED — needs OpenAPI spec**
`SpurLineClient.send(endpoint, file_bytes, fmt)` returns a `SendResult`
dataclass.  Never raises — all exceptions are caught internally.

Three values are marked `TODO` and must be filled from the OpenAPI spec:
```python
_ENDPOINT_PATH = "/api/import"      # TODO: real path
_AUTH_HEADER   = "X-Api-Token"      # TODO: real header name
_CONTENT_TYPE  = "application/octet-stream"  # TODO: real content type
```

Error handling is already complete for both error categories:
- `urllib.error.URLError` (connection refused, timeout) → descriptive message
- `urllib.error.HTTPError` with status 401/403 → `is_auth_error=True`
- All other `HTTPError` statuses → generic message with status code

### `prefs/preferences.py`
Wraps `FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/SpurLine")`.
Stores two keys: `LightBurnEndpoint` and `MillMageEndpoint` as raw strings.
`get_endpoint(target)` returns a parsed `EndpointConfig(url, token, raw)`
or `None` if not configured.  `set_endpoint(target, raw)` persists.

---

## What is complete vs stubbed

| Component | Status |
|---|---|
| Workbench registration + toolbar | ✅ Complete |
| All three command classes | ✅ Complete |
| GearPanel UI structure + wiring | ✅ Complete |
| TokenDialog (validation + save) | ✅ Complete |
| Preferences read/write/parse | ✅ Complete |
| ProfileExtractor geometry | ✅ Complete (verify `num_teeth` vs `teeth`) |
| SheetComposer layout + export | ✅ Complete (test `importDXF` path) |
| REST client error handling | ✅ Complete |
| REST client — endpoint path | ⚠️  TODO: from OpenAPI spec |
| REST client — auth header name | ⚠️  TODO: from OpenAPI spec |
| REST client — Content-Type | ⚠️  TODO: from OpenAPI spec |
| REST client — response parsing | ⚠️  TODO: from OpenAPI spec |
| Toolbar icons | ⚠️  Placeholder SVGs — functional but not polished |

---

## Immediate next steps

### 1 — Verify it loads in FreeCAD

Symlink the project folder into FreeCAD's user Mod directory:

```bash
# Linux / macOS
ln -s /path/to/SpurLine ~/.local/share/FreeCAD/Mod/SpurLine

# Windows (PowerShell, run as admin)
New-Item -ItemType SymbolicLink `
  -Path "$env:APPDATA\FreeCAD\Mod\SpurLine" `
  -Target "C:\path\to\SpurLine"
```

Restart FreeCAD.  SpurLine should appear in the workbench selector.
The toolbar should show three buttons.

Quick smoke test in FreeCAD's Python console:
```python
import freecad.spurline
print(freecad.spurline.__version__)   # should print '0.1.0'
```

If this fails with a namespace conflict on `freecad/`, see the note below.

### 2 — Namespace package conflict

FreeCAD's `freecad.gears` addon also lives under a `freecad/` directory.
Python's namespace package mechanism should allow both to coexist, but
only if **neither** `freecad/__init__.py` contains meaningful imports.
SpurLine's `freecad/__init__.py` is intentionally near-empty.  If you
see import errors, check whether the installed `freecad.gears` has a
conflicting `__init__.py`.

### 3 — Verify fcgears property names

In FreeCAD's Python console, after installing the FCGear addon:
```python
import FreeCAD, freecad.gears.commands as gc
doc = FreeCAD.newDocument("test")
g = gc.CreateInvoluteGear.create()
print([p for p in dir(g) if 'teeth' in p.lower()])
```

If the output is `['num_teeth']`, the code is correct as written.
If it's `['teeth']`, find and replace `num_teeth` with `teeth` in
`core/profile_extractor.py`.

### 4 — Fill in the REST client TODOs

The owner of this project has an OpenAPI YAML spec for the LightBurn /
MillMage REST API.  Once provided, update these three constants in
`freecad/spurline/api/client.py`:

```python
_ENDPOINT_PATH = "/api/import"          # replace with real path
_AUTH_HEADER   = "X-Api-Token"          # replace with real header name
_CONTENT_TYPE  = "application/octet-stream"  # replace per spec
```

Also update `_do_post()` if the spec requires multipart form-data,
a specific filename parameter, or a non-trivial response body parse.

### 5 — Test the full send flow end-to-end

Once the REST TODOs are filled:
1. Start LightBurn or MillMage with its REST listener enabled
2. Open SpurLine, create an involute gear
3. Click Preview — verify the profile appears in FreeCAD
4. Click Send — verify the file arrives in the machine software

---

## FreeCAD API quick reference

```python
# Document
doc = FreeCAD.ActiveDocument          # None if no document open
doc = FreeCAD.newDocument("name")     # create one

# Add a shape to the document
feat = doc.addObject("Part::Feature", "MyLabel")
feat.Shape = some_part_face
doc.recompute()

# Remove an object
doc.removeObject(obj.Name)

# Preferences
params = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/SpurLine")
params.GetString("MyKey", "default")
params.SetString("MyKey", "value")

# Task panel
FreeCADGui.Control.showDialog(panel_instance)  # open
FreeCADGui.Control.closeDialog()               # close from inside accept()/reject()

# Register a command
FreeCADGui.addCommand("CommandName", CommandInstance())
```

---

## Dependencies

- **FreeCAD 1.0+** (provides `FreeCAD`, `Part`, `importDXF`, `importSVG`,
  `Draft`, `FreeCADGui`, PySide2)
- **freecad.gears** addon (install via Tools → Addon Manager → search "Gears")
- No pip dependencies — stdlib `urllib` is used for HTTP

---

## Notes for the developer

- The project owner wrote the LightBurn/MillMage REST API themselves,
  so the OpenAPI spec is authoritative and available on request.
- LightBurn and MillMage will have **different** auth tokens, hence two
  separate preference keys and two separate Send buttons.
- The "Send to X" buttons do NOT close the task panel on success —
  the user may want to send to both targets or tweak and re-send.
- SSL certificate verification is disabled (`ssl.CERT_NONE`) because
  LightBurn/MillMage use self-signed certs on a LAN.  This is intentional.
- Icons are placeholders.  Final icons should be clean SVG, ideally
  matching FreeCAD's icon style (thin strokes, no fills, ~64×64 viewBox).