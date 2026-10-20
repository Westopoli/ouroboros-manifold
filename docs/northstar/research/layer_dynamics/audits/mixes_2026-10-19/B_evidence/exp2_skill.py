"""E2: skilled arrangement v naive blob, same mix both sides, break-even scan 8..48 (lab bisection, 2 replicates x swap)."""
import sys, json, time
sys.path.insert(0, "/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/b1e8769e-404e-4263-be23-8535a58b0e59/scratchpad/mix_B")
from mixlib import *
RB = (("Raider", 8), ("Bombard", 8)); IB = (("Interceptor", 8), ("Bombard", 8)); VB = (("Vanguard", 8), ("Bombard", 8))
UP2_025 = {"OM_TP_RANGE_UP_2": 0.25, "OM_TP_DAMAGE_UP_2": 0.25}
def screen(front, back):
    return lambda mix: [line(0, front, 8, -GAP / 2 + 60), line(0, back, 8, -GAP / 2 - 60)]
def stack(low, high, layer=2):
    return lambda mix: [blob(0, low, 8, -GAP / 2), blob(0, high, 8, -GAP / 2, layer=layer)]
PLAYS = {
 "RB naive": build_naive(RB),
 "RB screen (Raiders front, Bombards behind)": build_custom(RB, screen("Raider", "Bombard")),
 "IB naive": build_naive(IB),
 "IB stack (Bombards +2) up2=1.0": build_custom(IB, stack("Interceptor", "Bombard")),
 "IB stack (Bombards +2) up2=0.25": build_custom(IB, stack("Interceptor", "Bombard"), settings=UP2_025),
 "VB naive": build_naive(VB),
 "VB stack (Bombards +2)": build_custom(VB, stack("Vanguard", "Bombard")),
 "VB screen (M3 s2_screen shape)": build_custom(VB, screen("Vanguard", "Bombard")),
}
if __name__ == "__main__":
    which = sys.argv[3:] or list(PLAYS)
    out = {}
    with pool.FightPool(int(sys.argv[1]), lean=True) as p:
        for name in which:
            t = time.time()
            r = scan_mod.scan(PLAYS[name], 16, 8, 48, replicates=2, map_fn=p.map)
            cells = {c.enemy_heads: (sum(f.outcome == "side0" for f in c.fights), len(c.fights),
                                     sorted(set(f.outcome for f in c.fights)), round(sum(f.ticks for f in c.fights) / len(c.fights))) for c in r.cells}
            out[name] = {"beats": r.beats, "loses_to": r.loses_to, "ceiling": r.ceiling_hit, "multi_flip": r.multi_flip,
                         "fights": sum(len(c.fights) for c in r.cells), "wall_s": round(time.time() - t, 1), "cells": cells}
            print(name.ljust(42), "beats", r.beats, "loses_to", r.loses_to, "ceiling", r.ceiling_hit, "fights", out[name]["fights"],
                  "wall", out[name]["wall_s"], {h: v[:3] for h, v in cells.items()}, flush=True)
    json.dump(out, open(sys.argv[2], "w"), indent=1)
