"""TimelineFakeEngine plus the three Engine methods terrain adds (no compiler, no library).

New Engine methods these tests fix (scripts/skilllab/engine.py supplies them later):
  set_canvas(w, width, height)                          -> None   om_map_set_canvas; ValueError when refused
  block_rect(w, x0, y0, x1, y1, layer_lo, layer_hi)     -> None   om_map_block_rect; ValueError when refused
  add_cover(w, x, y, radius, height)                    -> int    om_map_add_cover, 1-based; ValueError when 0

Each call is logged as ("set_canvas", w, ...) etc.; `terrain_calls()` is just those, in order.
"""
from fakes_timeline import TimelineFakeEngine

TERRAIN = ("set_canvas", "block_rect", "add_cover")


class TerrainFakeEngine(TimelineFakeEngine):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.covers = 0

    def terrain_calls(self):
        return [c for c in self.calls if c[0] in TERRAIN]

    def set_canvas(self, w, width, height):
        self.calls.append(("set_canvas", w, width, height))

    def block_rect(self, w, x0, y0, x1, y1, layer_lo, layer_hi):
        self.calls.append(("block_rect", w, x0, y0, x1, y1, layer_lo, layer_hi))

    def add_cover(self, w, x, y, radius, height):
        self.calls.append(("add_cover", w, x, y, radius, height))
        self.covers += 1
        return self.covers
