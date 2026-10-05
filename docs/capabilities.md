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

A tool that adjusts cut settings typically needs `project` to read them and
`project_write` to change them:

```json
{ "application_name": "My Tool", "capabilities": ["project", "project_write"] }
```

## The four capabilities

| Wire string | Grants | Endpoints |
|-------------|--------|-----------|
| `state` | Read-only machine and job state | `GET /api/status`, `GET /api/position`, `GET /api/jog/settings`, `GET /api/goto/saved`, `GET /api/units`, `GET /api/events`, `GET /api/events/poll` |
| `project` | Read-only project data | `GET /api/project`, `GET /api/layers`, `GET /api/cuts`, `GET /api/cuts/{index}`, `GET /api/material-library`, `GET /api/overlay`, `GET /api/overlay/metadata` |
| `upload` | Submit files for import | `POST /api/file/upload`, `POST /api/file/open` |
| `project_write` | Change project data | `POST /api/cuts/{index}` |

A token validates against the endpoints its capabilities cover; calling an
endpoint outside its scope fails authorization even though the token itself is
valid.

`project_write` is independent of `project`: request both if you need to read
cut settings as well as change them. See [Cut settings](cut-settings.md).

> **`project` includes camera imagery.** `GET /api/overlay` returns the camera
> overlay drawn on the workspace — a photograph of the user's machine and
> whatever is around it. If your integration doesn't need it, say so in your
> documentation; users granting `project` are granting this too.

See [`openapi.yaml`](openapi.yaml) for request/response schemas of each endpoint.
