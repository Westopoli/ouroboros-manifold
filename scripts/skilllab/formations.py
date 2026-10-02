"""Formation placement; geometry ported from toys/layerlab/layerlab/formations.py."""
import math

_REQUIRED = {
    "line": ("spacing",),
    "column": ("spacing", "cols"),
    "concave": ("arc_deg", "radius"),
    "blob": ("radius",),
    "points": ("points",),
}
_GOLDEN_ANGLE = 2.399963229728653


def _r(v):
    return float(round(v, 6))


def _arc_angles(n, axis_deg, arc_deg):
    """n angles (deg) evenly spaced over arc_deg centred on axis_deg; n = 1 sits on the axis."""
    if n == 1:
        return [axis_deg]
    return [axis_deg - arc_deg / 2.0 + k * arc_deg / (n - 1) for k in range(n)]


def _blob(n, x, y, radius):
    # Pairs (p, reflection of p) from a Fermat spiral, plus the anchor itself when n is odd.
    pairs = n // 2
    out = [(float(x), float(y))] if n % 2 else []
    for i in range(pairs):
        d = radius * math.sqrt((i + 0.5) / pairs)
        a = i * _GOLDEN_ANGLE
        dx, dy = round(d * math.cos(a), 6), round(d * math.sin(a), 6)
        out.append((float(x + dx), float(y + dy)))
        out.append((float(x - dx), float(y - dy)))
    return out


def place(kind, n, x, y, facing_deg, params):
    if kind not in _REQUIRED:
        raise ValueError("unknown formation %r" % (kind,))
    if n < 0:
        raise ValueError("n must be >= 0")
    missing = [k for k in _REQUIRED[kind] if k not in params]
    if missing:
        raise ValueError("formation %r: missing %s" % (kind, missing))
    if kind == "points":
        pts = [(float(px), float(py)) for px, py in params["points"]]
        if len(pts) != n:
            raise ValueError("points has %d entries, expected %d" % (len(pts), n))
        return pts
    if n == 0:
        return []
    f = math.radians(facing_deg)
    ax, ay = math.cos(f), math.sin(f)     # along the facing
    px, py = -ay, ax                      # perpendicular (facing rotated +90 degrees)
    out = []
    if kind == "line":
        spacing = params["spacing"]
        for i in range(n):
            off = (i - (n - 1) / 2.0) * spacing
            out.append((_r(x + off * px), _r(y + off * py)))
    elif kind == "column":
        spacing, cols = params["spacing"], int(params["cols"])
        if cols < 1:
            raise ValueError("column cols must be >= 1")
        rows = -(-n // cols)
        for i in range(n):
            m = min(cols, n - i // cols * cols)          # a short last row is centred
            lat = (i % cols - (m - 1) / 2.0) * spacing
            dep = (i // cols - (rows - 1) / 2.0) * spacing
            out.append((_r(x + dep * ax + lat * px), _r(y + dep * ay + lat * py)))
    elif kind == "concave":
        radius, arc = params["radius"], params["arc_deg"]
        cx, cy = x + radius * ax, y + radius * ay
        axis = math.degrees(math.atan2(y - cy, x - cx))
        for a in _arc_angles(n, axis, arc):
            r = math.radians(a)
            out.append((_r(cx + radius * math.cos(r)), _r(cy + radius * math.sin(r))))
    else:
        out = _blob(n, x, y, params["radius"])
    return out
