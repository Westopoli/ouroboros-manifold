import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, ".")
import inv_check
from scripts.skilllab import engine as E
L, sight, tick, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
inner = E.Engine.step
def wrap(self, w):
    inner(self, w)
    chk = inv_check._CTX.get("chk")
    if chk and chk.tick in range(tick - 1, tick + 2):
        pa, pb = self.unit_pos(w, a), self.unit_pos(w, b)
        print("tick", chk.tick, "a", pa, "layer", self.unit_layer(w, a), "b", pb, "layer", self.unit_layer(w, b), "dist2d %.1f" % math.dist(pa, pb),
              "see a->b", self.can_see(w, a, b), "see b->a", self.can_see(w, b, a), "shoot a->b", self.can_shoot(w, a, b), "shoot b->a", self.can_shoot(w, b, a),
              "playersee side", [bool(self._lib.om_player_can_see(w, s, e)) for s, e in ((0, b), (1, a))])
E.Engine.step = wrap
inv_check.ALLOW_R6 = True
inv_check.run_one("docs/northstar/research/layer_dynamics/catalogue/%s.toml" % L, 1, sight)
