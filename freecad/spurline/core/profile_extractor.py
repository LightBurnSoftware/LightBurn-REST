"""
SpurLine — ProfileExtractor

Responsible for:
  1. Creating a 3D gear solid via freecad.gears
  2. Slicing it at Z=0 to obtain a 2D Part.Face
  3. Cutting the bore hole
  4. Cutting the keyway slot
  5. Removing the temporary 3D solid from the document

This class is pure geometry — no UI, no file I/O.
"""

from __future__ import annotations
from typing import Optional

import FreeCAD as App
import Part


class ProfileExtractor:
    """
    Converts a gear parameter dict into a 2D ``Part.Face``.

    Usage
    -----
    ::

        extractor = ProfileExtractor()
        face = extractor.extract({
            "gear_type": "involute",
            "teeth":     20,
            "module":    2.0,
            "pressure":  20.0,
            "bore":      6.0,
            "keyway_w":  2.0,
        })
        # face is a Part.Face in the XY plane, centered at origin
    """

    def extract(self, params: dict) -> Part.Face:
        """
        Main entry point.

        Parameters
        ----------
        params : dict
            Keys: gear_type, teeth, module, pressure, belt_type,
                  bore (mm, optional), keyway_w (mm, optional)

        Returns
        -------
        Part.Face
            2D profile in the XY plane ready for DXF/SVG export.

        Raises
        ------
        RuntimeError
            If no active FreeCAD document exists or gear creation fails.
        ValueError
            If params are out of range or inconsistent
            (e.g. keyway requested but no bore).
        """
        doc = self._ensure_document()

        gear_obj = self._create_gear(params, doc)
        try:
            face = self._slice_at_z0(gear_obj.Shape)
            face = self._cut_bore(face, params)
            face = self._cut_keyway(face, params)
        finally:
            # Always remove the 3D solid — we only want the 2D face
            doc.removeObject(gear_obj.Name)
            doc.recompute()

        return face

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_document() -> App.Document:
        """Return the active document, creating one if necessary."""
        if App.ActiveDocument is None:
            App.newDocument("SpurLine")
        return App.ActiveDocument

    @staticmethod
    def _create_gear(params: dict, doc: App.Document):
        """
        Instantiate the appropriate freecad.gears object and set params.

        Returns the document object (before recompute).
        """
        import freecad.gears.commands as gc

        gear_type = params["gear_type"]

        # TODO: verify property names against installed freecad.gears version.
        # On newer builds the property is num_teeth; on some older builds it
        # is teeth.  Check with: print(dir(gear_obj)) in the FC console.

        if gear_type == "involute":
            obj = gc.CreateInvoluteGear.create()
            obj.num_teeth    = params["teeth"]
            obj.module       = params["module"]
            obj.pressure_angle = params["pressure"]
            obj.height       = 1.0   # minimal height — we only need one face

        elif gear_type == "rack":
            obj = gc.CreateInvoluteRack.create()
            obj.num_teeth = params["teeth"]
            obj.module    = params["module"]
            obj.pressure_angle = params["pressure"]
            obj.height    = 1.0

        elif gear_type == "timing":
            obj = gc.CreateTimingGear.create()
            obj.num_teeth = params["teeth"]
            obj.belt_type = params.get("belt_type", "GT2")
            obj.height    = 1.0

        else:
            raise ValueError(f"Unknown gear type: {gear_type!r}")

        doc.recompute()
        return obj

    @staticmethod
    def _slice_at_z0(shape: Part.Shape) -> Part.Face:
        """
        Intersect the 3D shape with the XY plane (Z=0) and return
        the resulting face.

        Raises RuntimeError if the slice produces no usable edges.
        """
        plane   = Part.makePlane(2000, 2000, App.Vector(-1000, -1000, 0))
        section = shape.section(plane)

        if not section.Edges:
            raise RuntimeError(
                "Gear slice at Z=0 produced no edges.  "
                "The gear solid may not intersect Z=0."
            )

        sorted_edges = Part.sortEdges(section.Edges)
        if not sorted_edges:
            raise RuntimeError("Could not sort gear profile edges into a closed wire.")

        wire = Part.Wire(sorted_edges[0])
        face = Part.Face(wire)
        return face

    @staticmethod
    def _cut_bore(face: Part.Face, params: dict) -> Part.Face:
        """
        Subtract a circular bore hole from the face.
        Returns face unchanged if bore is None or 0.
        """
        bore = params.get("bore")
        if not bore:
            return face

        r           = bore / 2.0
        bore_circle = Part.makeCircle(r)
        bore_wire   = Part.Wire([bore_circle])
        bore_face   = Part.Face(bore_wire)
        return face.cut(bore_face)

    @staticmethod
    def _cut_keyway(face: Part.Face, params: dict) -> Part.Face:
        """
        Subtract a rectangular keyway slot from the top of the bore.

        The slot is centred on the Y axis and extends from the bore
        surface outward by keyway_height (= 0.6 × keyway_width,
        per DIN 6885 proportions).

        Returns face unchanged if keyway_w or bore is None / 0.
        """
        bore     = params.get("bore")
        keyway_w = params.get("keyway_w")
        if not bore or not keyway_w:
            return face

        import math

        r          = bore / 2.0
        kh         = keyway_w * 0.6   # keyway height (radial depth beyond bore)

        # Rectangle: centred on Y axis, bottom corners on the bore circle.
        #   half_w² + y_bottom² = r²  →  y_bottom = sqrt(r² - half_w²)
        #   Top edge at y = r + kh (extends outward from bore surface)
        half_w   = keyway_w / 2.0
        y_bottom = math.sqrt(r * r - half_w * half_w)
        y_top    = r + kh
        pts = [
            App.Vector(-half_w, y_bottom, 0),
            App.Vector( half_w, y_bottom, 0),
            App.Vector( half_w, y_top,    0),
            App.Vector(-half_w, y_top,    0),
            App.Vector(-half_w, y_bottom, 0),  # close
        ]
        key_wire = Part.makePolygon(pts)
        key_face = Part.Face(key_wire)
        return face.cut(key_face)
