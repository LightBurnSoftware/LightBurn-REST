# Getting started

The LightBurn / MillMage REST API is an HTTP API served on loopback — port
**19520** for LightBurn and **19521** for MillMage. These are fixed per
product and cannot be changed. The API listens whenever the app is open, and
can be opened to the network via **Settings → Extensions → Allow API Access
From Network**. The examples below use loopback. This guide covers pairing to
obtain a shared secret and deriving the Bearer token every authenticated
request needs.

The full endpoint reference is [`openapi.yaml`](openapi.yaml) (render it with
[`index.html`](index.html) or any OpenAPI viewer).

## 1. Pair to obtain a shared secret

Every authenticated endpoint needs a Bearer token derived from a **shared
secret**, obtained by pairing a local application via `POST /api/connect`
(localhost only — shows a consent dialog in the desktop app and returns a
secret on approval).

`/api/connect` is localhost-only even when network access is enabled, so a
client that will run on another machine still has to be paired on the machine
running LightBurn. Once issued, the secret works from anywhere the listener is
reachable.

Send your app name and the [capabilities](capabilities.md) you need:

```http
POST /api/connect HTTP/1.1
Host: localhost:19520
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
    "http://localhost:19520/api/status",
    headers={"Authorization": f"Bearer {bearer_token(secret)}"},
)
print(urllib.request.urlopen(req).read())
```

A missing or invalid token returns `401`. All endpoints except `/` and
`POST /api/connect` require the token.

## Next

- [Capabilities](capabilities.md) — what each token scope unlocks.
- [Uploading files](uploading.md) — import artwork and projects.
- [`examples/spurline`](../examples/spurline/) — a working FreeCAD client.
