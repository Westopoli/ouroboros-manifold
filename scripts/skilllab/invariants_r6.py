"""Engine rules Round 6, L4 (docs/northstar/plans/engine-rules-2026-11-08/round6.md): the predicate the lab checker (`invariants.py`) gained for two units that stay overlapped on one layer.

  SameLayerOverlap  R-097-05  two living units on one layer closer than OVERLAP_GAP wu for more than OVERLAP_SETTLE_TICKS consecutive frames

A small state machine fed one frame at a time by `invariants._Checker.feed`, like `invariants_r5.SlopeCollision`; the frame and row shapes are those of `invariants.py` (this module imports nothing from
it). Tests: tests/skilllab/arena/test_invariants_r6_same_layer_overlap.py. Every number below is a DRAFT constant, Westley's to change: DRAFT-ramp-slack 2 wu, DRAFT-ramp-settle-ticks 3.
# See also: scripts/skilllab/invariants_r5.py (SlopeCollision: the same rule for a pair on one slope, any layers)
"""
import math

OVERLAP_GAP = 28.0           # R-097-05: 2 x unit radius 15 wu is 30 wu; 2 wu less is DRAFT-ramp-slack (the sweep's I13, and SlopeCollision's limit)
OVERLAP_SETTLE_TICKS = 3     # DRAFT-ramp-settle-ticks: a pair is reported in the frame in which it has stayed overlapped for more than this many consecutive frames (the fourth)


class SameLayerOverlap:
    """R-097-05, same layer. Two living units on one layer closer than OVERLAP_GAP wu (the plane), either side, any ground, are a violation of the lower id in the frame the pair has stayed that close for more
    than OVERLAP_SETTLE_TICKS consecutive frames, once while it stays close; the count restarts when the pair is apart for a frame or either unit is dead.
    `slope_at(x, y)` (as `Rules.slope_at`, optional): a pair that both stand on one slope is `SlopeCollision`'s (reported once, not twice), so it is left to it."""

    def __init__(self, slope_at=None):
        self.slope_at = slope_at
        self.close = {}              # pair -> consecutive frames it has been overlapped (reported in the frame the count passes OVERLAP_SETTLE_TICKS)

    def feed(self, frame, prev, tick, out):
        cells = {}
        for u, r in frame["units"].items():
            if r["alive"]:
                cells.setdefault((r["layer"], int(r["x"] // OVERLAP_GAP), int(r["y"] // OVERLAP_GAP)), []).append(u)
        now = {}
        for (layer, cx, cy), ids in sorted(cells.items()):
            for dx, dy in ((0, 0), (1, -1), (1, 0), (1, 1), (0, 1)):          # each pair of neighbouring cells once
                others = cells.get((layer, cx + dx, cy + dy), ())
                for a in ids:
                    ra = frame["units"][a]
                    for b in others:
                        if (dx, dy) == (0, 0) and b <= a:
                            continue
                        rb = frame["units"][b]
                        d = math.hypot(ra["x"] - rb["x"], ra["y"] - rb["y"])
                        if d >= OVERLAP_GAP or self._on_one_slope(ra, rb):
                            continue
                        pair = (min(a, b), max(a, b))
                        now[pair] = self.close.get(pair, 0) + 1
                        if now[pair] == OVERLAP_SETTLE_TICKS + 1:
                            out.append({"rule": "R-097-05", "tick": tick, "unit": pair[0], "detail": "%d and %d stand %.1f wu apart on layer %d, under %.0f wu after the collision pass" % (
                                pair[0], pair[1], d, layer, OVERLAP_GAP)})
        self.close = now

    def _on_one_slope(self, ra, rb):
        if self.slope_at is None:
            return False
        sa = self.slope_at(ra["x"], ra["y"])
        return sa is not None and sa == self.slope_at(rb["x"], rb["y"])
