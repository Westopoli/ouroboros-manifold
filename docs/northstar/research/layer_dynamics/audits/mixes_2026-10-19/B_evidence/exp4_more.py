"""E4: Strike-Siege flank (S5), Strike-pair fire-up-from-below (S3 counter), Siege pair, and the all-six mix: skilled v naive scans."""
import sys, json, time, dataclasses
sys.path.insert(0, "/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/b1e8769e-404e-4263-be23-8535a58b0e59/scratchpad/mix_B")
from mixlib import *
RB = (("Raider", 8), ("Bombard", 8)); RI = (("Raider", 8), ("Interceptor", 8)); BB = (("Bombard", 8), ("Bastion", 8))
def flank(mix):
    # Raiders start 500 wu off the axis and attack-move onto the enemy's far side; Bombards blob on the axis
    return [Group(side=0, unit="Raider", count=8, formation="blob", x=-GAP / 2, y=500.0, facing_deg=0.0, layer=0, order="attack_move",
                  goal=(GAP / 2 + 150.0, 0.0), params={"radius": 80 + 12 * math.sqrt(8)}), blob(0, "Bombard", 8, -GAP / 2)]
def from_below(mix):
    # enemy stands two layers up (layer 2); our Interceptors sit on layer 0 (fire up 2, nobody replies), Raiders meet them on layer 2
    return [blob(0, "Interceptor", 8, -GAP / 2, layer=0), blob(0, "Raider", 8, -GAP / 2, layer=2)]
def naive_on2(mix):
    return [blob(0, u, c, -GAP / 2, layer=2) for u, c in mix]
def siege_screen(mix):
    return [line(0, "Bastion", 8, -GAP / 2 + 60), line(0, "Bombard", 8, -GAP / 2 - 60)]
UP2 = {"OM_TP_RANGE_UP_2": 0.25, "OM_TP_DAMAGE_UP_2": 0.25}
PLAYS = {
 "RB flank (Raiders round to the Bombards)": build_custom(RB, flank),
 "RI naive, all on layer 2": build_custom(RI, naive_on2, enemy_layer=2),
 "RI from below up2=1.0": build_custom(RI, from_below, enemy_layer=2),
 "RI from below up2=0.25": build_custom(RI, from_below, settings=UP2, enemy_layer=2),
 "BB naive": build_naive(BB),
 "BB screen (Bastions front)": build_custom(BB, siege_screen),
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
                  "wall", out[name]["wall_s"], {h: v[:3] + (v[3],) for h, v in cells.items()}, flush=True)
    json.dump(out, open(sys.argv[2], "w"), indent=1)
