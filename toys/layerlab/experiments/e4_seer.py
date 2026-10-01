"""E4, vision as a dial, with the seer (README 6.2, Q-E12-01 closed 2026-10-01: a roster unit, costly, wide
cross-layer sight, no attack). High side A (10 raiders, layer 4) against low side B (n raiders, layer 3) whose
raiders have a very short sensor (they cannot see up at their weapon range); B may also field one seer
(sensor 1500, so 750 across one layer, no attack) that advances with them. Sides share vision, so one seer
that sees A lets all of B target A. Both sides attack-move (symmetric approach), nearest-target, cross-layer
fire on between adjacent layers at full range and damage (config LA, README 6.3). The question: how many
extra raiders is the seer worth to B, and how does the answer depend on the seer's cost and sight?"""
import copy
from layerlab import scenario
from layerlab.scenario import set_path

def build(n_b=10, seer=True, seer_sensor=1500.0, raider_sensor=100.0, seer_hp=80.0, seer_behind=150.0, base="scenarios/x0_mirror.toml"):
    scn = scenario.load(base)
    cross = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0]
    scn = set_path(scn, "rules.range_mult", cross); scn = set_path(scn, "rules.dmg_mult", cross); scn = set_path(scn, "rules.aoe_layer_mult", cross)
    t = copy.deepcopy(scn["types"]["raider"]); t["sensor"] = float(raider_sensor); scn["types"]["raider_b"] = t
    s = copy.deepcopy(scn["types"]["seer"]); s["sensor"] = float(seer_sensor); s["hp"] = float(seer_hp); scn["types"]["seer_b"] = s
    y = 1000.0
    g = [dict(side="A", type="raider", count=10, formation="line", x=1000.0, y=y, facing=0.0, layer=4, order="attack_move", goal=[3000.0, y]),
         dict(side="B", type="raider_b", count=n_b, formation="line", x=3000.0, y=y, facing=180.0, layer=3, order="attack_move", goal=[1000.0, y])]
    if seer:
        g.append(dict(side="B", type="seer_b", count=1, formation="line", x=3000.0 + seer_behind, y=y, facing=180.0, layer=3,
                      order="move", goal=[1000.0, y]))
    scn["groups"] = g
    return scn
