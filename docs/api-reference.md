# API Reference

The authoritative, machine-readable contract is [`openapi.yaml`](openapi.yaml).
Render it with [`index.html`](index.html) (Redoc) or any OpenAPI viewer. This
page is a human-friendly index grouped by capability.

All endpoints except `GET /` and `POST /api/connect` require a Bearer token
(see [Authentication](authentication.md)). Base URL: `http://localhost:19520`
(LightBurn) or `19521` (MillMage).

## Pairing & service (no auth)

| Method & path | Description |
|---------------|-------------|
| `GET /` | Placeholder HTML page |
| `POST /api/connect` | Pair a localhost application; returns a shared secret |

## `state` capability — read-only machine & job state

| Method & path | Description |
|---------------|-------------|
| `GET /api/status` | Connection status and device capabilities |
| `GET /api/position` | Machine and workpiece coordinates |
| `GET /api/jog/settings` | Current jog distance/speed settings |
| `GET /api/goto/saved` | Saved positions from the device profile |
| `GET /api/units` | Current display units |
| `GET /api/events` | Server-Sent Events stream of state changes |
| `GET /api/events/poll` | Latest state snapshot (polling fallback) |

## `project` capability — read-only project data

| Method & path | Description |
|---------------|-------------|
| `GET /api/project` | Project metadata: filename, units, workspace, device |
| `GET /api/layers` | All 32 layer definitions |
| `GET /api/cuts` | Cut settings for all layers (product-specific) |
| `GET /api/cuts/{index}` | A single cut entry by flat index |
| `GET /api/material-library` | Loaded material / operations library |

## `upload` capability — submit files

| Method & path | Description |
|---------------|-------------|
| `POST /api/file/upload` | Import a file into the current project (supports placement headers) |
| `POST /api/file/open` | Replace the current project with the uploaded file |

See [Uploading files](uploading.md) for the request body, `X-Filename`, and the
placement headers (`X-Position-X/Y`, `X-Origin`, `X-Group-Shapes`).

## Conventions

- **Auth:** `Authorization: Bearer <token>`; missing/invalid → `401`. Calling an
  endpoint outside your granted capability → `403`.
- **Units:** distance and speed values use the user's current display units;
  read them from `GET /api/units` or `GET /api/project`.
- **Async import:** uploads return `202 Accepted` immediately; the result
  arrives later as a `file_imported` event on `GET /api/events`.
- **Product differences:** `GET /api/cuts` and `GET /api/material-library`
  return product-specific shapes — dispatch on the `product` field.

## Stability

Endpoint and field details may change between application releases until
versioning ships — see [Versioning](versioning.md). Only documented behaviour is
supported; undocumented responses may change without notice.
