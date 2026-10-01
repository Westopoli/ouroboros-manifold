"""E3, the slope as a trickle (README 6.2), on the `ramp` preset. Walking attackers on layer 1 climb a slope
(joining layer 1 to the plateau layer 2) toward walking defenders holding the plateau just beyond its top.
Theory: a long slope strings the climbers out, which is E2 with the packet size set by the slope, so slow
units on long slopes fare worst. E-01 R-004-06 decides who can shoot whom on the slope: a climber below the
midline counts as being on layer 1 and only layer-1 units can attack it; at and above the midline it counts
as layer 2. Both sides shoot the nearest enemy (Westley, 2026-10-01). Hard bodies and the sidestep are on.
`cfg` is None (the default rules: only same-layer fire, so nobody shoots across the midline) or "LA", "LB",
"LC" (README 6.3 lever configurations; cross-layer fire on)."""
import copy
from layerlab import scenario
from layerlab.scenario import set_path
from layerlab.run import run
from layerlab.analysis import exchange
from experiments.configs import apply

def build(sl, speed, cfg=None, n_att=10, n_def=10, ru=0.8, d=0.8, sw=200.0, where="top", def_off=60.0, base="scenarios/x0_mirror.toml"):
    scn = scenario.load(base)
    t = copy.deepcopy(scn["types"]["raider"]); t["movement_kind"] = "walk"; t["speed"] = float(speed)
    scn["types"]["raider_w"] = t
    scn["terrain"] = dict(scn["terrain"]); scn["terrain"].update(preset="ramp", x1=40, sl=float(sl), sw=float(sw), g=1, h=1)
    top = 1975.0 + sl                                   # the slope's top edge (SPEC 6: bottom edge at x1*cell - cell/2)
    y = 1000.0
    # where the defenders hold: "top" = just beyond the slope's top edge; "midline" = on the plateau beside the
    # slope at the midline, 170 off its centre line (inside weapon range 200 of the midline for every length).
    if where == "top":
        dx, dy = top + float(def_off), y
    elif where == "midline":
        dx, dy = 1975.0 + sl / 2.0, y + 170.0 + 100.0
    else:
        raise ValueError(where)
    scn["groups"] = [
        dict(side="A", type="raider_w", count=n_att, formation="box", cols=5, spacing=31.0, x=900.0, y=y, facing=0.0,
             layer=1, order="attack_move", goal=[dx, dy]),
        dict(side="B", type="raider_w", count=n_def, formation="box", cols=5, spacing=31.0, x=dx, y=dy,
             facing=180.0, layer=2, order="hold", goal=[dx, dy]),
    ]
    scn = set_path(scn, "rules.chase_when_idle", 1)
    scn = set_path(scn, "run.stalemate_ticks", 3000) if "run" in scn else set_path(scn, "rules.stalemate_ticks", 3000)
    if cfg: scn = apply(scn, cfg, ru=ru, d=d)
    return scn

def row(scn, seeds=range(20), window=20):
    """Returns (attackers' win rate, stalemates or caps out of the runs, mean attacker survivors in the runs
    where someone won, mean firing ratio A/B, mean ticks)."""
    w = 0; stale = 0; sa = []; fr = []; ticks = []
    for s in seeds:
        r = run(scn, seed=s, trace=True); ticks.append(r.ticks)
        if r.winner == 1: w += 1
        if r.winner in (3, 4): stale += 1
        if r.winner in (1, 2, 5): sa.append(r.survivors[0])
        t = exchange(r, scn, window=window)
        if t.firing_ratio is not None: fr.append(t.firing_ratio)
    n = len(seeds)
    return w / n, stale, (sum(sa) / len(sa) if sa else float("nan")), (sum(fr) / len(fr) if fr else float("nan")), sum(ticks) / n

if __name__ == "__main__":
    for where in ("top", "midline"):
        for cfg in (None, "LA", "LB", "LC"):
            print(f"\nE3 ramp, defenders at the {where}, config {cfg or 'default (same-layer fire only)'}: attackers' win rate [stalemates of 20] (attacker survivors, firing ratio A/B); 10 v 10")
            print("slope length\\speed  " + "".join(f"{s:>30d}" for s in (40, 80, 150)))
            for sl in (150, 300, 600, 900):
                cells = []
                for sp in (40, 80, 150):
                    try:
                        w, st, sv, fr, tk = row(build(sl, sp, cfg, where=where))
                        cells.append(f"{w:4.2f} [{st:2d}] ({sv:4.1f}, {fr:4.2f})".ljust(30))
                    except ValueError:
                        cells.append("(skip)".ljust(30))
                print(f"{sl:>14d}      " + "".join(cells))
