import sys, json, collections, dataclasses, time
sys.path.insert(0, "/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/b1e8769e-404e-4263-be23-8535a58b0e59/scratchpad/mix_B")
from mixlib import *
def main():
    jobs, keys = [], []
    for play in ("s3_types_by_reach", "s3_layer_above"):
        b = plays_space.scan_build(play)
        for label, st in (("base", {}), ("two-layer knobs 0.25", {"OM_TP_RANGE_UP_2": 0.25, "OM_TP_DAMAGE_UP_2": 0.25, "OM_TP_VISION_UP_2": 0.05, "OM_TP_VISION_DOWN_2": 0.05}),
                          ("one-layer knobs 0.25", {"OM_TP_RANGE_UP_1": 0.25, "OM_TP_DAMAGE_UP_1": 0.25})):
            for seed in (0, 1):
                s = b(None, 20, False)
                jobs.append((dataclasses.replace(s, settings={**s.settings, **st}), seed, False)); keys.append((play, label))
    WM = {"V14 W2": (("Vanguard", 14), ("Warden", 2)), "V12 W4": (("Vanguard", 12), ("Warden", 4)),
          "R7 V7 W2": (("Raider", 7), ("Vanguard", 7), ("Warden", 2)), "B7 V7 W2": (("Bombard", 7), ("Vanguard", 7), ("Warden", 2))}
    for name, mix in WM.items():
        b = build_naive(mix)
        for heads in (16, 20):
            for swap in (False, True):
                jobs.append((b(heads, swap), 0, swap)); keys.append(("warden " + name, heads))
    t = time.time()
    with pool.FightPool(10, lean=True) as p:
        res = p.map(jobs)
    rows = collections.defaultdict(list)
    for k, f in zip(keys, res):
        rows[k].append((f.outcome, f.ticks, tuple(f.survivors), round(f.margin, 4)))
    for k, v in rows.items(): print(k, v)
    print("fights", len(jobs), "wall", round(time.time() - t, 1))
    json.dump({"|".join(map(str, k)): v for k, v in rows.items()}, open("runs/exp3c.json", "w"), indent=1)

if __name__ == '__main__':
    main()
