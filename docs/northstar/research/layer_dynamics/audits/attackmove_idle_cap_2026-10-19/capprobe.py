import sys, math
from scripts.skilllab import sweep, fight as F, scenes, plays
from scripts.skilllab.engine import Engine

def survivors(eng, w):
    out = {0: [], 1: []}
    for (wv, side), ids in eng._own.items():
        if wv == w.value:
            out[side] = [u for u in ids if eng.unit_alive(w, u)]
    return out

def describe(eng, w, label):
    S = survivors(eng, w)
    print("== %s: alive side0=%s side1=%s" % (label, S[0], S[1]))
    for s in (0, 1):
        for u in S[s]:
            x, y = eng.unit_pos(w, u)
            t = eng.unit_type(w, u)
            st = eng.type_stats(w, t)
            print(" s%d u%d type%d cat%s layer%d pos(%.0f,%.0f) hp%.0f tgt%d dest%s face%.2f range%.0f reach%s" % (
                s, u, t, st["category"], eng.unit_layer(w, u), x, y, eng.unit_hp(w, u), eng.unit_target(w, u),
                eng.unit_destination(w, u), eng.unit_facing(w, u), st["attack_range"], eng.profile_reach(w, t)))
    for s in (0, 1):
        vis = eng.visible_enemies(w, s, S[1 - s])
        print(" side%d sees %s of %s" % (s, sorted(vis), S[1 - s]))
        for u in S[s]:
            row = []
            for v in S[1 - s]:
                x, y = eng.unit_pos(w, u); ex, ey = eng.unit_pos(w, v)
                row.append("u%d: ce=%d dist=%.0f sight=%s shoot=%s" % (v, eng.can_engage(w, u, v), math.hypot(ex-x, ey-y), eng.can_see(w, u, v), eng.can_shoot(w, u, v)))
            print("  u%d -> %s" % (u, " | ".join(row)))
    return S

def run(setup, seed, swap, extra=300, lib=None):
    eng = Engine(lib)
    orig = eng.free_world
    def hook(w):
        S = describe(eng, w, "cap tick")
        pos0 = {u: eng.unit_pos(w, u) for s in S for u in S[s]}
        for _ in range(extra): eng.step(w)
        moved = {u: round(math.hypot(eng.unit_pos(w,u)[0]-pos0[u][0], eng.unit_pos(w,u)[1]-pos0[u][1]),1) for u in pos0 if eng.unit_alive(w,u)}
        print("after +%d ticks moved:" % extra, moved, "alive", {s: len(survivors(eng, w)[s]) for s in (0,1)})
        orig(w)
    eng.free_world = hook
    res = F.fight(setup, seed, swap, eng)
    print(res.outcome, res.survivors, res.ticks, res.first_contact_tick)
    return res
