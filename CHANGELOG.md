# Changelog

This changelog records changes to the LightBurn / MillMage REST API
documentation and specification. Dates use ISO 8601.

## Unreleased

Specification synchronised with the current LightBurn / MillMage
implementation. The API is still pre-stable (see `docs/versioning.md`), so the
breaking changes below ship without a version bump.

### Added

- `distance_units` (`mm` / `in`) on `GET /api/units`, `GET /api/jog/settings`
  and the `settings` event, alongside `units`.
- `in/s` added to the `units` enum.
- Multiple instances section describing which running copy serves the port and
  what that means for a paired secret (`docs/overview.md`, spec description).
- `project_write` capability, requested through `POST /api/connect`.
- `POST /api/cuts/{index}` — partial update of one cut setting (LightBurn) or
  operation (MillMage). Validated as a whole, applied as a single undo step,
  and returns `409` while the cut settings / operation editor is open.
- `LaserCutParams` schema shared by a cut's base layer and its sub-layers,
  adding dual-source (`min_power_2`, `max_power_2`, `laser1_enabled`,
  `laser2_enabled`), `alt_source`, `q_pulse_width` and `fiber_pulse_width`.
  Image cuts gain the source and pulse fields too.
- Full sub-layer entries in `LaserCut.sub_layers`: `index`, `name`, `enabled`,
  `mode` and `params`.
- `device.laser` on `GET /api/project` (LightBurn): controller, galvo,
  flying galvo, UV, source count, MOPA and fiber flags.
- `CncCut.shape_count`, `CncCut.settings` (every stored operation property)
  and `CncCut.shared_fields`.
- `vcarve` and `vcarve_clear` values for `CncCut.operation`.

### Fixed

- `units` reported `mm/s` whenever the application's control units were set to
  `in/sec` or to either mixed mode (inch distances with metric speeds). A
  client converting on the reported unit was wrong by a factor of 25.4 — the
  same class of error corrected in the Inkscape examples last release. `units`
  is now strictly the speed unit and always accurate; the distance unit moved
  to the new `distance_units` field.
- `cut.index` on `GET /api/material-library` entries was `0`, which looked
  like a valid `/api/cuts` position. Library entries have no position in the
  cut list, so `index` and `layer_index` are now both `-1`.
- `POST /api/cuts/{index}` returned `409` instead of `404` for an
  out-of-range index while the cut editor was open.
- The state endpoints (`/api/status`, `/api/position`, `/api/jog/settings`,
  `/api/units`, `/api/events/poll`) returned empty objects when no machine was
  attached, and for a moment after the application started. They now always
  answer: `connected` is `false`, and settings and units report real values.

### Changed (breaking)

- `CncCut` no longer has `layer_index` or `priority` — operations attach to
  shapes and run in list order (`index`).
- `CncCut` no longer has top-level `vacuum` and `coolant`; they are now keys in
  `CncCut.settings`.
- `LaserCut.sub_layers` items no longer have the top-level `speed`,
  `max_power` and `z_offset` fields; these are now in each item's `params`.

### Clarified

- Units: positions and the `/api/project` `workspace` are always in mm;
  MillMage operation `settings` are always mm and mm/s. LightBurn cut values
  and the MillMage `tool` block use display units, read from `units` and
  `distance_units`. `/api/project` `units.distance` is a translated UI label
  for display only, not for conversion.
- `GET /api/status` answers with `connected: false` rather than failing when
  no machine is attached.
- `POST /api/file/open` is served by the application's own API surface only.
- The **Show Secret…** button appears only while network access is enabled,
  and the dialog is **Manage API Security** (`docs/authentication.md`).
- Connection refused and `401` mean different things; the authentication
  failure table now distinguishes them.
- `JobState.progress` is optional — absent while idle and on controllers that
  can't report execution progress (e.g. Ruida during a cut).
- `Position` omits any axis the controller doesn't report.
- `GET /api/project` returns only `filename`, `modified` and `shape_count`
  when no project is loaded.
- `GET /api/cuts` on LightBurn is a fixed-size list (30 cut layers, 2 tool
  layers, 1 internal cut, 30 image cuts); on MillMage it is the operation list
  in order.
- `GET /api/events` opens with a `:connected` comment; "on change" events
  aren't replayed to new subscribers, so poll once after connecting. The event
  table now names each event's `data` schema. A `401` has an empty body.
- `POST /api/file/open` reports its result through the `file_imported` event.

### Documentation

- New cut settings guide (`docs/cut-settings.md`).
- Capabilities, API reference, overview, README, getting started and
  uploading guides updated for `project_write`, units and event behaviour.

### Safety & policy

- Clarified operator responsibility for reviewing and verifying API-modified
  job settings and operational parameters before machine operation
  (`SAFETY.md`, `API-EULA.md`, `POLICY.md`, `docs/overview.md`).
- Renamed the README's scope section to Intended Use and linked safety guidance.
- Expanded responsible-disclosure coverage for unauthorized access, capability
  bypasses/escalation, secret or token exposure, and unexpected parameter changes
  (`DISCLOSURE.md`).
- Simplified the examples' GPL-3.0 licensing explanation without changing the
  MIT default or per-subdirectory licenses (`examples/README.md`).

### Examples

- Inkscape extensions: read the `/api/project` workspace size as mm. They
  previously converted it from the display units, which produced a workspace
  25.4× too large when LightBurn / MillMage was set to inches.

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
