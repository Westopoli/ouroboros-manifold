"""Terrain presets (SPEC.md section 6). R0: preset 'flat' only."""
from . import ffi

_ALL_LAYERS = (1 << ffi.LAYERS) - 1
_SCALARS = {"preset", "w_cells", "h_cells", "cell", "layer_spacing"}
_LISTS = {"cover", "vantage", "zone", "slope"}
_PRESETS_R1 = {"block", "wall", "barrier", "lane", "ramp"}


def build(terrain_dict, out=None):
    if out is None:
        out = ffi.ll_terrain()
    preset = terrain_dict.get("preset", "flat")
    if preset in _PRESETS_R1:
        raise NotImplementedError("terrain preset %r is added in rung R1" % preset)
    if preset != "flat":
        raise NotImplementedError("unknown terrain preset %r (only 'flat' exists; others arrive in rung R1)" % (preset,))
    for key in terrain_dict:
        if key in _LISTS:
            if terrain_dict[key]:
                raise NotImplementedError("terrain.%s is added in rung R1" % key)
        elif key not in _SCALARS:
            raise NotImplementedError("terrain key %r (a preset parameter) is added in rung R1" % key)
    w, h = int(terrain_dict["w_cells"]), int(terrain_dict["h_cells"])
    if not (1 <= w <= ffi.MAX_GRID_W and 1 <= h <= ffi.MAX_GRID_H):
        raise ValueError("terrain grid %dx%d outside 1..%d x 1..%d" % (w, h, ffi.MAX_GRID_W, ffi.MAX_GRID_H))
    out.w_cells, out.h_cells = w, h
    out.cell = float(terrain_dict["cell"])
    out.layer_spacing = float(terrain_dict["layer_spacing"])
    n = w * h
    out.open[:n] = [_ALL_LAYERS] * n
    out.land[:n] = [_ALL_LAYERS] * n
    out.n_cover = out.n_vantage = out.n_zone = out.n_slope = 0
    return out
