#!/usr/bin/env python
"""
Inkscape extension: draw the LightBurn / MillMage workspace frame.

Fetches the machine's workspace size via GET /api/project and draws a dotted,
brand-coloured background rectangle at that size. The frame's workspace
dimensions (mm) are stored on it so "Send to ..." can map geometry into the
workspace without another API call. Move or resize the frame to position your
designs; the send maps them to match.

Re-running updates the existing frame's stored dimensions rather than adding a
second one.
"""

import inkex

import lightburn_client as lb
from lightburn_common import (
    ROLE_ATTR, PRODUCT_ATTR, WORKSPACE_ATTR, DEVICE_ATTR, FRAME_ROLE,
    PRODUCT_COLORS, to_mm,
)


class DrawWorkspaceFrame(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--app", default="LightBurn")
        pars.add_argument("--host", default="localhost")
        pars.add_argument("--port", type=int, default=19520)
        pars.add_argument("--reset_auth", type=inkex.Boolean, default=False)
        pars.add_argument("--tab", default="opts")

    def effect(self):
        product = self.options.app.lower()
        base_url = f"http://{self.options.host}:{self.options.port}"
        if self.options.reset_auth:
            self.msg(lb.forget_secret_message(base_url, self.options.app))
        try:
            secret = lb.ensure_secret(base_url, f"Inkscape ({self.options.app})")
            project = lb.get_project(base_url, secret)
        except lb.LBError as exc:
            raise inkex.AbortExtension(str(exc))

        try:
            ws = project["workspace"]["workpiece_size"]
            unit = project.get("units", {}).get("distance", "mm")
            w_mm = to_mm(float(ws["x"]), unit)
            h_mm = to_mm(float(ws["y"]), unit)
        except (KeyError, TypeError, ValueError):
            raise inkex.AbortExtension("Could not read workspace size from the app.")
        device = project.get("device", {}).get("name", "")

        existing = self._find_frame(product)
        if existing is not None:
            existing.set(WORKSPACE_ATTR, f"{w_mm:g}x{h_mm:g}")
            if device:
                existing.set(DEVICE_ATTR, device)
            self.msg(f"{self.options.app} workspace frame refreshed "
                     f"({w_mm:g} x {h_mm:g} mm). Move or resize it to position designs.")
            return

        self._create_frame(product, w_mm, h_mm, device)
        self.msg(f"Drew {self.options.app} workspace frame ({w_mm:g} x {h_mm:g} mm). "
                 f"Move or resize it to position your designs, then Send.")

    # -- helpers -------------------------------------------------------------

    def _find_frame(self, product):
        for el in self.svg.descendants():
            if el.get(ROLE_ATTR) == FRAME_ROLE and el.get(PRODUCT_ATTR) == product:
                return el
        return None

    def _create_frame(self, product, w_mm, h_mm, device=""):
        uu = self.svg.unittouu
        rect = inkex.Rectangle(
            x="0", y="0",
            width=str(uu(f"{w_mm}mm")), height=str(uu(f"{h_mm}mm")),
        )
        color = PRODUCT_COLORS.get(product, "#d40000")
        rect.style = inkex.Style({
            "fill": "none",
            "stroke": color,
            "stroke-width": str(uu("0.3mm")),
            "stroke-dasharray": f"{uu('0.8mm')},{uu('1.4mm')}",
            "stroke-opacity": "0.85",
        })
        rect.set(ROLE_ATTR, FRAME_ROLE)
        rect.set(PRODUCT_ATTR, product)
        rect.set(WORKSPACE_ATTR, f"{w_mm:g}x{h_mm:g}")
        if device:
            rect.set(DEVICE_ATTR, device)
        rect.set("inkscape:label", f"{self.options.app} workspace")
        rect.set("id", f"lightburn-frame-{product}")
        self.svg.insert(0, rect)   # background (drawn first → behind designs)


if __name__ == "__main__":
    DrawWorkspaceFrame().run()
