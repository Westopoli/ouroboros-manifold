import json, collections, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
R = [json.loads(l) for l in open(os.path.join(HERE, "sweep_results.jsonl"))]
ok = [r for r in R if "viol" in r and r["tag"] != "dup"]
print("results", len(R), "ok non-dup", len(ok), "rejects", [(r["layout"], r["sight"], r["reject"]) for r in R if "reject" in r], "errors", [(r["layout"], r["error"][-200:]) for r in R if "error" in r])
print("fights by sight", collections.Counter(r["sight"] for r in ok), "layouts", len({r["layout"] for r in ok}), "unit-ticks", sum(r["unit_ticks"] for r in ok))
import inv_check
inv = collections.defaultdict(lambda: {"cnt": 0, "layouts": set(), "fights": 0, "by": collections.Counter(), "first": None, "ex": []})
for r in ok:
    for k, v in r["viol"].items():
        d = inv[k]; d["cnt"] += v["count"]; d["layouts"].add(r["layout"]); d["fights"] += 1; d["by"][(r["layout"], r["sight"], r["seed"])] += v["count"]
        if v["examples"] and len(d["ex"]) < 3 and all(e[0] != r["layout"] for e in d["ex"]):
            d["ex"].append((r["layout"], r["sight"], r["seed"], v["examples"][0]))
        f = (v["first"][0], r["layout"], r["sight"], r["seed"], v["first"][1], v["first"][2]) if v["first"] else None
        if f and (d["first"] is None or f[0] < d["first"][0]): d["first"] = f
tot = sum(r["unit_ticks"] for r in ok)
print("\n%-6s %9s %7s %7s  %s" % ("inv", "count", "layouts", "fights", "name"))
for k in sorted(inv, key=lambda s: (int("".join(c for c in s[1:] if c.isdigit()) or 0), s)):
    d = inv[k]; print("%-6s %9d %7d %7d  %s" % (k, d["cnt"], len(d["layouts"]), d["fights"], inv_check.NAMES.get(k, "")))
print("\nclean (never seen):", [k for k in inv_check.NAMES if k not in inv])
print("\nDETERMINISM:")
byk = collections.defaultdict(list)
for r in R:
    if "hash" in r: byk[(r["layout"], r["sight"], r["seed"])].append(r["hash"])
n = bad = 0
for k, hs in byk.items():
    if len(hs) > 1:
        n += 1
        if len(set(hs)) > 1: bad += 1; print("MISMATCH", k, hs)
print("pairs compared", n, "mismatches", bad)
json.dump({k: {"cnt": d["cnt"], "layouts": sorted(d["layouts"]), "fights": d["fights"], "first": d["first"], "ex": d["ex"],
               "by": {"%s|%s|%s" % k2: c for k2, c in d["by"].most_common(8)}} for k, d in inv.items()}, open(os.path.join(HERE, "agg.json"), "w"), indent=1, default=str)
