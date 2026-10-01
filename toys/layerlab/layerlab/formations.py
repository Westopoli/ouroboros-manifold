"""Formation placement (SPEC.md section 7). R0: line only."""
import math


def place(kind, n, x, y, facing_deg, spacing, **params):
    if kind != "line":
        raise NotImplementedError("formation %r is added in rung R2" % (kind,))
    if params:
        raise ValueError("formation 'line' takes no parameters beyond spacing: %s" % sorted(params))
    f = math.radians(facing_deg)
    px, py = -math.sin(f), math.cos(f)
    out = []
    for i in range(n):
        off = (i - (n - 1) / 2.0) * spacing
        out.append((round(x + off * px, 6), round(y + off * py, 6), facing_deg))
    return out
