# Changelog

This changelog records changes to the LightBurn / MillMage REST API
documentation and specification. Dates use ISO 8601.

## 1.0 — Initial public release

First public release of the API specification and documentation.

### Specification

- Published the OpenAPI specification (`docs/openapi.yaml`) covering the
  `state`, `project`, and `upload` capabilities.
- Added a rendered API reference viewer (`docs/index.html`, Redoc).

### Documentation

- API overview and conceptual model (`docs/overview.md`).
- Getting started guide — pairing, token derivation, first call
  (`docs/getting-started.md`).
- Authentication reference — pairing and the HMAC-SHA256 token scheme
  (`docs/authentication.md`).
- Capabilities reference — scopes and the endpoints each grants
  (`docs/capabilities.md`).
- File upload and placement guide (`docs/uploading.md`).
- Human-readable API reference index (`docs/api-reference.md`).
- Versioning model (`docs/versioning.md`). Describes the planned versioning
  approach; a version negotiation mechanism is not yet implemented.
- Deprecation policy (`docs/deprecations.md`). No deprecations at this time.

### Legal & policy

- API End User License Agreement (`API-EULA.md`).
- Project policy, goals, and support boundaries (`POLICY.md`).
- Safety guidance (`SAFETY.md`).
- Security reporting policy (`SECURITY.md`).
- Responsible disclosure process (`DISCLOSURE.md`).
- Certification and compatibility-claims policy (`CERTIFICATION.md`).
- Copyright, ownership, and licensing notice (`NOTICE.md`).

### Examples

- FreeCAD workbench reference client — generate gear profiles and send them
  (`examples/spurline/`, GPL-3.0).
- Inkscape extensions reference client — draw the workspace, de-duplicate
  shared edges, size the document, and send drawings (`examples/inkscape/`,
  GPL-3.0).
- Examples licensing: MIT by default, with per-subdirectory licenses where a
  LICENSE file is present (`examples/README.md`).
