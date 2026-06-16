# Capabilities

A token is scoped at [pairing time](getting-started.md#1-pair-to-obtain-a-shared-secret)
to one or more capabilities. You request them as a non-empty array in the
`capabilities` field of `POST /api/connect`; unknown values are rejected with
`400`. Capabilities are **immutable** for the life of a token — to change scope,
re-pair.

Request only what you need. A file-submitting tool typically needs just
`upload` (plus `state` if it wants to read machine status):

```json
{ "application_name": "My Tool", "capabilities": ["state", "upload"] }
```

## The three capabilities

| Wire string | Grants | Endpoints |
|-------------|--------|-----------|
| `state` | Read-only machine and job state | `GET /api/status`, `GET /api/position`, `GET /api/jog/settings`, `GET /api/goto/saved`, `GET /api/units`, `GET /api/events`, `GET /api/events/poll` |
| `project` | Read-only project data | `GET /api/project`, `GET /api/layers`, `GET /api/cuts`, `GET /api/cuts/{index}`, `GET /api/material-library` |
| `upload` | Submit files for import | `POST /api/file/upload`, `POST /api/file/open` |

A token validates against the endpoints its capabilities cover; calling an
endpoint outside its scope fails authorization even though the token itself is
valid.

See [`openapi.yaml`](openapi.yaml) for request/response schemas of each endpoint.
