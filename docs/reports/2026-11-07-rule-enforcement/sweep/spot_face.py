import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, ".")
import inv_check
from scripts.skilllab import engine as E
L, sight, lo, hi, a = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
inner = E.Engine.step
def wrap(self, w):
    inner(self, w)
    chk = inv_check._CTX.get("chk")
    if chk and lo <= chk.tick <= hi:
        t = self.unit_target(w, a); pa = self.unit_pos(w, a)
        bear = math.atan2(self.unit_pos(w, t)[1] - pa[1], self.unit_pos(w, t)[0] - pa[0]) if t else None
        print("tick", chk.tick, "unit", a, "pos (%.1f,%.1f)" % pa, "facing %.2f" % self.unit_facing(w, a), "target", t, "bearing", bear and round(bear, 2), "fired", a in self.fire_attackers(w))
E.Engine.step = wrap
inv_check.ALLOW_R6 = True
inv_check.run_one("docs/northstar/research/layer_dynamics/catalogue/%s.toml" % L, 1, sight)
