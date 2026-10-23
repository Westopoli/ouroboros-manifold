"""Design chat (b1): hold a choke properly. Defenders stand in arcs around the corridor's exit, every one within
reach of the mouth, and hold; the attackers walk through. Compared with the lab's scripted S1 (a 4-deep block at the
mouth) and with both sides walking in. Usage: python3 experiments/b1_choke.py [size=16] [seeds=10]"""
import sys, copy, dataclasses, math
sys.path.insert(0, ".")
import numpy as np
from layerlab import scenario
from layerlab.run import run
from layerlab.skill import plays, situation
from layerlab.skill.fight import run_fights
from layerlab.skill.situation import sample_situations

def lane_sit(unit="raider"):
    sit = [s for s in sample_situations(14, 1) if s.family == "lane"][0]
    return dataclasses.replace(sit, mix={unit: 1.0})

def exit_point(sit):
    t = sit.terrain; cell = 50.0
    return ((t["cx"] - t["wt"] / 2.0) * cell, 1000.0)          # our (west) end of the corridor, at mid height

def wall_cover(sit):
    """The lane preset blocks movement but not sight, so units shoot through the rock. Cover discs along both wall
    halves make the walls block sight (and so fire) on the layers they block."""
    t = sit.terrain; cell = 50.0; xc = t["cx"] * cell; half = t["ch"] * cell / 2.0; h = t["h"]; r = t["wt"] * cell / 2.0
    discs = []
    for sign in (-1, 1):
        y = 1000.0 + sign * (half + r)
        while 0 <= y <= 2000:
            discs.append({"x": xc, "y": y, "r": r, "height_layer": h}); y += sign * r
        for dx in (-r + 40, r - 40):
            discs.append({"x": xc + dx, "y": 1000.0 + sign * (half + 40), "r": 40.0, "height_layer": h})
    return discs

def with_walls(build, sit):
    def b(n, swap):
        scn = build(n, swap); scn["terrain"] = dict(scn["terrain"], cover=wall_cover(sit)); scenario.to_c(scn); return scn
    return b

def arc_build(sit, size, rings=((190.0, 12), (140.0, 4)), arc=170.0, unit="raider"):
    base = situation.base_scenario(sit); ex = exit_point(sit)
    def build(n_enemy, swap):
        scn = copy.deepcopy(base); groups = []; left = size
        for R, cap in rings:
            k = min(cap, left); left -= k
            if k:
                groups.append({"side": "A", "type": unit, "count": k, "formation": "concave", "x": ex[0] - R, "y": ex[1],
                               "center": [ex[0], ex[1]], "R": R, "arc_deg": arc, "facing": 0.0, "layer": sit.layer,
                               "order": "hold", "target_policy": "nearest", "spacing": 50.0})
        assert left == 0, "rings too small for %d" % size
        theirs = plays._compose(sit, base, 1, {unit: n_enemy}, frozenset(), "line", (sit.mix, {unit: size}), True, layer=sit.layer)
        if swap:
            groups = [dict(g, side="B") for g in groups]; theirs = [dict(g, side="A") for g in theirs]
        g = groups + theirs
        scn["groups"] = [x for x in g if x["side"] == "A"] + [x for x in g if x["side"] == "B"]
        scenario.to_c(scn)
        return scn
    return build

def lab_build(sit, size, skills):
    b = plays.build_scenario(sit, skills, size)
    return lambda n, swap: b(n / size, swap)

def cell(build, n, seeds):
    jobs, slots = [], []
    for swap in (False, True):
        scn = build(n, swap)
        for s in range(seeds):
            jobs.append((scn, s)); slots.append(swap)
    out = []
    for swap, fr in zip(slots, run_fights(jobs, processes=8)):
        sk = int(swap); dur = max(fr.ticks - max(fr.first_contact_tick, 0), 1)
        out.append((-fr.margin if swap else fr.margin, fr.firing_ticks[sk] / dur, fr.firing_ticks[1 - sk] / dur, fr.outcome, fr.survivors[sk]))
    return out

def table(title, build, size, heads, seeds):
    print(f"\n{title}\n  enemy |   won   | margin | avg firing after contact: ours | theirs | ours left | stalemates")
    beat = None
    for n in heads:
        try:
            r = cell(build, n, seeds)
        except ValueError as e:
            print(f"  {n:>5} | cannot build: {str(e)[:70]}"); continue
        k = len(r); won = sum(1 for x in r if x[0] > 0.05)
        print(f"  {n:>5} | {won:>3}/{k:<3} | {sum(x[0] for x in r)/k:>+6.2f} | {sum(x[1] for x in r)/k:>30.1f} | {sum(x[2] for x in r)/k:>6.1f} | {sum(x[4] for x in r)/k:>9.1f} | {sum(1 for x in r if x[3]=='stalemate')}")
        if won * 2 > k: beat = n
    print(f"  => {size} units beat up to {beat}")

if __name__ == "__main__":
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    sit = lane_sit(); print("lane:", sit.terrain, "exit", exit_point(sit))
    scn = arc_build(sit, size)(24, False); res = run(scn, seed=0, trace=True); tr = res.trace; side = tr["side"][0]
    fire = (tr["flags"] & 16) != 0; alive = tr["alive"] != 0; first = int(np.argmax(fire.any(axis=1)))
    print("arc play, one fight v 24: winner", res.winner, "survivors", res.survivors, "| ours x", round(float(tr["x"][0][side == 0].min())), "to", round(float(tr["x"][0][side == 0].max())))
    for t in (first + 40, first + 120, first + 300):
        if t < len(tr): print(f"  t={t}: ours firing {int(fire[t][side==0].sum())}/{int(alive[t][side==0].sum())}  theirs {int(fire[t][side==1].sum())}/{int(alive[t][side==1].sum())}")
    heads = [16, 20, 24, 28, 32, 40, 48, 64]
    table("Both walk in (naive v naive)", lab_build(sit, size, frozenset()), size, heads, seeds)
    table("Lab's scripted S1 (block at the mouth)", lab_build(sit, size, frozenset({"S1"})), size, heads, seeds)
    table("Arcs around the exit, holding", arc_build(sit, size), size, heads, seeds)
