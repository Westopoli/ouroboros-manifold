import sys, json, time
sys.path.insert(0, ".")
from exp import *
if __name__ == "__main__":
    res = {}; t0 = time.time()
    with FightPool(14) as pool:
        for mix in ("M1", "N1_RBo", "N3_VRBo"):
            for v in (0.2, 0.8):
                k = "%s_SIEGE_STRIKE_%s" % (mix, v)
                res[k] = run_fixed(pool, naive(MIXES[mix], settings={"OM_TP_CATMULT_SIEGE_STRIKE": v}), heads=20)
                print(k, res[k]["outcomes"], res[k]["mean_margin"], res[k]["mean_ticks"], flush=True)
    res["_wall_s"] = round(time.time() - t0, 1)
    json.dump(res, open(OUT + "exp_catmult.json", "w"), indent=1, default=str)
    print("wall", res["_wall_s"])
