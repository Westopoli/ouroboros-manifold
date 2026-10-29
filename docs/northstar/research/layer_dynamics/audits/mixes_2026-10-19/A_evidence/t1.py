import time, sys
sys.path.insert(0, ".")
from mixlab import *
from scripts.skilllab import fight
b = scan_build(naive((("Vanguard", 8), ("Raider", 8))))
for h in (16, 48):
    t = time.time(); f = fight.fight(b(h, False), 0, False); print(h, round(time.time() - t, 2), row(f))
