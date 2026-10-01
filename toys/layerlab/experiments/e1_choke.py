"""E1, choke breadth (README 6.2): 20 walking attackers against 10 walking defenders holding the
far end of a channel (the `lane` preset). The channel width, in cells of 50 world units, sets how
many attackers can be in reach of the defenders at once. Theory: the larger side's survivors slide
from the square-law answer sqrt(20^2 - 10^2) = 17.3 toward the linear answer 20 - 10 = 10 as the
engaged width shrinks. Both sides use the nearest-target rule (Westley, 2026-10-01)."""
import copy
from layerlab import scenario
from layerlab.scenario import set_path
from layerlab.run import run

def build(ch, n_att=20, n_def=10, def_x=2250.0, base="scenarios/x0_mirror.toml"):
    scn = scenario.load(base)
    t = copy.deepcopy(scn["types"]["raider"]); t["movement_kind"] = "walk"
    scn["types"]["raider_w"] = t
    scn["terrain"] = dict(scn["terrain"]); scn["terrain"].update(preset="lane", ch=ch, wt=4, h=1)
    scn["groups"] = [
        dict(side="A", type="raider_w", count=n_att, formation="box", cols=5, x=800.0, y=1000.0, facing=0.0, layer=1,
             order="attack_move", goal=[def_x, 1000.0]),
        dict(side="B", type="raider_w", count=n_def, formation="line", x=def_x, y=1000.0, facing=180.0, layer=1,
             order="hold", goal=[def_x, 1000.0]),
    ]
    scn = set_path(scn, "rules.chase_when_idle", 0)
    return scn

def stats(scn, seeds=range(20)):
    sa = []; sb = []; w = 0; fa = []
    for s in seeds:
        r = run(scn, seed=s, trace=True)
        sa.append(r.survivors[0]); sb.append(r.survivors[1]); w += r.winner == 1
        fa.append(r.firing_ticks[0] / max(r.alive_ticks[0], 1))
    n = len(sa)
    return sum(sa) / n, sum(sb) / n, w / n, sum(fa) / n

if __name__ == "__main__":
    print("E1: 20 attackers vs 10 defenders at a choke; mean survivors over 20 seeds. theory for the 20: 17.3 (open) down to 10 (narrow)")
    print("channel(cells)  width(units)  attackers_left  defenders_left  attackers_win  attacker_firing_fraction")
    for ch in (1, 2, 3, 4, 6, 8, 12, 20, 36):
        try:
            a, b, w, f = stats(build(ch))
        except ValueError as e:
            print(f"{ch:>10d}  (skipped: {e})"); continue
        print(f"{ch:>10d} {ch*50:>12d} {a:>15.1f} {b:>15.1f} {w:>14.2f} {f:>20.2f}")
