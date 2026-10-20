import sys, math
sys.path.insert(0, "/home/westopoli/Projects/om-push/wt/labrev2-captrace3")
from scripts.skilllab import sweep, fight as F, firing
from scripts.skilllab.engine import Engine
feat = sweep.smoke_layouts()["192"]
build = sweep.Applied(sweep.default_builds("s3_layer_above", "play", feat), sweep._damage_up(0.75))
eng = Engine()
T = {"t": 0, "sil": []}
class Spy(F._Reengage):
    def tick(self, hp, fired):
        super().tick(hp, fired); T["t"] += 1; t = T["t"]
        if t % 500 == 0 or t in (2000, 2300, 2400, 2500):
            sd = {}
            for s in (0,1):
                sd[s] = [(u, tuple(round(v) for v in eng.unit_pos(self.w, u)), None if eng.unit_destination(self.w,u) is None else tuple(round(v) for v in eng.unit_destination(self.w,u)), eng.unit_target(self.w,u)) for u in self.side_ids[s] if hp[u]>0]
            print("t=%d silent=%s armed=%s count=%s" % (t, self.silent, self.armed, self.count))
            print("   s1:", sd[1])
        Spy.last = self
F._Reengage = Spy
orig = eng.free_world
def hook(w):
    r = Spy.last
    S = {s: [u for u in r.side_ids[s] if eng.unit_alive(w, u)] for s in (0,1)}
    smp = firing._Sample(eng, w, S[0], S[1], 360.0)
    print("engine_mode", smp.engine_mode)
    for s in (0,1):
        for u in S[s]:
            print(" s%d u%d type%d layer%d: %s" % (s, u, eng.unit_type(w,u), eng.unit_layer(w,u), {v: smp.composed(s,u,v) for v in S[1-s]}))
    orig(w)
eng.free_world = hook
r = F.fight(build(24, False), 1, False, eng)
print(r.outcome, r.survivors, r.ticks, r.reengage)
