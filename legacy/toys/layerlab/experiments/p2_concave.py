"""P2, the concave beats the surround's line; P4, a smaller force wins by position (README section 4,
Westley 2026-09-30: "when units have a surround, the units in the concave with the surround win";
"organizing your units in specific patterns can lead to better engagements").
Both sides attack-move at each other (a symmetric approach: holding against advancing gave the holder or
the advancer an edge in earlier passes, so neither side holds). Same layer, flat ground, identical raiders,
nearest-target on both sides (Westley, 2026-10-01), hard bodies and the sidestep on.
A starts as a concave arc of `arc` degrees at radius `R` around B's centre, on A's side; `arc` = 0 means a
plain line (the control: two lines advancing, A wins about half). B is a line of n_b units facing A.
"""
import math
from layerlab import scenario
from layerlab.scenario import set_path
from layerlab.run import run

def build(n_a=10, n_b=10, arc=0.0, R=700.0, b_x=3000.0, y=1000.0, a_layer=3, b_layer=3, base="scenarios/x0_mirror.toml"):
    scn = scenario.load(base)
    a_x = b_x - R
    if arc <= 0.0:
        ga = dict(side="A", type="raider", count=n_a, formation="line", x=a_x, y=y, facing=0.0, layer=a_layer,
                  order="attack_move", goal=[b_x, y])
    else:
        ga = dict(side="A", type="raider", count=n_a, formation="concave", center=[b_x, y], R=R, arc_deg=float(arc),
                  x=a_x, y=y, facing=0.0, layer=a_layer, order="attack_move", goal=[b_x, y])
    gb = dict(side="B", type="raider", count=n_b, formation="line", x=b_x, y=y, facing=180.0, layer=b_layer,
              order="attack_move", goal=[a_x, y])
    scn["groups"] = [ga, gb]
    return scn

def rate(scn, seeds=range(40)):
    w = 0; sa = []
    for s in seeds:
        r = run(scn, seed=s); w += r.winner == 1; sa.append(r.survivors[0])
    return w / len(seeds), sum(sa) / len(sa)

if __name__ == "__main__":
    print("P2: A in a concave of `arc` degrees (0 = line) v B in a line, 10 v 10, both advancing, 40 seeds: A win rate (A survivors)")
    for R in (500.0, 700.0):
        print(f"  radius {R:.0f}: " + "  ".join(f"arc {a:>3d}: {rate(build(arc=a, R=R))[0]:.2f}" for a in (0, 40, 80, 120, 160, 200)))
    print("\nP4: how many units is the concave worth? A win rate; rows = A's count (B = 10), columns = A's arc (R = 700), 40 seeds")
    arcs = (0, 80, 160, 200)
    print("n_A\\arc  " + "".join(f"{a:>9d}" for a in arcs))
    for n_a in (6, 7, 8, 9, 10, 11):
        print(f"{n_a:>6d}   " + "".join(f"{rate(build(n_a=n_a, arc=a))[0]:9.2f}" for a in arcs))
