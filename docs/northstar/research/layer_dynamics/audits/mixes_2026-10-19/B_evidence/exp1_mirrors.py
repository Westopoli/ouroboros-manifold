"""E1: naive blob v naive blob, same mix both sides, heads 12..20 against 16. C0 per mix, defects, agreement."""
import sys, json, time
sys.path.insert(0, "/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/b1e8769e-404e-4263-be23-8535a58b0e59/scratchpad/mix_B")
from mixlib import *
MIXES = {
 "M0 V16": (("Vanguard", 16),), "M1 V8 R8": (("Vanguard", 8), ("Raider", 8)), "M2 V8 I8": (("Vanguard", 8), ("Interceptor", 8)),
 "M3 V8 B8": (("Vanguard", 8), ("Bombard", 8)), "M4 V8 Bas8": (("Vanguard", 8), ("Bastion", 8)),
 "W16": (("Warden", 16),), "V8 W8": (("Vanguard", 8), ("Warden", 8)), "R8 B8": (("Raider", 8), ("Bombard", 8)),
 "I8 Bas8": (("Interceptor", 8), ("Bastion", 8)), "R8 W8": (("Raider", 8), ("Warden", 8)),
 "R16": (("Raider", 16),), "B16": (("Bombard", 16),), "Bas16": (("Bastion", 16),), "I16": (("Interceptor", 16),),
 "six R3 I3 V3 W2 B3 Bas2": (("Raider", 3), ("Interceptor", 3), ("Vanguard", 3), ("Warden", 2), ("Bombard", 3), ("Bastion", 2)),
}
HEADS = (12, 15, 16, 17, 20)
if __name__ == "__main__":
    jobs, keys = [], []
    for name, mix in MIXES.items():
        b = build_naive(mix)
        for h in HEADS:
            for swap in (False, True):
                for seed in (0, 1):
                    s = b(h, swap); jobs.append((s, seed, swap)); keys.append((name, h))
    t = time.time()
    with pool.FightPool(int(sys.argv[1]) if len(sys.argv) > 1 else 6, lean=True) as p:
        res = p.map(jobs)
    wall = time.time() - t
    out = {}
    for (name, h), f in zip(keys, res):
        out.setdefault(name, {}).setdefault(h, []).append(f)
    table = {n: {h: summarize(fs) for h, fs in d.items()} for n, d in out.items()}
    json.dump({"wall_s": wall, "fights": len(jobs), "table": table}, open(sys.argv[2], "w"), indent=1)
    print("fights", len(jobs), "wall", round(wall, 1))
    for n, d in table.items():
        print(n.ljust(26), " ".join("%d:%d/%d%s t%d" % (h, s["win0"], s["n"], "" if set(s["outcomes"]) <= {"side0", "side1"} else "!" + ",".join("%s%d" % kv for kv in s["outcomes"].items() if kv[0] not in ("side0","side1")), s["mean_ticks"]) for h, s in d.items()),
              "| agree", dict(sum((collections.Counter(s["agreement"]) for s in d.values()), collections.Counter())))
