import sys, json, time
sys.path.insert(0, ".")
from exp import *

def p_int_below():   # M2: enemy on layer 2; side 0 Vanguards level with it (layer 2), Interceptors two below (layer 0) fire up 2
    x = -GAP / 2
    g = [blob(0, "Interceptor", 8, x, layer=0), blob(0, "Vanguard", 8, x, layer=2)]
    return make_setup(g + enemy(MIXES["M2"], layer=2), types(["Vanguard", "Interceptor"]))

def p_int_above2():  # M2 blunder control: Interceptors two ABOVE the enemy (cannot fire down 2; enemy Interceptors fire up 2)
    x = -GAP / 2
    g = [blob(0, "Interceptor", 8, x, layer=2), blob(0, "Vanguard", 8, x, layer=0)]
    return make_setup(g + enemy(MIXES["M2"], layer=0), types(["Vanguard", "Interceptor"]))

def p_types_by_reach_now():  # the shipped s3_types_by_reach shape: Interceptors one above
    x = -GAP / 2
    g = [blob(0, "Interceptor", 8, x, layer=1), blob(0, "Vanguard", 8, x, layer=0)]
    return make_setup(g + enemy(MIXES["M2"], layer=0), types(["Vanguard", "Interceptor"]))

MIXES["N2b_V8W8"] = (("Vanguard", 8), ("Warden", 8))
if __name__ == "__main__":
    res = {}; t0 = time.time()
    with FightPool(14) as pool:
        P = {"int_below2_M2": p_int_below, "int_above2_M2_blunder": p_int_above2, "types_by_reach_as_shipped_M2": p_types_by_reach_now,
             "mirror_N2b_V8W8": naive(MIXES["N2b_V8W8"])}
        for k, fn in P.items():
            res[k] = {"fixed16": run_fixed(pool, fn), "scan": run_scan(pool, fn)}
            print(k, res[k]["fixed16"]["outcomes"], res[k]["fixed16"]["mean_ticks"], res[k]["fixed16"]["agreement"], res[k]["scan"]["beats"], res[k]["scan"]["loses_to"], res[k]["scan"]["ceiling"], res[k]["scan"]["fights"], res[k]["scan"]["wall_s"], flush=True)
    res["_wall_s"] = round(time.time() - t0, 1)
    json.dump(res, open(OUT + "exp_reach.json", "w"), indent=1, default=str)
    print("wall", res["_wall_s"])
