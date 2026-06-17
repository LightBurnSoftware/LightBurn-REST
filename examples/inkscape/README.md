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

## Install

Copy (or symlink) the four files into your Inkscape **user extensions**
directory, then restart Inkscape:

| OS | Extensions directory |
|----|----------------------|
| Windows | `%APPDATA%\inkscape\extensions` |
| Linux | `~/.config/inkscape/extensions` |
| macOS | `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions` |

```bash
# Linux/macOS — symlink the folder (Inkscape scans subdirectories)
ln -s "$PWD" ~/.config/inkscape/extensions/lightburn-send
```

Files (keep them together): `lightburn_send_lightburn.inx`,
`lightburn_send_millmage.inx`, `lightburn_send.py`, `lightburn_client.py`,
`dedupe.py`.

## Use

1. In LightBurn / MillMage, make sure the REST API is enabled.
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
