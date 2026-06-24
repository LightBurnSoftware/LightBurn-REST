# Examples

Reference clients for the LightBurn / MillMage REST API.

| Example | Description | License |
|---------|-------------|---------|
| [`spurline/`](spurline/) | FreeCAD workbench: generate gear profiles and send them to LightBurn / MillMage | **GPL-3.0** ([LICENSE](spurline/LICENSE)) |
| [`inkscape/`](inkscape/) | Inkscape extensions: draw the workspace, de-duplicate shared edges, send the drawing | **GPL-3.0** ([LICENSE](inkscape/LICENSE)) |

## Licensing

Example code in this directory is provided under the **MIT License**
([LICENSE](LICENSE)) **unless a subdirectory contains its own LICENSE file**, in
which case that license governs everything in that subdirectory.

Both current examples carry their own **GPL-3.0** license because they build on
GPL-licensed host software — the FreeCAD workbench links FreeCAD and the FCGear
addon, and the Inkscape extensions import Inkscape's `inkex` module. Combining
with those libraries makes the result a derivative work under the GPL, so MIT
cannot apply to them.

The MIT default is intended for self-contained, dependency-free examples (such
as a future standalone API client). When in doubt, the nearest enclosing
LICENSE file wins.

These licenses cover the example code only. They do not apply to LightBurn,
MillMage, the API implementations, or any other proprietary LightBurn Software
materials — see [`../NOTICE.md`](../NOTICE.md).
