# Uploading files

The `upload` [capability](capabilities.md) exposes two endpoints. Both take the
file as the **raw request body** (`application/octet-stream`) with the filename
in an `X-Filename` header, and return `202 Accepted` immediately — the import
runs asynchronously.

| Endpoint | Behavior |
|----------|----------|
| `POST /api/file/upload` | Imports the file into the **current** project (merge). Supports placement headers. |
| `POST /api/file/open` | Replaces the current project with the file (File → Open). No placement headers. |

## Importing into the current project

```python
import urllib.request

data = open("design.svg", "rb").read()
req = urllib.request.Request(
    "http://localhost:19522/api/file/upload",
    data=data,
    method="POST",
    headers={
        "Authorization": f"Bearer {bearer_token(secret)}",
        "Content-Type": "application/octet-stream",
        "X-Filename": "design.svg",
    },
)
print(urllib.request.urlopen(req).read())   # {"status": "accepted", ...}
```

The `X-Filename` extension selects the loader/translator, so set it to match the
payload (`.svg`, `.dxf`, `.lbrn2`, …).

### Placement headers (`/api/file/upload` only)

By default the import lands at the current view center. To anchor it at a
specific workspace coordinate:

| Header | Meaning |
|--------|---------|
| `X-Position-X`, `X-Position-Y` | Anchor point in workspace mm (workpiece origin). Must be sent as a pair. |
| `X-Origin` | Which corner of the import's bounding box sits at the anchor: `top-left` … `bottom-right`, or `center` (default). Ignored unless both position headers are present. |
| `X-Group-Shapes` | `"true"` keeps imported shapes grouped; `"false"` (default) uses the app's global grouping preference. |

## Knowing when the import finished

The `202` only means the file was received. The actual import result arrives
over the [`state`](capabilities.md) channel as a `file_imported` event — via the
`GET /api/events` SSE stream or the `GET /api/events/poll` fallback. Request the
`state` capability too if you need to confirm success.

See [`openapi.yaml`](openapi.yaml) for the full header and response schemas.
