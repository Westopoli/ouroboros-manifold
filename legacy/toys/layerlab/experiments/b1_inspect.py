"""Design chat (b1): look at what a scripted play actually does before measuring it.
Usage: python3 experiments/b1_inspect.py <type> <skills e.g. S2 or -> <size> <enemy heads>"""
import sys, dataclasses, math
sys.path.insert(0, ".")
import numpy as np
from layerlab.skill import plays
from layerlab.skill.situation import sample_situations
from layerlab.run import run

def flat_sit(unit):
    sit = [s for s in sample_situations(14, 1) if s.family == "flat"][0]
    return dataclasses.replace(sit, mix={unit: 1.0})

if __name__ == "__main__":
    unit, sk, size, enemy = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    skills = frozenset() if sk == "-" else frozenset(sk.split("+"))
    sit = flat_sit(unit)
    build = plays.build_scenario(sit, skills, size)
    scn = build(enemy / size, False)
    print("anchors", sit.anchor_A, sit.anchor_B, "approach", round(sit.approach_distance), "arc", getattr(build, "arc", None))
    for g in scn["groups"]:
        print({k: g[k] for k in ("side", "type", "count", "formation", "x", "y", "order", "goal") if k in g}, {k: g[k] for k in g if k in ("R", "arc_deg", "center", "spacing", "cols")})
    res = run(scn, seed=0, trace=True)
    tr = res.trace; side = tr["side"][0]
    fire = (tr["flags"] & 16) != 0; alive = tr["alive"] != 0
    def spread(t, s):
        m = (side == s) & alive[t]
        x, y = tr["x"][t][m], tr["y"][t][m]
        return (round(float(x.min())), round(float(x.max())), round(float(y.min())), round(float(y.max()))) if m.any() else None
    first = int(np.argmax(fire.any(axis=1))) if fire.any() else -1
    print("ticks", res.ticks, "winner", res.winner, "survivors", res.survivors, "first firing tick", first)
    for t in sorted(set([0, max(first, 0), min(first + 40, len(tr) - 1), min(first + 120, len(tr) - 1), len(tr) - 1])):
        print(f"t={t:5d} A box {spread(t,0)} firing {int(fire[t][side==0].sum())}/{int(alive[t][side==0].sum())} | B box {spread(t,1)} firing {int(fire[t][side==1].sum())}/{int(alive[t][side==1].sum())}")
