"""
Exact-coincident line-segment de-duplication.

When adjacent shapes share an edge, a laser cuts that edge twice. This drops
the duplicates so every physical segment is cut once: the first shape to use an
edge keeps it, later shapes lose it (leaving a gap there).

Pure geometry — no inkex dependency, so it runs standalone (see __main__).

ponytail: dedupes straight LINE segments only; curves always pass through.
Partial/collinear overlaps and coincident curves are a known ceiling — revisit
with a geometric boolean-union approach if double-cut curves become a problem.

Segment representation (absolute coords):
    ('L', start, end, None)              straight line
    ('C', start, end, (c1, c2))          cubic bezier
    ('Q', start, end, (c1,))             quadratic bezier
    ('A', start, end, (rx, ry, rot, laf, sf))   elliptical arc
where each point is an (x, y) tuple.
"""

ROUND = 3  # decimal places (~SVG user-unit precision) for the coincidence test


def _key(a, b):
    """Direction-independent key for the segment between points a and b."""
    pa = (round(a[0], ROUND), round(a[1], ROUND))
    pb = (round(b[0], ROUND), round(b[1], ROUND))
    return frozenset((pa, pb))


def dedupe(shapes):
    """Remove duplicate line segments across all shapes.

    ``shapes`` is an ordered list of shape segment-lists. Returns a new list
    of segment-lists; the first occurrence of each line segment is kept and
    later duplicates are dropped. Ordering decides which shape keeps a shared
    edge. Curves are never dropped.
    """
    seen = set()
    out = []
    for segs in shapes:
        kept = []
        for seg in segs:
            if seg[0] == 'L':
                if seg[1] == seg[2]:
                    continue                 # zero-length, drop quietly
                k = _key(seg[1], seg[2])
                if k in seen:
                    continue                 # shared edge already emitted
                seen.add(k)
            kept.append(seg)
        out.append(kept)
    return out


def _fmt(p):
    return f"{p[0]:g},{p[1]:g}"


def to_d(segments, eps=1e-4):
    """Rebuild an SVG path ``d`` string from kept segments, inserting a moveto
    wherever the pen has to jump because a segment was dropped."""
    out = []
    pen = None
    for seg in segments:
        kind, start, end = seg[0], seg[1], seg[2]
        if pen is None or abs(pen[0] - start[0]) > eps or abs(pen[1] - start[1]) > eps:
            out.append(f"M {_fmt(start)}")
        if kind == 'L':
            out.append(f"L {_fmt(end)}")
        elif kind == 'C':
            c1, c2 = seg[3]
            out.append(f"C {_fmt(c1)} {_fmt(c2)} {_fmt(end)}")
        elif kind == 'Q':
            (c1,) = seg[3]
            out.append(f"Q {_fmt(c1)} {_fmt(end)}")
        elif kind == 'A':
            rx, ry, rot, laf, sf = seg[3]
            out.append(f"A {rx:g},{ry:g} {rot:g} {int(laf)},{int(sf)} {_fmt(end)}")
        pen = end
    return " ".join(out)


if __name__ == "__main__":
    # Two unit squares sharing the edge x=1 between (1,0) and (1,1).
    def square(ox, oy):  # closed square as four explicit line segments
        c = [(ox, oy), (ox + 1, oy), (ox + 1, oy + 1), (ox, oy + 1)]
        return [('L', c[i], c[(i + 1) % 4], None) for i in range(4)]

    a = square(0, 0)
    b = square(1, 0)  # its (1,1)->(1,0) edge is A's (1,0)->(1,1), reversed
    before = sum(len(s) for s in (a, b))
    out = dedupe([a, b])
    after = sum(len(s) for s in out)
    assert before - after == 1, (before, after)            # exactly one shared edge removed
    assert len(out[0]) == 4 and len(out[1]) == 3, [len(s) for s in out]
    # rebuilt path for B must start with a moveto (its first edge is intact here)
    assert to_d(out[1]).startswith("M "), to_d(out[1])
    print("ok: removed", before - after, "shared edge; direction-independent match works")
