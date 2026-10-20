"""Mix experiments for analysis mix_A. Read-only on the repo: imports the lab from the worktree, writes nothing there."""
import dataclasses, math, sys, json, time
sys.path.insert(0, "/home/westopoli/Projects/om-push/wt/mixA")
from scripts.skilllab import plays_space as ps, scan as scan_mod
from scripts.skilllab.contract import Group

UNITS = 16
GAP = ps.START_GAP
REACH = {"Vanguard": (0, 0), "Warden": (0, 0), "Raider": (1, 1), "Interceptor": (2, 1), "Bombard": (0, 2), "Bastion": (0, 2)}

def types(names, clone=()):
    """Builtin where the reach is (0,0) (keeps type-keyed specials: Warden aura, Bastion cap); else a clone with reach (the lab's way)."""
    out = {}
    for n in names:
        base = n.rstrip("C") if n.endswith("C") and n[:-1] in REACH else n
        if REACH[base] != (0, 0) or n in clone:
            out[n] = {"base": base, "reach": REACH[base]}
    return out

def blob(side, unit, n, x, layer=0, y=0.0, order="attack_move"):
    return ps._g(side, unit, n, "blob", x, y, order=order, layer=layer, radius=80 + 12 * math.sqrt(n))

def line(side, unit, n, x, layer=0, y=0.0, spacing=30.0, order="attack_move"):
    return ps._g(side, unit, n, "line", x, y, order=order, layer=layer, spacing=spacing)

def enemy(mix, layer=0, layers=None):
    return [blob(1, t, n, GAP / 2, layer=(layers or {}).get(t, layer)) for t, n in mix]

def make_setup(groups, unit_types, settings=None):
    # ruling 6: a meeting is both sides attack-moved to one point; the play's centre (0, 0) is canvas centre after the shift
    return dataclasses.replace(ps._setup(groups, unit_types=unit_types, settings=settings), point=(ps.CANVAS[0] / 2, ps.CANVAS[1] / 2))

def scan_build(fn):
    """As plays_space.scan_build without terrain: side 1 scaled to enemy_heads by largest remainder."""
    def build(enemy_heads, swap):
        setup = fn()
        en = [g for g in setup.groups if g.side == 1]
        counts = ps._scale(en, enemy_heads)
        new = {}
        for g, c in zip(en, counts):
            params = dict(g.params)
            if g.formation == "blob":
                params["radius"] = 80 + 12 * math.sqrt(c)
            new[id(g)] = dataclasses.replace(g, count=c, params=params)
        return dataclasses.replace(setup, groups=tuple(new.get(id(g), g) for g in setup.groups))
    return build

def naive(mix, settings=None, extra_types=()):
    names = [t for t, _ in mix]
    return lambda: make_setup([blob(0, t, n, -GAP / 2) for t, n in mix] + enemy(mix), types(names + list(extra_types)), settings)

def row(f):
    return dict(outcome=f.outcome, margin=round(f.margin, 3), surv=list(f.survivors), heads=list(f.heads), ticks=f.ticks,
                fw=[round(x, 1) for x in f.firing_window], ww=[round(x, 1) for x in f.weighted_window],
                fs=[round(x, 1) for x in f.firing_unit_seconds], ws=[round(x, 1) for x in f.weighted_unit_seconds],
                pc=f.predicted_count, pt=f.predicted_type, agree=f.agreement, contact=f.first_contact_tick)
