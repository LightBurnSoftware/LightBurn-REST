# API Reference

The authoritative, machine-readable contract is [`openapi.yaml`](openapi.yaml).
Render it with [`index.html`](index.html) (Redoc) or any OpenAPI viewer. This
page is a human-friendly index grouped by capability.

All endpoints except `GET /` and `POST /api/connect` require a Bearer token
(see [Authentication](authentication.md)). Base URL: `http://localhost:19520`
(LightBurn) or `19521` (MillMage) — these ports are fixed per product. Replace
`localhost` with the host's address when the application has network access
enabled; `POST /api/connect` remains localhost-only regardless.

With more than one copy of the same product running, the port is served by the
most recently focused window — see [Overview](overview.md#multiple-instances).

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
| `GET /api/project` | Project metadata: filename, units, workspace, device (including laser source capabilities) |
| `GET /api/layers` | All 32 layer definitions |
| `GET /api/cuts` | Cut settings for all layers or operations (product-specific) |
| `GET /api/cuts/{index}` | A single cut entry by flat index |
| `GET /api/material-library` | Loaded material / operations library |

## `upload` capability — submit files

| Method & path | Description |
|---------------|-------------|
| `POST /api/file/upload` | Import a file into the current project (supports placement headers) |
| `POST /api/file/open` | Replace the current project with the uploaded file |

See [Uploading files](uploading.md) for the request body, `X-Filename`, and the
placement headers (`X-Position-X/Y`, `X-Origin`, `X-Group-Shapes`).

## `project_write` capability — change project data

| Method & path | Description |
|---------------|-------------|
| `POST /api/cuts/{index}` | Partial update of one cut entry; returns the updated entry |

See [Cut settings](cut-settings.md) for the fields each product accepts, how
changes are validated and applied, and the `409` returned while the cut editor
is open.

## Conventions

- **Auth:** `Authorization: Bearer <token>`. Every authorization failure returns
  a bare `401` — missing, invalid, expired, revoked, outside your granted
  capability, or from off-machine while network access is off. The reasons are
  deliberately indistinguishable; don't branch on them.
- **Units:** positions (`/api/position`, the `position` event) and the
  `/api/project` `workspace` are always in mm. LightBurn cut values, the
  MillMage `tool` block, and jog settings use the user's display units — read
  those from `GET /api/units`, which reports the speed unit as `units` and the
  distance unit as `distance_units`. The two are independent: the application
  supports modes that pair inch distances with metric speeds, so never infer
  one from the other. MillMage operation `settings` are always mm and mm/s.
  (`/api/project` `units.distance` is a translated UI label for display only —
  don't parse it.)
- **Optional fields:** a field the application can't report is omitted rather
  than zeroed — for example an axis the controller doesn't report, or job
  `progress` while idle or on controllers that don't report it. Treat absence
  as "unknown".
- **Async import:** uploads return `202 Accepted` immediately; the result
  arrives later as a `file_imported` event on `GET /api/events`.
- **Events:** the SSE stream opens with a `:connected` comment. "On change"
  events aren't replayed to a new subscriber, so call `GET /api/events/poll`
  once after connecting to get the current state.
- **Partial updates:** `POST /api/cuts/{index}` changes only the fields in the
  body and validates the whole body first — on any error nothing changes.
- **Product differences:** `GET /api/cuts`, `POST /api/cuts/{index}` and
  `GET /api/material-library` use product-specific shapes — dispatch on the
  `product` field.

## Stability

Endpoint and field details may change between application releases until
versioning ships — see [Versioning](versioning.md). Only documented behaviour is
supported; undocumented responses may change without notice.
