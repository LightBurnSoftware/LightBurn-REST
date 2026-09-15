# LightBurn REST API

The LightBurn REST API provides a documented interface for applications to communicate with supported versions of LightBurn.

The API is intended to support integrations, workflow automation, interoperability, status monitoring, and data exchange between LightBurn and third-party applications.

A similar API is available for MillMage.

---

## Public Specification

The API specification is publicly documented to encourage interoperability and third-party development.

The LightBurn and MillMage API implementations remain proprietary software.

Public documentation of the API does not imply that the implementations, internal functionality, or associated software components are open source.

Example code may be provided under separate licenses as identified within this repository.

---

## Current Scope

The APIs are primarily intended for:

- Reading application state
- Querying supported information
- Exchanging data with LightBurn or MillMage
- Building workflow integrations
- Building companion applications
- Building automation and productivity tools

API functionality may evolve over time as LightBurn and MillMage continue to develop.

---

## Safety Notice

LightBurn Software does not endorse, recommend, support, or encourage the remote or unattended operation of lasers, CNC machines, or other machinery.

The APIs are provided to support integrations and workflows. They are not safety systems and must not be relied upon as a substitute for direct operator supervision.

Users remain responsible for the safe operation of all equipment connected to or used with LightBurn or MillMage.

Please review `SAFETY.md` before implementing machine-related workflows.

---

## Contents

| Path | What it is |
|------|------------|
| [`docs/openapi.yaml`](docs/openapi.yaml) | The API specification — single source of truth |
| [`docs/getting-started.md`](docs/getting-started.md) | Pairing, HMAC token derivation, first call |
| [`docs/capabilities.md`](docs/capabilities.md) | Token scopes and the endpoints each unlocks |
| [`docs/uploading.md`](docs/uploading.md) | Importing artwork and projects |
| `lib/` | `lightburn_rest` — a stdlib-only Python client (install from source) |
| [`examples/spurline/`](examples/spurline/) | FreeCAD workbench that generates gear profiles and sends them to LightBurn/MillMage (reference client) |
| [`examples/inkscape/`](examples/inkscape/) | Inkscape extension that de-duplicates coincident SVG segments before sending (reference client) |

> `lib/` is in progress.

## The API at a glance

- **Transport:** plain HTTP. Port 19520 (LightBurn) / 19521 (MillMage), fixed
  per product. Loopback by default; can be opened to the local network in the
  application's settings.
- **Auth:** Bearer token = `hex(HMAC-SHA256(secret, floor(unix_time / 60)))`.
  Obtain a secret by pairing a localhost app via `POST /api/connect`. Pairing
  is localhost-only even when network access is enabled.
- **Capabilities:** a token is scoped at pairing time to any of `state`
  (read-only machine/job state), `project` (read-only project data), and
  `upload` (submit files for import).

See [`docs/openapi.yaml`](docs/openapi.yaml) for the full endpoint reference.

## Repository Documents

| Document | Description |
|-----------|-------------|
| `NOTICE.md` | Copyright, ownership, and licensing notices |
| `API-EULA.md` | Legal terms governing API use |
| `POLICY.md` | Project goals, expectations, and support boundaries |
| `SAFETY.md` | Safety guidance and operational recommendations |
| `SECURITY.md` | Security reporting procedures |
| `DISCLOSURE.md` | Responsible disclosure process |
| `CERTIFICATION.md` | Compatibility claims and future certification policies |
| `CHANGELOG.md` | API and documentation changes |

---

## Documentation

Additional documentation is available in the `docs` directory.

Documentation may include:

- API Overview
- Authentication
- Versioning
- API Reference
- Deprecation Notices
- Migration Guidance

---

## Versioning

The APIs evolve alongside LightBurn and MillMage releases.

Endpoints, request formats, response formats, authentication methods, and available functionality may change between software versions.

Where practical, compatibility will be maintained and migration guidance may be provided. However, backward compatibility cannot be guaranteed.

Developers should test integrations against the versions they intend to support.

---

## Examples

Example code is available in the `examples` directory.

Example code is licensed separately under the MIT License **unless a
subdirectory provides its own LICENSE file**, in which case that license
governs. Both current examples (the FreeCAD and Inkscape plugins) are **GPL-3.0**
because they build on GPL-licensed host software; see
[`examples/README.md`](examples/README.md) for details.

Where it applies, the MIT License covers only the example code and does not apply to:

- LightBurn
- MillMage
- The API implementations
- API documentation outside the examples directory
- Other proprietary LightBurn Software materials

---

## Support

Support may be available for publicly documented API functionality.

Third-party applications, integrations, custom automations, and derivative tools remain the responsibility of their respective developers.

Undocumented, internal, experimental, or reverse-engineered functionality is unsupported and may change without notice.

---

## Trademarks

LightBurn and MillMage are trademarks of LightBurn Software, Inc.

Use of the APIs does not grant any right to use LightBurn Software trademarks except as permitted by applicable law or by written permission from LightBurn Software.

See `CERTIFICATION.md` for guidance regarding compatibility claims and branding.

---

## Contact

For support, security reporting, or API-related questions, please refer to the appropriate repository documents or contact LightBurn Software through its official support channels.