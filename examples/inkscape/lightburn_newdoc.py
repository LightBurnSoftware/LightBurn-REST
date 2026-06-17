#!/usr/bin/env python
"""
Inkscape extension: size the document to the LightBurn / MillMage workspace.

Run it on a fresh, blank document. It fetches the machine's workspace size via
GET /api/project and sets the page to match, at 1 user unit = 1 mm — so a
design drawn at real size sends at real size. (Inkscape extensions act on the
open document; they can't spawn a new window, so make a new document first.)
"""

import inkex

import lightburn_client as lb
from lightburn_common import to_mm, WORKSPACE_ATTR, PRODUCT_ATTR, DEVICE_ATTR


class NewDocFromWorkspace(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--app", default="LightBurn")
        pars.add_argument("--host", default="localhost")
        pars.add_argument("--port", type=int, default=19520)
        pars.add_argument("--tab", default="opts")

    def effect(self):
        base_url = f"http://{self.options.host}:{self.options.port}"
        try:
            secret = lb.ensure_secret(base_url, f"Inkscape ({self.options.app})")
            project = lb.get_project(base_url, secret)
        except lb.LBError as exc:
            raise inkex.AbortExtension(str(exc))

        try:
            ws = project["workspace"]["workpiece_size"]
            unit = project.get("units", {}).get("distance", "mm")
            w = to_mm(float(ws["x"]), unit)
            h = to_mm(float(ws["y"]), unit)
        except (KeyError, TypeError, ValueError):
            raise inkex.AbortExtension("Could not read workspace size from the app.")

        svg = self.svg
        svg.set("width", f"{w:g}mm")
        svg.set("height", f"{h:g}mm")
        svg.set("viewBox", f"0 0 {w:g} {h:g}")     # 1 user unit = 1 mm
        svg.set(WORKSPACE_ATTR, f"{w:g}x{h:g}")     # tag so Send can map to the page
        svg.set(PRODUCT_ATTR, self.options.app.lower())
        device = project.get("device", {}).get("name", "")
        if device:
            svg.set(DEVICE_ATTR, device)            # for Send's device-mismatch check
        try:
            svg.namedview.set("inkscape:document-units", "mm")
        except Exception:
            pass
        self.msg(f"Document set to the {self.options.app} workspace: {w:g} x {h:g} mm.")


if __name__ == "__main__":
    NewDocFromWorkspace().run()
