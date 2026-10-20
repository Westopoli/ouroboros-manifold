import sys, math, collections
sys.path.insert(0, "/home/westopoli/Projects/om-push/wt/labrev2-captrace3")
from scripts.skilllab import sweep, fight as F
from scripts.skilllab.engine import Engine
feat = sweep.smoke_layouts()["192"]
build = sweep.Applied(sweep.default_builds("s3_layer_above", "play", feat), sweep._damage_up(0.75))
eng = Engine()
T = {"t": 0}; movers = collections.Counter(); resets = collections.Counter(); u31 = []
class Spy(F._Reengage):
    def tick(self, hp, fired):
        T["t"] += 1; t = T["t"]
        if t > 4000 and 1 in self.eligible:
            lim = F.REENGAGE_MOVED_WU ** 2
            mv = [u for u in self.side_ids[1] if hp[u] > 0 and (lambda p, r: (p[0]-r[0])**2+(p[1]-r[1])**2 > lim)(eng.unit_pos(self.w,u), self.ref[u])]
            if mv or fired[1]:
                resets[(tuple(mv), fired[1])] += 1
            if 4000 < t <= 4200 and 31 in self.ref and hp[31] > 0:
                u31.append((t, tuple(round(v,1) for v in eng.unit_pos(self.w,31)), eng.unit_destination(self.w,31) is not None))
        super().tick(hp, fired); Spy.last = self
F._Reengage = Spy
orig = eng.free_world
def hook(w):
    r = Spy.last
    print("resets from t>4000 (movers, fired1) -> count:", dict(resets))
    print("eligible", r.eligible, "role", r.role)
    print("u31 sample t4000-4200 every 10:", u31[::10])
    S1 = [u for u in r.side_ids[1] if eng.unit_alive(w,u)]; seen = eng.visible_enemies(w,1,[u for u in r.side_ids[0] if eng.unit_alive(w,u)])
    pts = [eng.unit_pos(w,u) for u in seen]; cx=sum(p[0] for p in pts)/len(pts); cy=sum(p[1] for p in pts)/len(pts)
    print("manual re-engage at cap: centroid", cx, cy, "seen", sorted(seen))
    for u in S1: eng.order_attack_move(w, [u], cx, cy)
    for k in range(1,6001):
        eng.step(w)
        a0=[u for u in r.side_ids[0] if eng.unit_alive(w,u)]; a1=[u for u in r.side_ids[1] if eng.unit_alive(w,u)]
        if k in (1,50,300) : print(" +%d dests"%k, {u:(None if eng.unit_destination(w,u) is None else 1) for u in a1}, "alive", len(a0), len(a1))
        if not a0 or not a1: print(" ended +%d alive"%k, len(a0), len(a1)); break
    orig(w)
eng.free_world = hook
r = F.fight(build(24, False), 1, False, eng)
print(r.outcome, r.survivors)
