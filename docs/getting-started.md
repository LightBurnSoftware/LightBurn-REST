# Getting started

The LightBurn / MillMage REST API is a local HTTP API served at
`http://localhost:19522` (default port). This guide covers pairing to obtain a
shared secret and deriving the Bearer token every authenticated request needs.

The full endpoint reference is [`openapi.yaml`](openapi.yaml) (render it with
[`index.html`](index.html) or any OpenAPI viewer).

## 1. Pair to obtain a shared secret

Every authenticated endpoint needs a Bearer token derived from a **shared
secret**. There are two ways to get one:

| Endpoint | For | Notes |
|----------|-----|-------|
| `POST /api/connect` | localhost applications | Shows a consent dialog in the desktop app; returns a secret on approval. |
| `POST /api/bind` | LAN devices (e.g. pendants) | Triggers a QR code containing the server URL and secret. |

Most integrations use `/api/connect`. Send your app name and the
[capabilities](capabilities.md) you need:

```http
POST /api/connect HTTP/1.1
Host: localhost:19522
Content-Type: application/json

{ "application_name": "My Tool", "capabilities": ["state", "upload"] }
```

The user sees a consent dialog naming your app and the capabilities requested.
On approval you receive a secret (the dialog times out and declines after 30
seconds):

```json
{ "status": "ok", "secret": "aB3dE7fG9hJ1kL5m" }
```

Persist this secret yourself. Each call to `/api/connect` produces a **new**
secret and a fresh consent prompt, scoped to the capabilities you asked for —
capabilities are immutable for the life of the token. To change scope, re-pair.

## 2. Derive the Bearer token

The token is an HMAC-SHA256 of the current Unix minute, keyed by the secret:

```
token = hex(HMAC-SHA256(secret, floor(unix_time / 60)))
```

The server accepts tokens for the current minute **and** the previous minute to
tolerate clock drift. Compute a fresh token per request (or per minute):

```python
import hmac, hashlib, time

def bearer_token(secret: str) -> str:
    message = str(int(time.time()) // 60).encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
```

## 3. Call an endpoint

Pass the token as a Bearer credential:

```python
import urllib.request

req = urllib.request.Request(
    "http://localhost:19522/api/status",
    headers={"Authorization": f"Bearer {bearer_token(secret)}"},
)
print(urllib.request.urlopen(req).read())
```

A missing or invalid token returns `401`. All endpoints except `/`,
`POST /api/bind`, and `POST /api/connect` require the token.

## Next

- [Capabilities](capabilities.md) — what each token scope unlocks.
- [Uploading files](uploading.md) — import artwork and projects.
- [`examples/spurline`](../examples/spurline/) — a working FreeCAD client.
