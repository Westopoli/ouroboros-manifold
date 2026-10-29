"""E3: (a) are the two-layer knobs live in the current sweep plays? (b) which units do the sweep's baselines field? (c) small Warden counts."""
import sys, json, collections, dataclasses
sys.path.insert(0, "/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/b1e8769e-404e-4263-be23-8535a58b0e59/scratchpad/mix_B")
from mixlib import *
from scripts.skilllab import sweep
out = {}
# (b) baselines' rosters on the smoke layouts
lay = sweep.smoke_layouts()
for play in ("s3_layer_above", "s3_types_by_reach", "s2_concave"):
    for layout, feats in list(lay.items())[:1]:
        for role in ("play",) + tuple(sweep.baseline_roles(play)):
            s = sweep.default_builds(play, role, feats)(16, False)
            c0 = collections.Counter(); c1 = collections.Counter()
            for g in s.groups:
                (c0 if g.side == 0 else c1)[(g.unit, g.layer)] += g.count
            out.setdefault("baseline_rosters", {})["%s/%s/%s" % (play, layout, role)] = {"side0": {"%s@L%d" % k: v for k, v in c0.items()}, "side1": {"%s@L%d" % k: v for k, v in c1.items()}, "prefight": None}
            print(play, layout, role, dict(c0), dict(c1))
# (a) dead knob: s3_types_by_reach and s3_layer_above, no terrain, RANGE_UP_2+DAMAGE_UP_2 1.0 v 0.25; RANGE_UP_1 0.25 as positive control
jobs, keys = [], []
for play in ("s3_types_by_reach", "s3_layer_above"):
    b = plays_space.scan_build(play)
    for label, st in (("base", {}), ("up2=0.25", {"OM_TP_RANGE_UP_2": 0.25, "OM_TP_DAMAGE_UP_2": 0.25, "OM_TP_VISION_UP_2": 0.05, "OM_TP_VISION_DOWN_2": 0.05}),
                      ("up1=0.25", {"OM_TP_RANGE_UP_1": 0.25, "OM_TP_DAMAGE_UP_1": 0.25})):
        for heads in (16, 20):
            for seed in (0, 1):
                s = b(None, heads, False)
                s = dataclasses.replace(s, settings={**s.settings, **st})
                jobs.append((s, seed, False)); keys.append((play, label, heads, seed))
# (c) small Warden counts, naive mirror at 16 v 16 and 16 v 20
WM = {"V14 W2": (("Vanguard", 14), ("Warden", 2)), "V12 W4": (("Vanguard", 12), ("Warden", 4)), "R7 V7 W2": (("Raider", 7), ("Vanguard", 7), ("Warden", 2)),
      "B7 V7 W2": (("Bombard", 7), ("Vanguard", 7), ("Warden", 2))}
for name, mix in WM.items():
    b = build_naive(mix)
    for heads in (16, 20):
        for swap in (False, True):
            for seed in (0, 1):
                jobs.append((b(heads, swap), seed, swap)); keys.append(("warden", name, heads, seed))
with pool.FightPool(8, lean=True) as p:
    res = p.map(jobs)
rows = collections.defaultdict(list)
for k, f in zip(keys, res):
    rows[k[:3]].append((f.outcome, f.ticks, f.survivors, round(f.margin, 4)))
for k, v in rows.items():
    print(k, v)
out["fights"] = {"|".join(map(str, k)): v for k, v in rows.items()}
json.dump(out, open(sys.argv[1], "w"), indent=1, default=str)
