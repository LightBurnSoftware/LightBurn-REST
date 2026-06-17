#!/usr/bin/env python
"""
Inkscape extension: send the drawing to LightBurn / MillMage.

Collects the selected shapes (or the whole document), de-duplicates coincident
line segments so shared edges are cut once, and uploads the result via the
REST API's `/api/file/upload`. The open document is never modified.
"""

import os

import inkex

import lightburn_client as lb
from dedupe import dedupe, to_d
from lightburn_common import (
    ROLE_ATTR, PRODUCT_ATTR, WORKSPACE_ATTR, FRAME_ROLE,
    bbox_of_points, uniform_scale, workspace_placement, aspect_mismatch,
)


def _points(segs):
    """Endpoint samples of a segment list, for a bounding box."""
    pts = []
    for s in segs:
        pts.append(s[1])
        pts.append(s[2])
    return pts


def element_segments(elem):
    """Absolute-coordinate segment list for one shape (see dedupe.py format)."""
    path = elem.path.to_absolute().transform(elem.composed_transform()).to_non_shorthand()
    segs = []
    cur = start = None
    for cmd in path:
        letter, a = cmd.letter, list(cmd.args)
        if letter == 'M':
            cur = start = (a[0], a[1])
        elif letter == 'L':
            p = (a[0], a[1]); segs.append(('L', cur, p, None)); cur = p
        elif letter == 'C':
            c1, c2, p = (a[0], a[1]), (a[2], a[3]), (a[4], a[5])
            segs.append(('C', cur, p, (c1, c2))); cur = p
        elif letter == 'Q':
            c1, p = (a[0], a[1]), (a[2], a[3])
            segs.append(('Q', cur, p, (c1,))); cur = p
        elif letter == 'A':
            rx, ry, rot, laf, sf, x, y = a
            segs.append(('A', cur, (x, y), (rx, ry, rot, laf, sf))); cur = (x, y)
        elif letter in ('Z', 'z'):
            if cur and start and cur != start:
                segs.append(('L', cur, start, None))
            cur = start
    return segs


class LightBurnSend(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--app", default="LightBurn")     # target name (hidden in .inx)
        pars.add_argument("--port", type=int, default=19520)
        pars.add_argument("--dedupe", type=inkex.Boolean, default=True)
        pars.add_argument("--selected_only", type=inkex.Boolean, default=True)
        pars.add_argument("--tab", default="opts")           # notebook page; unused

    def effect(self):
        elems = self._target_elements()
        if not elems:
            raise inkex.AbortExtension("Nothing to send — draw or select some shapes first.")

        shapes = [element_segments(e) for e in elems]
        # specified_style() folds in presentation attributes (stroke=, fill=) and
        # inherited styles — so colors survive (LightBurn maps them to cut layers).
        styles = [str(e.specified_style()) for e in elems]
        if self.options.dedupe:
            shapes = dedupe(shapes)

        placement, scale = self._frame_mapping(shapes)
        svg_bytes = self._build_svg(shapes, styles, scale)
        base_url = f"http://localhost:{self.options.port}"
        try:
            secret = lb.ensure_secret(base_url, f"Inkscape ({self.options.app})")
            if placement is not None:
                lb.upload(base_url, secret, svg_bytes, self._filename(),
                          position=placement, origin="bottom-left")
            else:
                lb.upload(base_url, secret, svg_bytes, self._filename())
        except lb.LBError as exc:
            raise inkex.AbortExtension(str(exc))
        framed = " (positioned via the workspace frame)" if placement else ""
        self.msg(f"Sent to {self.options.app}{framed}.")

    # -- helpers -------------------------------------------------------------

    def _target_elements(self):
        if self.options.selected_only and len(self.svg.selection):
            roots = list(self.svg.selection.values())
        else:
            roots = [self.svg]
        out = []
        for root in roots:
            for el in ([root] + list(root.descendants())):
                if not isinstance(el, inkex.ShapeElement):
                    continue
                if isinstance(el, (inkex.Group, inkex.Layer)):
                    continue
                if el.get(ROLE_ATTR) == FRAME_ROLE:
                    continue  # the workspace frame is a guide, never sent
                try:
                    if len(el.path):
                        out.append(el)
                except Exception:
                    pass
        return out

    def _find_frame(self, product):
        for el in self.svg.descendants():
            if el.get(ROLE_ATTR) == FRAME_ROLE and el.get(PRODUCT_ATTR) == product:
                return el
        return None

    def _frame_mapping(self, design_shapes):
        """(placement_mm, scale_mm_per_uu) from the workspace frame, or
        (None, None) when there's no usable frame for this target."""
        frame = self._find_frame(self.options.app.lower())
        spec = frame.get(WORKSPACE_ATTR) if frame is not None else None
        if not spec:
            return (None, None)
        try:
            w_mm, h_mm = (float(v) for v in spec.split("x"))
        except ValueError:
            return (None, None)

        frame_bbox = bbox_of_points(_points(element_segments(frame)))
        design_pts = [p for segs in design_shapes for p in _points(segs)]
        if not design_pts or frame_bbox[2] == 0:
            return (None, None)
        design_bbox = bbox_of_points(design_pts)

        scale = uniform_scale(w_mm, frame_bbox[2])
        if aspect_mismatch((w_mm, h_mm), (frame_bbox[2], frame_bbox[3])) > 0.02:
            self.msg("Note: the frame's aspect doesn't match the machine; using "
                     "its width for a uniform scale (no distortion).")
        return (workspace_placement(frame_bbox, design_bbox, scale), scale)

    def _build_svg(self, shapes, styles, scale=None):
        root = self.svg
        vb = root.get("viewBox")
        if scale is not None and vb:
            # 1 user unit -> `scale` mm, so geometry is sent at workspace size.
            nums = [float(v) for v in vb.replace(",", " ").split()]
            vbw, vbh = nums[2], nums[3]
            header = f'viewBox="{vb}" width="{vbw * scale:g}mm" height="{vbh * scale:g}mm"'
        else:
            header = " ".join(
                f'{a}="{root.get(a)}"' for a in ("width", "height", "viewBox") if root.get(a)
            )
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" {header}>']
        for segs, style in zip(shapes, styles):
            d = to_d(segs)
            if not d.strip():
                continue  # every edge was a duplicate of an earlier shape
            parts.append(f'  <path d="{d}" style="{style or "fill:none;stroke:#000000"}"/>')
        parts.append("</svg>")
        return "\n".join(parts).encode("utf-8")

    def _filename(self):
        path = self.document_path()
        if path:
            return os.path.splitext(os.path.basename(path))[0] + ".svg"
        return "drawing.svg"


if __name__ == "__main__":
    LightBurnSend().run()
