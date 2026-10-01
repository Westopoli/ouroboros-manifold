"""E1, choke breadth (README 6.2), and the reserves case (README 6.3): both sides walk inside a long
corridor (the `lane` preset, 1000 units long); n_att attackers in a box attack-move at n_def defenders
holding a box as wide as the corridor allows deeper in (the attackers start as a 5-wide box so a wide corridor lets them spread). The corridor width, in 50-unit cells, bounds how many bodies can be within
reach of one point. Theory for the larger side: survivors slide from the square-law sqrt(a^2 - d^2) toward
the linear a - d as the engaged width shrinks. Both sides shoot the nearest enemy (Westley, 2026-10-01).
Hard bodies and the sidestep are on (toys/layerlab SPEC 5.10)."""
import copy, math
from layerlab import scenario
from layerlab.scenario import set_path
from layerlab.run import run
from layerlab.analysis import exchange

def build(ch, n_att=20, n_def=10, wt=20, base="scenarios/x0_mirror.toml"):
    scn = scenario.load(base)
    t = copy.deepcopy(scn["types"]["raider"]); t["movement_kind"] = "walk"
    scn["types"]["raider_w"] = t
    scn["terrain"] = dict(scn["terrain"]); scn["terrain"].update(preset="lane", ch=ch, wt=wt, h=1)
    y = 1025.0
    scn["groups"] = [
        dict(side="A", type="raider_w", count=n_att, formation="box", cols=5, spacing=31.0, x=700.0, y=y, facing=0.0, layer=1,
             order="attack_move", goal=[2400.0, y]),
        dict(side="B", type="raider_w", count=n_def, formation="box", cols=max(1, min(5, int(50 * ch / 31))), spacing=31.0,
             x=2250.0, y=y, facing=180.0, layer=1, order="hold", goal=[2250.0, y]),
    ]
    return scn

def row(scn, seeds=range(20), window=20):
    sa = []; sb = []; w = 0; fr = []; dr = []; ag = []
    for s in seeds:
        r = run(scn, seed=s, trace=True)
        sa.append(r.survivors[0]); sb.append(r.survivors[1]); w += r.winner == 1
        t = exchange(r, scn, window=window)
        if t.firing_ratio is not None: fr.append(t.firing_ratio)
        if t.damage_ratio is not None: dr.append(t.damage_ratio)
        if t.n_agree + t.n_disagree: ag.append(t.n_agree / (t.n_agree + t.n_disagree))
    m = lambda v: sum(v) / len(v) if v else float("nan")
    n = len(sa)
    return sum(sa) / n, sum(sb) / n, w / n, m(fr), m(dr), m(ag)

if __name__ == "__main__":
    a_, d_ = 20, 10
    print(f"E1: {a_} attackers v {d_} defenders in a corridor. theory for the larger side: square law {math.sqrt(a_*a_-d_*d_):.1f} left, linear {a_-d_} left")
    print(" width(cells)  attackers_left  defenders_left  attackers_win  firing_ratio A/B  damage_ratio A/B  windows_agreeing")
    for ch in (1, 2, 3, 4, 8, 20):
        try: a, b, w, fr, dr, ag = row(build(ch, a_, d_))
        except ValueError as e: print(f"{ch:>8d}  skipped: {str(e)[:70]}"); continue
        print(f"{ch:>10d} {a:15.1f} {b:15.1f} {w:14.2f} {fr:17.2f} {dr:17.2f} {ag:17.2f}")
