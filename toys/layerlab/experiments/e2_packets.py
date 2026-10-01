"""E2, defeat in detail (README 6.2): a concentrated side A of n units against side B of n units arriving
in k equal packets `gap` world units apart. Theory (square law, each packet fully destroyed before the
next arrives): A keeps n * sqrt(1 - 1/k). BOTH sides attack-move at each other (a symmetric approach: the
earlier version had A stand still, which gave the standing side a 70 percent edge in the 20 v 20 baseline).
Spawn positions are computed from the arena width so every packet lies inside it, and a layout that does
not fit raises ValueError. The k = 1 run is the baseline (two equal forces meeting: nobody should keep
n * sqrt(0) = 0 in theory; the lab keeps a few); `gain` below is the survivors minus that baseline.
Both sides shoot the nearest enemy (Westley, 2026-10-01); hard bodies and the sidestep are on."""
import math
from layerlab import scenario
from layerlab.scenario import set_path
from layerlab.run import run

def build(k, gap, n=20, base="scenarios/x0_mirror.toml", a_x=400.0, y=1000.0, last_x=3800.0, layer=3):
    arena = None
    scn = scenario.load(base)
    arena = scn["terrain"]["w_cells"] * scn["terrain"]["cell"]
    first_x = last_x - (k - 1) * gap          # the LAST packet sits at last_x, the first closest to A
    if first_x <= a_x + 400.0 or last_x >= arena - 50.0:
        raise ValueError(f"k={k}, gap={gap} does not fit the {arena:.0f}-wide arena (first packet at {first_x:.0f})")
    scn["groups"] = [dict(side="A", type="raider", count=n, formation="line", x=a_x, y=y, facing=0.0,
                          layer=layer, order="attack_move", goal=[last_x, y])]
    per = n // k
    for j in range(k):
        scn["groups"].append(dict(side="B", type="raider", count=per, formation="line", x=first_x + j * gap, y=y,
                                  facing=180.0, layer=layer, order="attack_move", goal=[a_x, y]))
    return scn

def survivors(scn, seeds=range(20)):
    a = []; w = 0
    for s in seeds:
        r = run(scn, seed=s); a.append(r.survivors[0]); w += r.winner == 1
    return sum(a) / len(a), w / len(a)

if __name__ == "__main__":
    n = 20
    print("E2, both sides advancing, 20 seeds. A survivors (A win rate); 'gain' = survivors minus the k = 1 baseline")
    print("theory: A keeps 20*sqrt(1-1/k): k=2 -> 14.1, k=4 -> 17.3, k=1 -> 0")
    print("gap    k=1 (baseline)    k=2: survivors / gain / theory     k=4: survivors / gain / theory")
    for gap in (100, 200, 400, 600, 900):
        base_s, base_w = survivors(build(1, gap, n))
        row = f"{gap:4d}   {base_s:4.1f} ({base_w:.2f})     "
        for k in (2, 4):
            try:
                s, w = survivors(build(k, gap, n))
                row += f"  {s:5.1f} ({w:.2f}) / {s-base_s:+5.1f} / {n*math.sqrt(1-1/k):4.1f}   "
            except ValueError as e:
                row += "  (does not fit the arena)            "
        print(row)
