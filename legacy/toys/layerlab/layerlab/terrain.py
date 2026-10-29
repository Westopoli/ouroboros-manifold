"""Terrain presets and explicit extras (SPEC.md section 6)."""
import math

from . import ffi

_ALL_LAYERS = (1 << ffi.LAYERS) - 1
_SCALARS = {"preset", "w_cells", "h_cells", "cell", "layer_spacing"}
_LISTS = {"cover", "vantage", "zone", "slope"}
PRESET_KEYS = {
    "flat": (),
    "block": ("bw", "bh", "h", "cx", "cy"),
    "wall": ("wt", "end_gap", "h", "cx"),
    "barrier": ("wt", "h", "cx"),
    "lane": ("wt", "ch", "h", "cx"),
    "ramp": ("x1", "sl", "sw", "g", "h", "cy"),
}
_EXTRA_KEYS = {
    "cover": ("x", "y", "r", "height_layer"),
    "vantage": ("x", "y", "r"),
    "zone": ("x", "y", "r", "intensity", "layer"),
    "slope": ("x0", "y0", "dx", "dy", "length", "width", "bottom_layer", "top_layer"),
}
_LIMITS = {"cover": ffi.MAX_COVER, "vantage": ffi.MAX_VANTAGE, "zone": ffi.MAX_ZONES, "slope": ffi.MAX_SLOPES}


def _int(name, v, lo, hi=None):
    if v != int(v):
        raise ValueError("terrain.%s must be a whole number, got %r" % (name, v))
    v = int(v)
    if v < lo or (hi is not None and v > hi):
        raise ValueError("terrain.%s = %d outside %d..%s" % (name, v, lo, "inf" if hi is None else hi))
    return v


def _pos(name, v):
    v = float(v)
    if not v > 0.0:
        raise ValueError("terrain.%s must be > 0, got %r" % (name, v))
    return v


