"""E5, staying power (README 6.2). Duels (1 v 1 raiders, same layer, flat): A holds and B walks at it. A's longer
range than B's gives A a head start of (range_A - range_B) / speed_B seconds of free fire. `h` is the number of
hits to kill (hp / dmg); the mean kill time is h * interval (0.8 s). Theory (research Q77): when h is low, striking
first decides the fight; when h is high the head start washes out; for a duel at equal rates a head start of one
mean kill time raises the win chance from 0.50 to about 0.82. Both sides shoot the nearest enemy (only one)."""
import copy
from layerlab import scenario
from layerlab.scenario import set_path

def build(h=3.0, head_start_kills=1.0, base="scenarios/x0_mirror.toml", dmg=9.0, interval=0.8, speed=150.0, rb=100.0):
    scn = scenario.load(base)
    hp = dmg * h
    head_s = head_start_kills * h * interval                 # seconds
    ra = rb + head_s * speed                                 # A's range gives A that many seconds before B is in reach
    ta = copy.deepcopy(scn["types"]["raider"]); ta["hp"] = float(hp); ta["range"] = float(ra); ta["sensor"] = 3000.0
    tb = copy.deepcopy(scn["types"]["raider"]); tb["hp"] = float(hp); tb["range"] = float(rb); tb["sensor"] = 3000.0
    scn["types"]["duel_a"] = ta; scn["types"]["duel_b"] = tb
    y = 1000.0
    start = 1500.0
    scn["groups"] = [dict(side="A", type="duel_a", count=1, formation="line", x=start, y=y, facing=0.0, layer=3, order="hold", goal=[start, y]),
                     dict(side="B", type="duel_b", count=1, formation="line", x=start + ra + 600.0, y=y, facing=180.0, layer=3,
                          order="attack_move", goal=[start, y])]
    return set_path(scn, "rules.spawn_jitter", 0.0)
