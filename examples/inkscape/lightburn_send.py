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
        pars.add_argument("--port", type=int, default=19522)
        pars.add_argument("--dedupe", type=inkex.Boolean, default=True)
        pars.add_argument("--selected_only", type=inkex.Boolean, default=True)

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

        svg_bytes = self._build_svg(shapes, styles)
        base_url = f"http://localhost:{self.options.port}"
        try:
            secret = lb.ensure_secret(base_url)
            lb.upload(base_url, secret, svg_bytes, self._filename())
        except lb.LBError as exc:
            raise inkex.AbortExtension(str(exc))
        self.msg("Sent to LightBurn / MillMage.")

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
                try:
                    if len(el.path):
                        out.append(el)
                except Exception:
                    pass
        return out

    def _build_svg(self, shapes, styles):
        root = self.svg
        attrs = " ".join(
            f'{a}="{root.get(a)}"' for a in ("width", "height", "viewBox") if root.get(a)
        )
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" {attrs}>']
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
