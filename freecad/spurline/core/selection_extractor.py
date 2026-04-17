"""
SpurLine — SelectionExtractor

Extracts a 2D Part.Face from an existing FreeCAD document object.

Unlike ProfileExtractor (which creates a gear from parameters),
this class works on shapes that already exist in the document —
FCGear objects, imported STEP parts, any Part::Feature with a solid.

Steps:
  1. Slice the shape at the user-positioned cutting plane
     (or at the Z midpoint if no placement is given)
  2. Re-center the resulting face at XY origin
  3. Optionally cut bore hole and keyway slot

This class is pure geometry — no UI, no file I/O.
"""

from __future__ import annotations
from typing import Optional

import FreeCAD as App
import Part

from freecad.spurline.core.profile_extractor import ProfileExtractor


class SelectionExtractor:
    """
    Extracts a 2D ``Part.Face`` from an existing document object's shape.
    """

    _Z_FLAT_TOLERANCE = 0.001  # mm — below this, treat shape as already 2D

    def extract_face(
        self,
        obj,
        bore: Optional[float] = None,
        keyway_w: Optional[float] = None,
        placement: Optional[App.Placement] = None,
    ) -> Part.Face:
        """
        Extract a 2D profile from ``obj.Shape``.

        Parameters
        ----------
        obj : App.DocumentObject
            Must have a ``.Shape`` attribute with geometry.
        bore : float or None
            Bore diameter in mm.  None or 0 means no bore.
        keyway_w : float or None
            Keyway width in mm.  None or 0 means no keyway.
        placement : App.Placement or None
            The cutting plane's placement.  If provided, the shape is
            sliced at this plane (arbitrary position and orientation).
            If None, falls back to slicing at the Z midpoint.

        Returns
        -------
        Part.Face
            Centered at XY origin, in the Z=0 plane.

        Raises
        ------
        RuntimeError
            If the object has no usable shape or slicing fails.
        """
        if not self.has_shape(obj):
            raise RuntimeError(
                f"Object '{getattr(obj, 'Label', '?')}' has no usable Shape."
            )

        shape = self._global_shape(obj)
        bb = shape.BoundBox

        if bb.ZLength < self._Z_FLAT_TOLERANCE:
            face = self._face_from_flat(shape)
        elif placement is not None:
            face = self._slice_at_plane(shape, placement)
        else:
            z_mid = (bb.ZMin + bb.ZMax) / 2.0
            face = self._slice_at_z(shape, z_mid)

        face = self._recenter(face)

        # Optional bore / keyway using ProfileExtractor's static methods
        params = {"bore": bore, "keyway_w": keyway_w}
        face = ProfileExtractor._cut_bore(face, params)
        face = ProfileExtractor._cut_keyway(face, params)

        return face

    # ------------------------------------------------------------------
    # Static helpers for UI display
    # ------------------------------------------------------------------

    @staticmethod
    def has_shape(obj) -> bool:
        """Return True if *obj* has a non-empty Shape."""
        shape = getattr(obj, "Shape", None)
        if shape is None:
            return False
        return not shape.isNull()

    @staticmethod
    def get_type_info(obj) -> str:
        """
        Human-readable type summary.

        Shows FCGear-specific properties when available, otherwise
        falls back to the object's TypeId.
        """
        # Involute gear / rack
        if hasattr(obj, "num_teeth") and hasattr(obj, "module"):
            kind = "Rack" if hasattr(obj, "add_endings") else "Involute"
            return f"{kind} {obj.num_teeth}T m{obj.module}"

        # Timing pulley (FCGear uses "type" for the belt profile)
        if hasattr(obj, "num_teeth") and hasattr(obj, "type"):
            return f"Timing {obj.type} {obj.num_teeth}T"

        return getattr(obj, "TypeId", type(obj).__name__)

    @staticmethod
    def get_size_info(obj) -> str:
        """Bounding-box dimensions string, e.g. '45.2 x 45.2 mm'."""
        if not SelectionExtractor.has_shape(obj):
            return ""
        bb = SelectionExtractor._global_shape(obj).BoundBox
        return f"{bb.XLength:.1f} x {bb.YLength:.1f} mm"

    # ------------------------------------------------------------------
    # Private geometry helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _global_shape(obj) -> Part.Shape:
        """
        Return a copy of *obj*'s shape in global document coordinates.

        ``obj.Shape`` is in the parent container's local space.  If the
        object sits inside an ``App::Part`` or ``PartDesign::Body`` that
        has its own Placement, we need to apply the full global transform
        so the shape aligns with top-level objects like the cutting plane.
        """
        shape = obj.Shape.copy()
        if hasattr(obj, "getGlobalPlacement"):
            shape.Placement = obj.getGlobalPlacement()
        return shape

    @staticmethod
    def _slice_at_plane(shape: Part.Shape, placement: App.Placement) -> Part.Face:
        """
        Slice *shape* at an arbitrary cutting plane defined by *placement*.

        Transforms the shape into the plane's local coordinate system
        (where the cutting plane becomes Z=0), slices there using the
        fast native ``Shape.slice()``, then returns the result in the
        plane's local XY — already flat 2D.
        """
        inv = placement.inverse()
        transformed = shape.copy()
        transformed.transformShape(inv.Matrix)
        return SelectionExtractor._slice_at_z(transformed, 0.0)

    @staticmethod
    def _slice_at_z(shape: Part.Shape, z: float) -> Part.Face:
        """
        Slice *shape* at height *z* and return the resulting face,
        preserving internal holes (bore, offset holes, etc.).

        Uses ``Shape.slice()`` which is a native cross-section
        operation — much faster than building a large helper plane
        and running a boolean ``section()``.
        """
        wires = shape.slice(App.Vector(0, 0, 1), z)

        if not wires:
            raise RuntimeError(
                "Slicing the shape produced no wires.  "
                "The object may be empty or not intersect the slice plane."
            )

        # Sort largest-first so wires[0] is the outer profile
        wires = sorted(
            wires,
            key=lambda w: w.BoundBox.XLength * w.BoundBox.YLength,
            reverse=True,
        )

        # Build the face with holes via Part::FaceMakerBullseye —
        # it treats the outermost wire as the boundary and any
        # contained wires as holes, in a single pass.
        try:
            face = Part.makeFace(wires, "Part::FaceMakerBullseye")
        except Exception:
            # Fallback: build from outer wire and cut holes individually
            face = Part.Face(wires[0])
            for hole_wire in wires[1:]:
                hole_face = Part.Face(hole_wire)
                cut_result = face.cut(hole_face)
                if cut_result.Faces:
                    face = cut_result.Faces[0]

        return face

    @staticmethod
    def _face_from_flat(shape: Part.Shape) -> Part.Face:
        """
        Extract a face from a shape that is already 2D (near-zero Z extent).
        """
        if shape.Faces:
            # Already has faces — pick the largest
            return max(
                shape.Faces,
                key=lambda f: f.BoundBox.XLength * f.BoundBox.YLength,
            )

        if shape.Wires:
            return Part.Face(shape.Wires[0])

        raise RuntimeError(
            "The selected object is flat but contains no faces or wires."
        )

    @staticmethod
    def _recenter(face: Part.Face) -> Part.Face:
        """Translate *face* so its bounding-box center sits at the origin."""
        bb = face.BoundBox
        cx = (bb.XMin + bb.XMax) / 2.0
        cy = (bb.YMin + bb.YMax) / 2.0
        cz = (bb.ZMin + bb.ZMax) / 2.0
        centered = face.copy()
        centered.translate(App.Vector(-cx, -cy, -cz))
        return centered
