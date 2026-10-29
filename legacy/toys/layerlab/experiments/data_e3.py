"""First systematic dataset (README 6, the lines-cross search): E3 on the ramp. One row per fight via
layerlab.batch. Swept: slope length, number of attackers, walking speed, where the defenders hold (offset beyond
the slope's top). Default rules (same-layer fire only), nearest-target, hard bodies, slope lanes."""
import sys, time, itertools
sys.path.insert(0, ".")
from experiments.e3_ramp import build
from layerlab.batch import run_rows, write_rows

def jobs(sls, ns, speeds, offs, seeds):
    out = []
    for sl, n, sp, off in itertools.product(sls, ns, speeds, offs):
        scn = build(sl, sp, None, n_att=n, def_off=off)
        st = {"terrain.sl": sl, "groups[0].count": n, "types.raider_w.speed": sp, "def_off": off}
        for s in seeds: out.append({"scenario": scn, "seed": s, "settings": st})
    return out

if __name__ == "__main__":
    t = time.time()
    J = jobs((125, 150, 175, 200, 250, 300, 400), (8, 10, 12, 14, 16), (40, 80, 150), (60, 150, 300), range(20))
    print(len(J), "fights"); rows = run_rows(J, processes=8)
    write_rows(rows, "results/data/e3_ramp.csv")
    print(f"{len(rows)} rows in {time.time()-t:.0f}s; errors: {sum(1 for r in rows if r['error'])}")
