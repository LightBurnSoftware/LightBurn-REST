---
hide:
  - navigation
---

# LightBurn / MillMage REST API

The LightBurn REST API is an HTTP interface served by the running desktop
application. External programs use it to read application and machine state,
read project data, adjust cut settings, and submit files for import. A similar
API is available for MillMage.

!!! warning "Safety"

    LightBurn Software does not endorse or support the remote or unattended
    operation of lasers, CNC machines, or other machinery. The API is not a
    safety system. Read [Safety](SAFETY.md) before building machine-related
    workflows.

## The API at a glance

- **Transport:** plain HTTP on port 19520 (LightBurn) or 19521 (MillMage),
  fixed per product. Loopback by default; can be opened to the local network
  in the application's settings.
- **Auth:** Bearer token = `hex(HMAC-SHA256(secret, floor(unix_time / 60)))`.
  Obtain a secret by pairing a localhost app via `POST /api/connect`. Pairing
  is localhost-only even when network access is enabled.
- **Capabilities:** a token is scoped at pairing time to any of `state`,
  `project`, `upload` and `project_write`.

## Where to start

| | |
|---|---|
| [Overview](guide/overview.md) | The conceptual map of the API |
| [Getting started](guide/getting-started.md) | Pairing, token derivation, first call |
| [Authentication](guide/authentication.md) | Tokens, clocks and failure modes |
| [Endpoint index](guide/api-reference.md) | Every endpoint, grouped by capability |
| [Full reference](/reference/) | The complete OpenAPI contract, rendered |
| [Changelog](CHANGELOG.md) | API and documentation changes |

Use of the API is governed by the [API EULA](API-EULA.md).

Questions about the documentation, and reports of errors in it, can be raised
as [issues on GitHub](https://github.com/LightBurnSoftware/LightBurn-REST/issues).
Security concerns, and documentation errors that could affect safe machine
operation, should be reported privately as described in [Security](SECURITY.md).