class _Grid:
    """Row-major open/land lists for one build; cell index = row * w + col."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.open = [_ALL_LAYERS] * (w * h)
        self.land = [_ALL_LAYERS] * (w * h)

    def block(self, cols, rows, height):
        mask = _ALL_LAYERS & ~((1 << height) - 1)
        for r in rows:
            for c in cols:
                if 0 <= c < self.w and 0 <= r < self.h:
                    self.open[r * self.w + c] &= mask
                    self.land[r * self.w + c] &= mask


def _strip(p, w):
    wt = _int("wt", p.get("wt", 4), 1)
    cx = _int("cx", p.get("cx", w // 2), 0)
    return range(cx - wt // 2, cx - wt // 2 + wt)


def _height(p):
    return _int("h", p.get("h", 2), 1, ffi.LAYERS)


def _apply_preset(preset, p, grid, cell):
    """Fill `grid` for the preset and return the slope dicts the preset adds."""
    w, h = grid.w, grid.h
    if preset == "flat":
        return []
    if preset == "block":
        bw, bh = _int("bw", p.get("bw", 10), 1), _int("bh", p.get("bh", 10), 1)
        cx, cy = _int("cx", p.get("cx", w // 2), 0), _int("cy", p.get("cy", h // 2), 0)
        grid.block(range(cx - bw // 2, cx - bw // 2 + bw), range(cy - bh // 2, cy - bh // 2 + bh), _height(p))
    elif preset == "wall":
        gap = _int("end_gap", p.get("end_gap", 6), 0)
        grid.block(_strip(p, w), range(gap, h - gap), _height(p))
    elif preset == "barrier":
        grid.block(_strip(p, w), range(h), _height(p))
    elif preset == "lane":
        ch = _int("ch", p.get("ch", 8), 0)
        lo = h // 2 - ch // 2
        grid.block(_strip(p, w), [r for r in range(h) if not lo <= r < lo + ch], _height(p))
    else:  # ramp
        x1 = _int("x1", p.get("x1", 40), 0, w)
        sl, sw = _pos("sl", p.get("sl", 600.0)), _pos("sw", p.get("sw", 200.0))
        g = _int("g", p.get("g", 1), 1, ffi.LAYERS)
        height = _height(p)
        cy = float(p.get("cy", h / 2.0))
        grid.block(range(x1, w), range(h), height)
        ground = 1 << (g - 1)
        plateau = _ALL_LAYERS & ~((1 << height) - 1)
        for r in range(h):
            for c in range(w):
                grid.land[r * w + c] = plateau if c >= x1 else ground
        x0 = x1 * cell - cell / 2.0
        if x0 + sl < x1 * cell:
            raise ValueError("terrain ramp: top edge x %g is short of the plateau at x %g" % (x0 + sl, x1 * cell))
        return [{"x0": x0, "y0": cy * cell, "dx": 1.0, "dy": 0.0, "length": sl, "width": sw,
                 "bottom_layer": g, "top_layer": height + 1}]
    return []


def _extras(terrain_dict, name):
    items = terrain_dict.get(name) or []
    if len(items) > _LIMITS[name]:
        raise ValueError("terrain.%s: %d entries exceed the limit %d" % (name, len(items), _LIMITS[name]))
    out = []
    for i, e in enumerate(items):
        where = "terrain.%s[%d]" % (name, i)
        bad = sorted(set(e) - set(_EXTRA_KEYS[name]))
        miss = [k for k in _EXTRA_KEYS[name] if k not in e]
        if bad or miss:
            raise ValueError("%s: unknown keys %s, missing keys %s" % (where, bad, miss))
        out.append(e)
    return out


def _normalise_slope(where, s):
    dx, dy = float(s["dx"]), float(s["dy"])
    n = math.hypot(dx, dy)
    if n == 0.0:
        raise ValueError("%s: zero direction" % where)
    bottom, top = _int(where + ".bottom_layer", s["bottom_layer"], 1, ffi.LAYERS), \
        _int(where + ".top_layer", s["top_layer"], 1, ffi.LAYERS)
    if bottom >= top:
        raise ValueError("%s: bottom_layer %d must be below top_layer %d" % (where, bottom, top))
    length, width = float(s["length"]), float(s["width"])
    if not (length > 0.0 and width > 0.0):
        raise ValueError("%s: length and width must be > 0" % where)
    return {"x0": float(s["x0"]), "y0": float(s["y0"]), "dx": dx / n, "dy": dy / n,
            "length": length, "width": width, "bottom_layer": bottom, "top_layer": top}


def _overlap(a, b):
    """True if two slope footprints (oriented rectangles) overlap by more than a touch (SAT)."""
    def rect(s):
        cx = s["x0"] + s["dx"] * s["length"] / 2.0
        cy = s["y0"] + s["dy"] * s["length"] / 2.0
        return cx, cy, (s["dx"], s["dy"]), (-s["dy"], s["dx"]), s["length"] / 2.0, s["width"] / 2.0
    ra, rb = rect(a), rect(b)
    for axis in (ra[2], ra[3], rb[2], rb[3]):
        def radius(r):
            return r[4] * abs(r[2][0] * axis[0] + r[2][1] * axis[1]) + r[5] * abs(r[3][0] * axis[0] + r[3][1] * axis[1])
        gap = abs((rb[0] - ra[0]) * axis[0] + (rb[1] - ra[1]) * axis[1])
        if gap >= radius(ra) + radius(rb) - 1e-9:
            return False
    return True


def cell_of(terr_w, terr_h, cell, x, y):
    """(col, row) of a world point, or None outside the arena."""
    c, r = math.floor(x / cell), math.floor(y / cell)
    if 0 <= c < terr_w and 0 <= r < terr_h:
        return c, r
    return None


def build(terrain_dict, out=None):
    if out is None:
        out = ffi.ll_terrain()
    preset = terrain_dict.get("preset", "flat")
    if preset not in PRESET_KEYS:
        raise ValueError("unknown terrain preset %r (known: %s)" % (preset, sorted(PRESET_KEYS)))
    allowed = _SCALARS | _LISTS | set(PRESET_KEYS[preset])
    for key in terrain_dict:
        if key not in allowed:
            raise ValueError("terrain key %r does not belong to preset %r (its keys: %s)"
                             % (key, preset, list(PRESET_KEYS[preset])))
    w, h = int(terrain_dict["w_cells"]), int(terrain_dict["h_cells"])
    if not (1 <= w <= ffi.MAX_GRID_W and 1 <= h <= ffi.MAX_GRID_H):
        raise ValueError("terrain grid %dx%d outside 1..%d x 1..%d" % (w, h, ffi.MAX_GRID_W, ffi.MAX_GRID_H))
    cell = float(terrain_dict["cell"])
    out.w_cells, out.h_cells = w, h
    out.cell = cell
    out.layer_spacing = float(terrain_dict["layer_spacing"])

    grid = _Grid(w, h)
    slopes = _apply_preset(preset, terrain_dict, grid, cell)
    slopes += _extras(terrain_dict, "slope")
    if len(slopes) > ffi.MAX_SLOPES:
        raise ValueError("terrain: %d slopes exceed LL_MAX_SLOPES %d" % (len(slopes), ffi.MAX_SLOPES))
    slopes = [_normalise_slope("terrain.slope[%d]" % i, s) for i, s in enumerate(slopes)]

    for i, a in enumerate(slopes):
        for j in range(i):
            if _overlap(a, slopes[j]):
                raise ValueError("terrain: slope footprints %d and %d overlap" % (j, i))
        for label, x, y, layer in (
                ("bottom", a["x0"], a["y0"], a["bottom_layer"]),
                ("top", a["x0"] + a["dx"] * a["length"], a["y0"] + a["dy"] * a["length"], a["top_layer"])):
            rc = cell_of(w, h, cell, x, y)
            if rc is None or not grid.land[rc[1] * w + rc[0]] & (1 << (layer - 1)):
                raise ValueError("terrain: slope %d %s edge (%g, %g) is not a land cell on layer %d"
                                 % (i, label, x, y, layer))

    n = w * h
    out.open[:n] = grid.open
    out.land[:n] = grid.land
    covers, vantages, zones = (_extras(terrain_dict, k) for k in ("cover", "vantage", "zone"))
    for i, c in enumerate(covers):
        _pos("cover[%d].r" % i, c["r"])
        _int("cover[%d].height_layer" % i, c["height_layer"], 1, ffi.LAYERS)
        out.cover[i] = ffi.ll_cover(float(c["x"]), float(c["y"]), float(c["r"]), int(c["height_layer"]))
    for i, v in enumerate(vantages):
        _pos("vantage[%d].r" % i, v["r"])
        out.vantage[i] = ffi.ll_vantage(float(v["x"]), float(v["y"]), float(v["r"]))
    for i, z in enumerate(zones):
        _pos("zone[%d].r" % i, z["r"])
        _int("zone[%d].layer" % i, z["layer"], 1, ffi.LAYERS)
        out.zone[i] = ffi.ll_zone(float(z["x"]), float(z["y"]), float(z["r"]), float(z["intensity"]), int(z["layer"]))
    for i, s in enumerate(slopes):
        out.slope[i] = ffi.ll_slope(s["x0"], s["y0"], s["dx"], s["dy"], s["length"], s["width"],
                                    s["bottom_layer"], s["top_layer"])
    out.n_cover, out.n_vantage, out.n_zone, out.n_slope = len(covers), len(vantages), len(zones), len(slopes)
    return out
