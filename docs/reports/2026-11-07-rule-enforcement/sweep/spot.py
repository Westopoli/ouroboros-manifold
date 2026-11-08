"""Spot check: python spot.py <L-id> <seed> <on|off> <tick_lo> <tick_hi> <unit ids comma>  -> per-tick rows
(tick, unit, role, x, y, layer, alive, hp, target, can_shoot(target), dest, fired_this_tick)"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, ".")
import inv_check
inv_check.ALLOW_R6 = True
L, seed, sight, lo, hi, units = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), [int(x) for x in sys.argv[6].split(",")]
r = inv_check.run_one("docs/northstar/research/layer_dynamics/catalogue/%s.toml" % L, seed, sight, trace={"lo": lo, "hi": hi, "units": units})
for row in r["trace"]:
    print(*row)
