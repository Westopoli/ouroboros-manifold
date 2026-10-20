# Which draw layouts fit batch one's plays (information only, no swap made)

Date 2026-10-20. Base: `origin/push/labrev2-lab` at c2d9bce8f6f2d98feb4df6e1c077cd947f5f8b90 (detached worktree). Nothing was fought; every word below is `scenes.preflight` on the built Setup.

## What was run

Layouts: all 200 of `depth.lhs_draw(200, 0)` (the draw batch one's smoke indices 81, 78, 192 come from; the whole draw was affordable, about 1.7 s per layout). Map seed per layout is `sweep._layout_seed` (its first index in the draw), as the smoke run does. Setups come from `sweep.default_builds(play, "play", features)` and `scenes.preflight(setup, engine)` at 8, 16, 24 and 48 enemy heads; baselines from `default_builds(play, "naive_attacker", ...)` and the roles `sweep.baseline_roles` names for the play (naive defender, with `naive_defender=True` blind-post check), same headcounts. Command, from the worktree root:

```
PYTHONPATH=. nice -n 10 /home/westopoli/Projects/agora/.venv/bin/python fit.py 0 200 all.json
```

`fit.py` (kept in the scratch directory, reproduced here so the run can be repeated):

```python
import json, sys, time
from scripts.skilllab import depth, sweep, scenes
from scripts.skilllab.engine import Engine
PLAYS = ["s3_layer_above", "s3_types_by_reach", "s3_dark_striker", "s3_over_the_choke", "s2_concave"]
HEADS = (8, 16, 24, 48)
lo, hi = int(sys.argv[1]), int(sys.argv[2])
draw = depth.lhs_draw(200, 0)
eng = Engine()
def word(build, h):
    build(h, False)
    return build.labels.get("prefight") if hasattr(build, "labels") and build.labels.get("prefight") is not None else None
out = {}
for i in range(lo, hi):
    f = draw[i]; t0 = time.time(); r = {"features": f, "seed": sweep._layout_seed(f), "plays": {}, "nb": {}}
    for p in PLAYS:
        try:
            b = sweep.default_builds(p, "play", f)
            r["plays"][p] = {h: scenes.preflight(b(h, False), eng) for h in HEADS}
        except Exception as e:
            r["plays"][p] = {h: "err:%s" % type(e).__name__ for h in HEADS}; r["err_" + p] = repr(e)[:200]
    # baselines
    try:
        b = sweep.default_builds("s3_layer_above", "naive_attacker", f)
        r["nb"]["naive_attacker"] = {h: scenes.preflight(b(h, False), eng) for h in HEADS}
    except Exception as e:
        r["nb"]["naive_attacker"] = {h: "err" for h in HEADS}
    for p in PLAYS:
        try:
            base = sweep.default_builds(p, "play", f)
            roles = sweep.baseline_roles(base(8, False))
            d = {}
            for role in roles:
                if role == "naive_attacker": continue
                b = sweep.default_builds(p, role, f)
                d[role] = {}
                for h in HEADS:
                    b(h, False); d[role][h] = b.labels.get("prefight")
            r["nb"][p] = d
        except Exception as e:
            r["nb"][p] = {"err": repr(e)[:200]}
    out[i] = r
    print(i, round(time.time() - t0, 1), {p: list(v.values()) for p, v in r["plays"].items()}, flush=True)
json.dump(out, open(sys.argv[3], "w"), indent=0, default=str)
```

Batch one's plays are the three in `sweep.PLAYS_BY_FAMILY` for vision, range_up, damage_up (A = s3_layer_above, T = s3_types_by_reach) and emitting (D = s3_dark_striker). The other two asked about are O = s3_over_the_choke and C = s2_concave. Letters per play, one per headcount 8, 16, 48: o ok, F no_fit, U unroutable, R no_reach, B blind_post. "Clean" means the play's own pre-flight is ok at 8, 16 and 48 and the naive attacker and the play's naive defender roles are ok too; blind_post on a naive defender is stricter than the sweep needs, since `sweep._usable_baselines` only drops that baseline and the play still runs. Layout feature names are the draw's; map size is not a feature, start distance is the nearest thing.

## Table: top 15 by number of batch-one plays clean (ties by all five, then index), plus 81, 78, 192

| Rank | Layout | Batch-one plays clean | All five clean | Features | Verdicts at 8/16/48 (A, T, D, O, C) | Baselines |
|---|---|---|---|---|---|---|
| 1 | 3 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 1.5, blocked-top 4, cover 0.1, start 2800 | ooo ooo ooo ooo ooo | ok |
| 2 | 4 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 1.5, blocked-top 2, cover 0.3, start 1400 | ooo ooo ooo ooo ooo | ok |
| 3 | 5 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 0, blocked-top 0, cover 0.1, start 1400 | ooo ooo ooo ooo ooo | ok |
| 4 | 13 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 1.5, blocked-top 0, cover 0, start 2800 | ooo ooo ooo ooo ooo | ok |
| 5 | 29 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 1.5, blocked-top 0, cover 0, start 2800 | ooo ooo ooo ooo ooo | ok |
| 6 | 42 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 1.5, blocked-top 4, cover 0.1, start 1400 | ooo ooo ooo ooo ooo | ok |
| 7 | 55 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 0, blocked-top 4, cover 0.3, start 2800 | ooo ooo ooo ooo ooo | ok |
| 8 | 61 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 3, blocked-top 2, cover 0.1, start 1400 | ooo ooo ooo ooo ooo | ok |
| 9 | 71 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 0, blocked-top 2, cover 0.3, start 2800 | ooo ooo ooo ooo ooo | ok |
| 10 | 82 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 0, blocked-top 4, cover 0.1, start 1400 | ooo ooo ooo ooo ooo | ok |
| 11 | 85 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 0, blocked-top 4, cover 0, start 2800 | ooo ooo ooo ooo ooo | ok |
| 12 | 107 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 0, blocked-top 4, cover 0.1, start 1400 | ooo ooo ooo ooo ooo | ok |
| 13 | 111 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 3, blocked-top 0, cover 0.3, start 1400 | ooo ooo ooo ooo ooo | ok |
| 14 | 130 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 0, blocked-top 0, cover 0, start 1400 | ooo ooo ooo ooo ooo | ok |
| 15 | 139 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 0, blocked-top 4, cover 0.1, start 1400 | ooo ooo ooo ooo ooo | ok |
| 51 | 192 | 3/3 | 4/5 | choke 8B, 0 lanes, detour 1.5, blocked-top 0, cover 0, start 2800 | ooo ooo ooo ooo FFF | ok |
| 127 | 78 | 1/3 | 1/5 | choke 4B, 1 lane, detour 1.5, blocked-top 4, cover 0, start 1400 | FFF FFF ooo FFF FFF | ok |
| 130 | 81 | 1/3 | 1/5 | choke 2B, 2 lanes, detour 0, blocked-top 4, cover 0.3, start 1400 | FFF FFF ooo FFF FFF | ok |

Counts over the 200 layouts: A and T each fit 76 layouts (the same 76), D fits 182, O fits 82, C fits 17. 57 layouts fit all three batch-one plays with every baseline clean; 17 of those also fit O and C (the top 15 above are drawn from them; 29 repeats 13, and 107 and 139 repeat 82, so they are the same map). Headcount never changes a word: every refusal is a layout property, identical at 8, 16, 24 and 48. The naive attacker is ok on all 200 layouts; the only baseline refusal anywhere is blind_post on the naive defender of A and T (19 of the 76 layouts that fit them, mostly choke 4 bodies with no lane).

What decides fit for A and T (layouts that fit / layouts drawn, by choke width and lane count): no choke, no lane 17/17; no choke, one lane 7/15; no choke, two lanes 0/18; choke 2B 7/13, 3/17, 1/20 for zero, one, two lanes; choke 4B 12/24, 0/13, 1/13; choke 8B 11/13, 13/22, 4/15. O (over the choke) fits every no-choke layout with at most one lane and every 8B layout, and no 2B or 4B layout; C fits only the 17 layouts with neither a choke nor a lane.

## Reading

1. 81 (choke 2B, 2 lanes) and 78 (choke 4B, 1 lane) are no_fit at every headcount for A, T, O and C and ok only for D, so batch one gets 1 of 3 plays on each; 192 fits all three (and O), failing only C.
2. Best replacement for 78, keeping a choke and a lane: 142 (choke 8B, 1 lane, detour 0, blocked-top 4, cover 0, start 1400) or 45 (same with detour 3); both 3 of 3 clean and O ok, C no_fit. 23 (no choke, 1 lane) is the same shape without a choke.
3. Best replacement for 81, whose narrow choke and two lanes fit nothing: no 2B or 4B layout with a lane fits cleanly. 69 (choke 8B, 2 lanes, detour 1.5, blocked-top 4, cover 0, start 1400) is the closest in shape, 3 of 3 clean, O ok; 102 (choke 2B, no lane, otherwise the same features as 81) fits A, T, D but its naive defender is blind_post for A and T, so those two lose the naive-defender baseline.
4. If the point is to fit the most plays (all five), take 82, 55 or 42 (no choke, no lane, blocked-top 4; A, T, D, O and C all ok); they give up the choke that 81 and 78 were chosen for.
5. Surprise: fit is not monotone in choke width: 8-body chokes fit A and T on 28 of 50 layouts against 11 of 50 for 2B and 13 of 50 for 4B, and lanes cut the fit sharply at every choke width.

(Alternatives checked for rows 2 and 3, same columns:)

| Rank | Layout | Batch-one plays clean | All five clean | Features | Verdicts at 8/16/48 (A, T, D, O, C) | Baselines |
|---|---|---|---|---|---|---|
| 140 | 102 | 1/3 | 1/5 | choke 2B, 0 lanes, detour 0, blocked-top 4, cover 0.3, start 1400 | ooo ooo ooo FFF FFF | blind_post on A,T |
| 20 | 23 | 3/3 | 4/5 | choke 0B, 1 lane, detour 3, blocked-top 4, cover 0, start 1400 | ooo ooo ooo ooo FFF | ok |
| 21 | 45 | 3/3 | 4/5 | choke 8B, 1 lane, detour 3, blocked-top 4, cover 0, start 1400 | ooo ooo ooo ooo FFF | ok |
| 38 | 142 | 3/3 | 4/5 | choke 8B, 1 lane, detour 0, blocked-top 4, cover 0, start 1400 | ooo ooo ooo ooo FFF | ok |
| 28 | 69 | 3/3 | 4/5 | choke 8B, 2 lanes, detour 1.5, blocked-top 4, cover 0, start 1400 | ooo ooo ooo ooo FFF | ok |
| 6 | 42 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 1.5, blocked-top 4, cover 0.1, start 1400 | ooo ooo ooo ooo ooo | ok |
| 7 | 55 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 0, blocked-top 4, cover 0.3, start 2800 | ooo ooo ooo ooo ooo | ok |
| 10 | 82 | 3/3 | 5/5 | choke 0B, 0 lanes, detour 0, blocked-top 4, cover 0.1, start 1400 | ooo ooo ooo ooo ooo | ok |
