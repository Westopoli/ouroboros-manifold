"""Formation placement (SPEC.md section 7): line, column, box, concave, screen."""
import math

_PARAMS = {
    "line": (), "column": (), "box": ("cols",),
    "concave": ("center", "R", "arc_deg"), "screen": ("screen_r", "arc_deg"),
}


def _r(v):
    return round(v, 6)


def _wrap_deg(a):
    return (a + 180.0) % 360.0 - 180.0


def _arc_angles(n, axis_deg, arc_deg):
    """n angles (deg) evenly spaced over arc_deg centred on axis_deg; n = 1 sits on the axis."""
    if n == 1:
        return [axis_deg]
    return [axis_deg - arc_deg / 2.0 + k * arc_deg / (n - 1) for k in range(n)]


def place(kind, n, x, y, facing_deg, spacing, **params):
    if kind not in _PARAMS:
        raise ValueError("unknown formation %r" % (kind,))
    missing = [k for k in _PARAMS[kind] if k not in params]
    extra = sorted(k for k in params if k not in _PARAMS[kind])
    if missing or extra:
        raise ValueError("formation %r: missing %s, unexpected %s" % (kind, missing, extra))
    f = math.radians(facing_deg)
    ax, ay = math.cos(f), math.sin(f)     # along the facing
    px, py = -ay, ax                      # perpendicular (facing rotated +90 degrees)
    out = []
    if kind == "line":
        for i in range(n):
            off = (i - (n - 1) / 2.0) * spacing
            out.append((_r(x + off * px), _r(y + off * py), facing_deg))
    elif kind == "column":
        for i in range(n):
            off = (i - (n - 1) / 2.0) * spacing
            out.append((_r(x + off * ax), _r(y + off * ay), facing_deg))
    elif kind == "box":
        cols = int(params["cols"])
        if cols < 1:
            raise ValueError("box cols must be >= 1")
        rows = -(-n // cols)
        for i in range(n):
            m = min(cols, n - i // cols * cols)          # a short last row is centred
            lat = (i % cols - (m - 1) / 2.0) * spacing
            dep = (i // cols - (rows - 1) / 2.0) * spacing
            out.append((_r(x + dep * ax + lat * px), _r(y + dep * ay + lat * py), facing_deg))
    elif kind == "concave":
        cx, cy = params["center"]
        radius, arc = params["R"], params["arc_deg"]
        axis = math.degrees(math.atan2(y - cy, x - cx))
        for a in _arc_angles(n, axis, arc):
            r = math.radians(a)
            out.append((_r(cx + radius * math.cos(r)), _r(cy + radius * math.sin(r)), _wrap_deg(a + 180.0)))
    else:  # screen
        radius, arc = params["screen_r"], params["arc_deg"]
        for a in _arc_angles(n, facing_deg, arc):
            r = math.radians(a)
            out.append((_r(x + radius * math.cos(r)), _r(y + radius * math.sin(r)), _wrap_deg(a)))
    return out
