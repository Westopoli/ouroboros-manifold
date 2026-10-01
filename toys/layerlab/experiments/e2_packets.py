"""E2, defeat in detail (README 6.2): a concentrated side A of n units against side B of n units
arriving in k equal packets spaced `gap` world units apart. Theory (square law, packets fully
destroyed one after another): A keeps n * sqrt(1 - 1/k). Both sides use the nearest-target rule
(Westley, 2026-10-01). A stands and engages what it sees; B's packets attack-move at it."""
from layerlab import scenario
from layerlab.scenario import set_path
from layerlab.run import run

def build(k, gap, n=20, base="scenarios/x0_mirror.toml", a_x=500.0, first_x=1700.0, y=1000.0, layer_a=3, layer_b=3):
    scn = scenario.load(base)
    scn["groups"] = []
    scn["groups"].append(dict(side="A", type="raider", count=n, formation="line", x=a_x, y=y, facing=0.0,
                              layer=layer_a, order="hold", goal=[a_x, y]))
    per = n // k
    for j in range(k):
        scn["groups"].append(dict(side="B", type="raider", count=per, formation="line", x=first_x + j * gap, y=y,
                                  facing=180.0, layer=layer_b, order="attack_move", goal=[a_x, y]))
    scn = set_path(scn, "rules.chase_when_idle", 1)
    return scn

def survivors(scn, seeds=range(20)):
    a = []; w = 0
    for s in seeds:
        r = run(scn, seed=s); a.append(r.survivors[0]); w += r.winner == 1
    return sum(a) / len(a), w / len(a)

if __name__ == "__main__":
    import math
    n = 20
    print("E2: A (20, concentrated, standing) against B (20) in k packets; mean A survivors over 20 seeds and A win rate")
    print("  theory: A keeps 20*sqrt(1-1/k)")
    for gap in (400, 700, 1000):
        row = []
        for k in (1, 2, 4):
            s, w = survivors(build(k, gap, n))
            row.append(f"k={k}: {s:5.1f} (win {w:.2f}, theory {n*math.sqrt(1-1/k):4.1f})")
        print(f"  gap {gap:4d}: " + " | ".join(row))
