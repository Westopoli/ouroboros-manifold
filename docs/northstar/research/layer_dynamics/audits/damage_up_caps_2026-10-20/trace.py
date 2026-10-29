import sys, math, dataclasses
sys.path.insert(0, "/home/westopoli/Projects/ouroboros-manifold/../om-push/wt/labrev2-captrace3")
from scripts.skilllab import sweep, fight as F
from scripts.skilllab.engine import Engine
heads, val = int(sys.argv[1]), float(sys.argv[2])
only = int(sys.argv[3]) if len(sys.argv) > 3 else None
feat = sweep.smoke_layouts()["192"]
build = sweep.Applied(sweep.default_builds("s3_layer_above", "play", feat), sweep._damage_up(val))
eng = Engine()
def alive(w, ids): return [u for u in ids if eng.unit_alive(w, u)]
class Spy(F._Reengage):
    log = []
    def tick(self, hp, fired):
        before = list(self.count)
        super().tick(hp, fired)
        t = self.t = getattr(self, "t", 0) + 1
        for s in (0, 1):
            if self.count[s] != before[s]:
                ids = self.ordered[s]
                Spy.log.append(("ENGAGE", t, s, [(u, self.engine.unit_pos(self.w, u)) for u in ids]))
                self.watch = (t, s, list(ids))
        wt = getattr(self, "watch", None)
        if wt and t in (wt[0]+1, wt[0]+50, wt[0]+300):
            Spy.log.append(("AFTER+%d" % (t - wt[0]), t, wt[1], [(u, tuple(round(v) for v in self.engine.unit_pos(self.w, u)), self.engine.unit_destination(self.w, u)) for u in wt[2] if hp[u] > 0]))
        Spy.last = (list(self.silent), list(self.armed), list(self.count))
F._Reengage = Spy
def describe(w, sides):
    for s in (0, 1):
        for u in sides[s]:
            t = eng.unit_type(w, u); st = eng.type_stats(w, t)
            print("  s%d u%d type%d(%s) layer%d pos(%.0f,%.0f) hp%.0f tgt%d dest=%s range%.0f reach%s" % (s, u, t, st["category"], eng.unit_layer(w, u), *eng.unit_pos(w, u), eng.unit_hp(w, u), eng.unit_target(w, u), eng.unit_destination(w, u), st["attack_range"], eng.profile_reach(w, t)))
    for s in (0, 1):
        vis = eng.visible_enemies(w, s, sides[1-s]); print(" side%d sees %s" % (s, sorted(vis)))
        for u in sides[s]:
            for v in sides[1-s]:
                a, b = eng.unit_pos(w, u), eng.unit_pos(w, v)
                print("   u%d->u%d code=%d dist=%.0f dlayer=%d" % (u, v, eng.can_engage(w, u, v), math.hypot(a[0]-b[0], a[1]-b[1]), eng.unit_layer(w, v)-eng.unit_layer(w, u)))
orig = eng.free_world
def hook(w):
    if hook.cur is not None:
        sides = {0: [], 1: []}
        for (wv, side), ids in eng._own.items():
            if wv == w.value: sides[side] = alive(w, ids)
        print("--- cap state; reengage silent/armed/count =", Spy.last)
        describe(w, sides)
        for e in Spy.log: print("  ", e)
        pos0 = {u: eng.unit_pos(w, u) for s in sides for u in sides[s]}
        for _ in range(300): eng.step(w)
        print("  moved in +300:", {u: round(math.hypot(eng.unit_pos(w,u)[0]-pos0[u][0], eng.unit_pos(w,u)[1]-pos0[u][1]),1) for u in pos0 if eng.unit_alive(w,u)})
    orig(w)
eng.free_world = hook
for swap in (False, True):
    for seed in range(3):
        if only is not None and only != (3 if swap else 0) + seed: continue
        Spy.log = []
        hook.cur = None
        r = F.fight(build(heads, swap), seed, swap, eng) if False else None
        setup = build(heads, swap)
        # probe quickly: run with hook enabled only if cap
        hook.cur = 1
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r = F.fight(setup, seed, swap, eng)
        print("swap=%s seed=%d -> %s surv=%s ticks=%d reengage=%s" % (swap, seed, r.outcome, r.survivors, r.ticks, r.reengage))
        if r.outcome == "cap": print(buf.getvalue())
