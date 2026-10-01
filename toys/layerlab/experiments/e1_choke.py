"""E1, choke breadth (README 6.2). 20 walking attackers against 10 walking defenders inside a corridor (the
`lane` preset, 1000 units long, `ch` cells wide), BOTH sides attack-moving at each other with the SAME
formation (a box as wide as the corridor allows), so the only difference between the two sides is their
number. The choke limits how many units can be within reach of one another: it binds when the weapon
range is short compared with the corridor length (range << 1000) and the corridor is narrow. Theory for
the larger side: survivors slide from the square law sqrt(20^2 - 10^2) = 17.3 (everyone can fire) toward
the linear law 20 - 10 = 10 (one at a time). Both sides shoot the nearest enemy (Westley, 2026-10-01).
Hard bodies and the sidestep are on."""
import copy, math
from layerlab import scenario
from layerlab.scenario import set_path
from layerlab.run import run
from layerlab.analysis import exchange

def build(ch, n_att=20, n_def=10, rng=60.0, wt=20, base="scenarios/x0_mirror.toml"):
    scn = scenario.load(base)
    t = copy.deepcopy(scn["types"]["raider"]); t["movement_kind"] = "walk"; t["range"] = float(rng)
    scn["types"]["raider_w"] = t
    scn["terrain"] = dict(scn["terrain"]); scn["terrain"].update(preset="lane", ch=ch, wt=wt, h=1)
    y = 1025.0
    cols = max(1, min(5, int(50 * ch / 31)))
    mk = lambda side, n, x, facing, goal: dict(side=side, type="raider_w", count=n, formation="box", cols=cols,
                                               spacing=31.0, x=x, y=y, facing=facing, layer=1,
                                               order="attack_move", goal=[goal, y])
    scn["groups"] = [mk("A", n_att, 1300.0, 0.0, 2700.0), mk("B", n_def, 2700.0, 180.0, 1300.0)]
    return scn

def row(scn, seeds=range(20), window=20):
    sa = []; sb = []; w = 0; fr = []
    for s in seeds:
        r = run(scn, seed=s, trace=True)
        sa.append(r.survivors[0]); sb.append(r.survivors[1]); w += r.winner == 1
        t = exchange(r, scn, window=window)
        if t.firing_ratio is not None: fr.append(t.firing_ratio)
    n = len(sa)
    return sum(sa) / n, sum(sb) / n, w / n, (sum(fr) / len(fr) if fr else float("nan"))

if __name__ == "__main__":
    a_, d_ = 20, 10
    print(f"E1: {a_} v {d_}, both advancing in a 1000-long corridor, identical formations; mean survivors of the {a_} over 20 seeds (firing ratio A/B)")
    print(f"theory: linear {a_-d_} when one at a time can fire, square law {math.sqrt(a_*a_-d_*d_):.1f} when all can")
    rs = (40, 60, 100, 200)
    print("width\\range  " + "".join(f"{r:>16d}" for r in rs))
    for ch in (1, 2, 3, 4, 8):
        cells = []
        for r in rs:
            try: a, b, w, fr = row(build(ch, a_, d_, r)); cells.append(f"{a:5.1f} ({fr:4.2f})   ")
            except ValueError as e: cells.append("(skip)".rjust(14))
        print(f"{ch:>8d}    " + "  ".join(cells))
