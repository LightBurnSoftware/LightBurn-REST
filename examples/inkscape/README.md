# Inkscape → LightBurn / MillMage

An Inkscape extension that sends the current drawing to LightBurn or MillMage
over the [REST API](../../docs/openapi.yaml), de-duplicating coincident edges so
shared cut lines aren't cut twice.

## What it does

1. Collects the selected shapes (or the whole document).
2. **De-duplicates exact-coincident line segments** — when two shapes share an
   edge, only the first keeps it; the laser cuts that edge once.
3. Uploads the result as SVG via `POST /api/file/upload`. The open document is
   never modified.

The de-dup is intentionally simple (see [`dedupe.py`](dedupe.py)): it matches
straight line segments by endpoint, direction-independent. **Curves always pass
through unchanged** — coincident curves and partial/collinear overlaps are a
known limitation, to be revisited with a geometric union if needed.

> **Demo extension.** This is an early demo, installed by hand (steps below) —
> not through an addon manager. More features are planned.

## Install

The extension is five files that must stay together. Copy them into a new
`lightburn-send` folder inside your Inkscape **user extensions** directory,
then restart Inkscape.

**1. Find your user extensions directory** (also shown in Inkscape under
**Edit → Preferences → System → User extensions**):

| OS | Path |
|----|------|
| Windows | `%APPDATA%\inkscape\extensions` |
| Linux | `~/.config/inkscape/extensions` |
| macOS | `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions` |

**2. Copy the files there.** From the repository root:

Windows (PowerShell):
```powershell
$dst = "$env:APPDATA\inkscape\extensions\lightburn-send"
New-Item -ItemType Directory -Force $dst | Out-Null
Copy-Item examples\inkscape\*.inx, examples\inkscape\*.py $dst
```

Linux / macOS:
```bash
dst=~/.config/inkscape/extensions/lightburn-send
mkdir -p "$dst"
cp examples/inkscape/*.inx examples/inkscape/*.py "$dst"
```

This installs the two `.inx` files plus `lightburn_send.py`,
`lightburn_client.py`, and `dedupe.py`. (If you're editing the code, symlink the
folder instead so changes are picked up: `ln -s "$PWD/examples/inkscape" "$dst"`.)

**3. Restart Inkscape.** The commands appear under **Extensions → LightBurn /
MillMage**.

## Use

1. Make sure LightBurn / MillMage is **open** (the API listens whenever the app
   is running).
2. In Inkscape: **Extensions → LightBurn / MillMage → Send to LightBurn**
   (or **Send to MillMage**).
3. The first send triggers a consent dialog in the app — approve it. The shared
   secret is stored under `…/lightburn-rest/inkscape-secrets.json` and reused on
   later sends (LightBurn and MillMage each get their own).

The correct port is used automatically — **19520** for LightBurn, **19521** for
MillMage. If you've customised the REST API port, override it on the **Advanced**
tab. Other options: **De-duplicate shared segments** and **Selection only**
(uncheck to send the whole document).

## Requirements & testing

- Inkscape 1.0+ (uses the bundled `inkex` Python module). No extra packages.
  Verified against Inkscape 1.4 / inkex 1.4.
- The de-dup core has a standalone self-check: `python dedupe.py`.
- Sample drawings live in [`test-svgs/`](test-svgs/): two squares sharing an
  edge, and two triangles sharing a diagonal. Open one in Inkscape and send it —
  the shared edge should be dropped from the second shape, and each shape's
  colour preserved.
