# Versioning

> **Status: in effect from API 1.0.**
> The API is versioned and stable from version 1.0, which shipped in
> LightBurn 2.2.01. The principles below apply from that version on. The API
> does **not** yet expose a version negotiation or discovery mechanism;
> sections marked _(proposed)_ describe those and are subject to change before
> they ship.

## Why versioning

The REST API evolves alongside LightBurn and MillMage. Endpoints, request and
response shapes, authentication, and available functionality may change between
application releases. Versioning gives integrators a stable contract to build
against and a predictable path when things change.

## Principles

These commitments hold from API 1.0:

- **The specification is the contract.** Each API version corresponds to a
  published `openapi.yaml`. If it isn't documented, it isn't part of the version.
- **Semantic intent.** Versions communicate the *kind* of change:
  - **Major** — backward-incompatible changes (removed/renamed endpoints or
    fields, changed semantics, stricter validation).
  - **Minor** — backward-compatible additions (new endpoints, new optional
    fields, new enum values).
  - **Patch** — documentation clarifications and fixes with no behavioural change.
- **Additive changes are not breaking.** Clients must ignore unknown fields and
  tolerate new enum values, so minor versions don't break them.
- **Deprecate before removal.** Functionality slated for removal is marked
  deprecated first, with migration guidance — see [Deprecations](deprecations.md).
- **No silent breakage.** Breaking changes arrive only with a major version and
  are recorded in [`../CHANGELOG.md`](../CHANGELOG.md).

## How a client will select a version _(proposed)_

The exact mechanism is not finalised. The leading approach is an explicit,
opt-in version signal so that an unversioned client keeps getting a stable
default:

- A request header (e.g. `X-API-Version: 1`), **or**
- a version prefix in the path (e.g. `/api/v1/...`).

Expected behaviour once chosen:

- **Omitted** → the server assumes a documented default version (initially `1`).
- **Supported** → the server honours that version's contract.
- **Unsupported** → the server responds with a clear error (e.g. `400`) naming
  the versions it does support, rather than failing obscurely.

> The choice between header and path prefix, and the precise error shape, are
> open decisions. This section will be updated when they are settled.

```mermaid
flowchart TD
    C[Client request] --> Q{Version signalled?}
    Q -- no --> D[Use default version]
    Q -- yes --> S{Version supported?}
    S -- yes --> H[Serve that version's contract]
    S -- no --> E["Error: unsupported version<br/>(lists supported versions)"]
    D --> H
```

## Discovering the version _(proposed)_

A lightweight, unauthenticated way to discover the running API version (for
example a `version` field on an existing metadata response, or a dedicated
endpoint) is planned so clients can adapt at runtime. Not yet available.

## Relationship to application versions

The API version is **not** the LightBurn or MillMage application version. One
application release may ship a given API version; a later release may keep the
same API version (no contract change) or introduce a new one. The mapping is
recorded here and in [`../CHANGELOG.md`](../CHANGELOG.md):

| API version | LightBurn | MillMage |
|-------------|-----------|----------|
| 1.0 | 2.2.01 | — |
| 1.1 | 2.3 | 1.0 |

MillMage is covered from API 1.1. No stable MillMage release served the API
before MillMage 1.0; its pre-release builds tracked the API as it changed and
are not covered by any version guarantee.

## Guidance for integrators

- **Test against the versions you support**, and state them (e.g. "compatible
  with LightBurn REST API v1") — see [`../CERTIFICATION.md`](../CERTIFICATION.md).
- **Be liberal in what you accept**: ignore unknown fields, tolerate new enum
  values, don't assume field order.
- **Watch the changelog** for deprecations and new versions.
- **Don't depend on undocumented behaviour** — it is not covered by any version
  guarantee and may change without notice.

## Current state, concretely

- The current specification is `1.1.0` (`openapi.yaml` `info.version`).
- No version header or path prefix is required or honoured, and the running API
  version can't be queried yet. Infer it from the application version using the
  table above.
- Breaking changes are made only in a new major version, and are recorded in
  the changelog.
