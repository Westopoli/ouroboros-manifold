"""Design chat (b1): the mouth held properly. Defenders stand on the curve that is exactly one weapon reach from where
the attackers' front rank must stand when it reaches the mouth: a short flat line facing the corridor, with an arc at
each end curving back to the wall. All hold. Walls block sight. Prediction (attackers held to c firing, D defenders all
firing, attackers refilled from behind): defenders beat about D(D+1)/(2c)."""
import sys, copy, math
sys.path.insert(0,'.'); sys.path.insert(0,'experiments')
import b1_choke as c, b1_look as L
from layerlab import scenario
from layerlab.skill import plays, situation

def mouth_curve(sit, n, reach=185.0, spacing=50.0):
    ex, ey = c.exit_point(sit); half = sit.terrain["ch"] * 50.0 / 2.0 - 25.0     # end attackers stand 25 inside each wall
    flat = 2 * half; arc = math.pi / 2 * reach; total = flat + 2 * arc
    pts = []
    for i in range(n):
        s = (i + 0.5) * total / n
        if s < arc:                                   # upper arc, from the wall face round to the flat
            a = s / reach; pts.append((ex - reach * math.sin(a), ey - half - reach * math.cos(a)))
        elif s < arc + flat:
            pts.append((ex - reach, ey - half + (s - arc)))
        else:
            a = (s - arc - flat) / reach; pts.append((ex - reach * math.cos(a), ey + half + reach * math.sin(a)))
    return pts, total / n

def curve_build(sit, n, unit="raider", reach=185.0):
    base = situation.base_scenario(sit); pts, sp = mouth_curve(sit, n, reach)
    def build(n_enemy, swap):
        scn = copy.deepcopy(base)
        ours = [{"side": "A", "type": unit, "count": 1, "formation": "line", "x": x, "y": y, "facing": 0.0, "layer": sit.layer,
                 "order": "hold", "target_policy": "nearest"} for x, y in pts]
        theirs = plays._compose(sit, base, 1, {unit: n_enemy}, frozenset(), "line", (sit.mix, {unit: n}), True, layer=sit.layer)
        if swap:
            ours = [dict(g, side="B") for g in ours]; theirs = [dict(g, side="A") for g in theirs]
        g = ours + theirs
        scn["groups"] = [x for x in g if x["side"] == "A"] + [x for x in g if x["side"] == "B"]
        scenario.to_c(scn)
        return scn
    build.spacing = sp
    return build

if __name__=='__main__':
    sit = c.lane_sit('raider')
    for n in (8, 12, 16):
        b = c.with_walls(curve_build(sit, n), sit)
        print(f"\n--- {n} defenders on the mouth curve, spacing {curve_build(sit, n).spacing:.0f}; prediction: beat about {n*(n+1)/8:.0f}")
        L.look(f'{n} on the curve', b, 2 * n)
        c.table(f'{n} raiders on the mouth curve, holding; walls block sight', b, n, sorted(set([n, int(1.25*n), int(1.5*n), int(1.75*n), 2*n, int(2.5*n), 3*n, 4*n])), 10)
