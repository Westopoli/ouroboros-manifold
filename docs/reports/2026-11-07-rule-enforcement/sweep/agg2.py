"""Per-layout matrix and applicability. Usage: PYTHONPATH=<dir> python agg2.py [results.jsonl]"""
import json, collections, sys, os, tomllib
HERE = os.path.dirname(os.path.abspath(__file__))
R = [json.loads(l) for l in open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "sweep_results.jsonl"))]
ok = [r for r in R if "viol" in r and r["tag"] != "dup"]
KEYS = ["I1", "I2a", "I2as", "I2b", "I4b", "I4bg", "I5b", "I5t", "I8", "I10s", "I11x", "I11nl", "I13", "I14", "I23", "I27", "I29", "I30"]
lay = collections.defaultdict(lambda: collections.defaultdict(int))
meta = {}
for r in ok:
    meta[r["layout"]] = (r["n_a"], r["n_b"], r["orders"], ",".join(r["features"]) or "-", r["landscape"])
    for k in KEYS:
        v = r["viol"].get(k)
        if v: lay[r["layout"]][k] += v["count"]
    lay[r["layout"]]["_ut_" + r["sight"]] += r["unit_ticks"]
print("| layout | a:b | orders | feature | land | " + " | ".join(KEYS) + " |")
print("|" + "---|" * (len(KEYS) + 5))
for L in sorted(lay):
    m = meta[L]
    print("| %s | %d:%d | %s | %s | %s | " % (L, m[0], m[1], m[2], m[3], m[4]) + " | ".join(str(lay[L].get(k, "")) if lay[L].get(k) else "." for k in KEYS) + " |")
# fights by sight and unit-ticks
for s in ("on", "off", "control"):
    xs = [r for r in ok if r["sight"] == s]
    print(s, "fights", len(xs), "layouts", len({r["layout"] for r in xs}), "unit-ticks", sum(r["unit_ticks"] for r in xs))
# per sight counts of key invariants
print("\nper sight (count / fights hit / fights):")
for k in KEYS:
    row = []
    for s in ("on", "off", "control"):
        xs = [r for r in ok if r["sight"] == s]
        row.append("%s: %d / %d / %d" % (s, sum(r["viol"].get(k, {}).get("count", 0) for r in xs), sum(1 for r in xs if k in r["viol"]), len(xs)))
    print(k, " | ".join(row))
# block-bearing layouts
bl = [r for r in ok if r["features"] and any(f in ("chokepoint", "cover", "city", "transit", "flank_route", "objective", "staging", "hazard_anchor", "trap") for f in r["features"])]
print("\nlayouts with planar blocks (approx):", len({r["layout"] for r in bl}))
