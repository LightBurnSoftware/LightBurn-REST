# lightburn-rest

Documentation and reference clients for the **LightBurn / MillMage REST API** —
the local HTTP API exposed by the desktop applications for file upload/import,
read-only project and machine-state queries, and real-time state streaming.

## Contents

| Path | What it is |
|------|------------|
| [`docs/openapi.yaml`](docs/openapi.yaml) | The API specification — single source of truth |
| `lib/` | `lightburn_rest` — a stdlib-only Python client (install from source) |
| [`examples/spurline/`](examples/spurline/) | FreeCAD workbench that generates gear profiles and sends them to LightBurn/MillMage (reference client) |
| `examples/inkscape/` | Inkscape extension that de-duplicates coincident SVG segments before sending (reference client) |

> `lib/` and `examples/inkscape/` are in progress.

## The API at a glance

- **Transport:** plain HTTP on `http://localhost:19522` (default port).
- **Auth:** Bearer token = `hex(HMAC-SHA256(secret, floor(unix_time / 60)))`.
  Obtain a secret by pairing via `POST /api/connect` (localhost apps) or
  `POST /api/bind` (LAN devices).
- **Capabilities:** a token is scoped at pairing time to any of `state`
  (read-only machine/job state), `project` (read-only project data), and
  `upload` (submit files for import).

See [`docs/openapi.yaml`](docs/openapi.yaml) for the full endpoint reference.

## License

GPL-3.0 — see [LICENSE](LICENSE).
