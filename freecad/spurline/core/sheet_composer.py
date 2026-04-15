"""
SpurLine — SheetComposer

Responsible for:
  1. Arranging one or more copies of a Part.Face in a grid layout
  2. Adding them to the FreeCAD document (for preview)
  3. Exporting to DXF or SVG — either to a file path or to bytes in memory
     (bytes path is used for the REST POST payload)
"""

from __future__ import annotations

import math
import os
import tempfile
from typing import List, Tuple

import FreeCAD as App
import Part


class SheetComposer:
    """
    Arranges gear profile copies and handles export.

    The grid is computed as a square-ish arrangement:
      cols = ceil(sqrt(copies))
      rows = ceil(copies / cols)

    Spacing between copies is 15% of the bounding-box dimension.
    """

    SPACING_FACTOR = 1.15   # centre-to-centre = bbox_size * this factor

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def place_in_document(
        self,
        face: Part.Face,
        copies: int,
    ) -> List[App.DocumentObject]:
        """
        Add ``copies`` translated instances of ``face`` to the active
        FreeCAD document as Part::Feature objects.

        Returns the list of document objects created.
        """
        doc      = App.ActiveDocument
        features = []
        grid     = self._grid_positions(face, copies)

        for i, (dx, dy) in enumerate(grid):
            f = face.copy()
            f.translate(App.Vector(dx, dy, 0))

            feat        = doc.addObject("Part::Feature", f"SpurLine_Profile_{i + 1}")
            feat.Shape  = f
            features.append(feat)

        doc.recompute()
        return features

    def to_dxf_bytes(self, face: Part.Face, copies: int) -> bytes:
        """
        Export the composed sheet to DXF and return the file contents
        as ``bytes`` (suitable for a REST POST body).

        Uses a temporary file internally because FreeCAD's importDXF
        module only writes to disk.
        """
        return self._export_to_bytes(face, copies, fmt="dxf")

    def to_svg_bytes(self, face: Part.Face, copies: int) -> bytes:
        """
        Export the composed sheet to SVG and return the file contents
        as ``bytes``.
        """
        return self._export_to_bytes(face, copies, fmt="svg")

    def export_to_file(self, face: Part.Face, copies: int, path: str):
        """
        Export the composed sheet to a file at ``path``.
        Format is inferred from the file extension (.dxf or .svg).
        """
        fmt = os.path.splitext(path)[1].lstrip(".").lower()
        if fmt not in ("dxf", "svg"):
            raise ValueError(f"Unsupported export format: {fmt!r}")
        self._write_to_path(face, copies, path, fmt)

    # ------------------------------------------------------------------
    # Multi-face public API
    # ------------------------------------------------------------------

    def place_multi_in_document(
        self,
        items: List[Tuple[Part.Face, int]],
    ) -> List[App.DocumentObject]:
        """
        Place multiple different faces, each with its own copy count,
        into the active document.

        Parameters
        ----------
        items : list of (Part.Face, int)
            Each tuple is (face, number_of_copies).

        Returns
        -------
        list of App.DocumentObject
        """
        doc = App.ActiveDocument
        features = []

        for face, dx, dy in self._multi_grid_positions(items):
            f = face.copy()
            f.translate(App.Vector(dx, dy, 0))
            feat = doc.addObject(
                "Part::Feature",
                f"SpurLine_Profile_{len(features) + 1}",
            )
            feat.Shape = f
            features.append(feat)

        doc.recompute()
        return features

    def multi_to_dxf_bytes(
        self,
        items: List[Tuple[Part.Face, int]],
    ) -> bytes:
        """Export a multi-face sheet to DXF and return as bytes."""
        return self._export_multi_to_bytes(items, fmt="dxf")

    def multi_to_svg_bytes(
        self,
        items: List[Tuple[Part.Face, int]],
    ) -> bytes:
        """Export a multi-face sheet to SVG and return as bytes."""
        return self._export_multi_to_bytes(items, fmt="svg")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _grid_positions(self, face: Part.Face, copies: int) -> List[tuple]:
        """
        Return a list of (dx, dy) translation vectors for ``copies``
        copies arranged in a grid.
        """
        bb     = face.BoundBox
        step_x = bb.XLength * self.SPACING_FACTOR
        step_y = bb.YLength * self.SPACING_FACTOR
        cols   = math.ceil(math.sqrt(copies))

        positions = []
        for i in range(copies):
            col = i % cols
            row = i // cols
            positions.append((col * step_x, row * step_y))
        return positions

    def _export_to_bytes(self, face: Part.Face, copies: int, fmt: str) -> bytes:
        """
        Write to a temp file, read back as bytes, delete temp file.
        """
        suffix = f".{fmt}"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name

        try:
            self._write_to_path(face, copies, tmp_path, fmt)
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _write_to_path(self, face: Part.Face, copies: int, path: str, fmt: str):
        """
        Create document features for the grid, export them, then
        clean them up so the document stays tidy.
        """
        # We need to add temporary doc objects for importDXF/importSVG
        doc      = App.ActiveDocument
        features = []
        grid     = self._grid_positions(face, copies)

        for i, (dx, dy) in enumerate(grid):
            f = face.copy()
            f.translate(App.Vector(dx, dy, 0))
            feat       = doc.addObject("Part::Feature", f"_SpurLine_tmp_{i}")
            feat.Shape = f
            features.append(feat)

        doc.recompute()

        try:
            if fmt == "dxf":
                import Draft        # must be imported before importDXF
                import importDXF
                importDXF.export(features, path)
            elif fmt == "svg":
                import importSVG
                importSVG.export(features, path)
        finally:
            # Always clean up temporary objects
            for feat in features:
                try:
                    doc.removeObject(feat.Name)
                except Exception:
                    pass
            doc.recompute()

    # ------------------------------------------------------------------
    # Multi-face private helpers
    # ------------------------------------------------------------------

    def _multi_grid_positions(
        self,
        items: List[Tuple[Part.Face, int]],
    ) -> List[Tuple[Part.Face, float, float]]:
        """
        Compute layout for multiple face types.

        Each item's copies form a horizontal strip.  Strips are stacked
        vertically with spacing between them.

        Returns
        -------
        list of (face, dx, dy)
            One entry per individual copy across all items.
        """
        result = []
        y_offset = 0.0

        for face, copies in items:
            if copies < 1:
                continue
            bb = face.BoundBox
            step_x = bb.XLength * self.SPACING_FACTOR

            for col in range(copies):
                result.append((face, col * step_x, y_offset))

            y_offset += bb.YLength * self.SPACING_FACTOR

        return result

    def _export_multi_to_bytes(
        self,
        items: List[Tuple[Part.Face, int]],
        fmt: str,
    ) -> bytes:
        """Write multi-face sheet to a temp file, read back as bytes."""
        suffix = f".{fmt}"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name

        try:
            self._write_multi_to_path(items, tmp_path, fmt)
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _write_multi_to_path(
        self,
        items: List[Tuple[Part.Face, int]],
        path: str,
        fmt: str,
    ):
        """Create temp doc objects for the multi-face grid, export, clean up."""
        doc = App.ActiveDocument
        features = []

        for face, dx, dy in self._multi_grid_positions(items):
            f = face.copy()
            f.translate(App.Vector(dx, dy, 0))
            feat = doc.addObject("Part::Feature", f"_SpurLine_tmp_{len(features)}")
            feat.Shape = f
            features.append(feat)

        doc.recompute()

        try:
            if fmt == "dxf":
                import Draft
                import importDXF
                importDXF.export(features, path)
            elif fmt == "svg":
                import importSVG
                importSVG.export(features, path)
        finally:
            for feat in features:
                try:
                    doc.removeObject(feat.Name)
                except Exception:
                    pass
            doc.recompute()
