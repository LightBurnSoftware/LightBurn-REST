"""
Shared constants and pure geometry for the LightBurn / MillMage Inkscape tools.

The mapping helpers take plain numbers (no inkex), so they run standalone — see
the self-check in __main__.

Coordinate conventions
----------------------
- Inkscape user units: Y increases downward.
- Workspace (workpiece origin): bottom-left, Y increases upward, millimetres.
- The frame rectangle *is* the machine workspace. Its on-canvas extent maps to
  the workspace size, at a single uniform scale (machine aspect is locked).
"""

# Namespaced identifier so the frame is found regardless of stroke/colour and
# survives a save round-trip. Found by URI, so the serialised prefix can change.
NS = "https://lightburnsoftware.com/inkscape"
ROLE_ATTR      = f"{{{NS}}}role"        # "workspace-frame"
PRODUCT_ATTR   = f"{{{NS}}}product"     # "lightburn" | "millmage"
WORKSPACE_ATTR = f"{{{NS}}}workspace"   # "<width>x<height>" in mm
DEVICE_ATTR    = f"{{{NS}}}device"      # device profile name at creation time
FRAME_ROLE = "workspace-frame"

# Approximate brand colours for the frame stroke (tweak to taste).
PRODUCT_COLORS = {"lightburn": "#d40000", "millmage": "#7b16ff"}


def to_mm(value, unit):
    """Convert a distance in the app's display unit to millimetres."""
    return value * 25.4 if unit in ("in", "inch", "inches") else value


def bbox_of_points(points):
    """(left, top, width, height) enclosing an iterable of (x, y) points."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


def uniform_scale(workpiece_mm_x, frame_width_uu):
    """mm per Inkscape user unit. Single factor (aspect locked)."""
    return workpiece_mm_x / frame_width_uu


def workspace_placement(frame_bbox, design_bbox, scale):
    """Workspace-mm position of the design's bottom-left bbox corner.

    Both bboxes are (left, top, width, height) in Inkscape user units (Y-down).
    Returns (x_mm, y_mm) measured from the workpiece origin (bottom-left, Y-up).
    Pair with X-Origin = "bottom-left".
    """
    fr_left, fr_top, fr_w, fr_h = frame_bbox
    fr_bottom = fr_top + fr_h
    b_left, b_top, b_w, b_h = design_bbox
    b_bottom = b_top + b_h
    x_mm = (b_left - fr_left) * scale
    y_mm = (fr_bottom - b_bottom) * scale     # flip: distance above frame bottom
    return (x_mm, y_mm)


def aspect_mismatch(workpiece_mm, frame_uu):
    """Relative difference between the frame's aspect and the machine's.

    workpiece_mm and frame_uu are (width, height). 0.0 == perfectly matched.
    The send path warns (but proceeds) when this is large, since a distorted
    frame means the single uniform scale won't visually match both axes.
    """
    wx, wy = workpiece_mm
    fw, fh = frame_uu
    if wy == 0 or fh == 0:
        return 0.0
    return abs((fw / fh) - (wx / wy)) / (wx / wy)


if __name__ == "__main__":
    # Frame 100x100 uu == 200x200 mm workspace → scale 2.0 mm/uu.
    scale = uniform_scale(200.0, 100.0)
    assert scale == 2.0, scale
    # Design bbox occupying uu (10,10)-(30,30); bottom edge at uu y=30.
    x, y = workspace_placement((0, 0, 100, 100), (10, 10, 20, 20), scale)
    assert (x, y) == (20.0, 140.0), (x, y)   # 70 uu above bottom * 2 = 140
    # A square frame (1.0) for a 2:1 machine (2.0): |1-2|/2 = 0.5 relative.
    assert abs(aspect_mismatch((200, 100), (100, 100)) - 0.5) < 1e-9
    assert aspect_mismatch((200, 100), (200, 100)) == 0.0
    assert to_mm(2, "in") == 50.8 and to_mm(5, "mm") == 5
    print("ok: scale, placement, aspect-mismatch, to_mm")
