# CC Paste: Revised 6J Test — Behavioral Gradient

## Context

The old L4 (">30% Strike wins with flanking") doesn't match the bible. The bible says "Strike units need to avoid Line engagement, not win it" and upsets only happen when Line is "out of formation." We're replacing the single win-rate target with a **gradient test across scenario tiers**.

## What to build: `test_6j_gradient.py`

Replaces `test_6j_matrix.py` and `test_6j_tuning.py` as the primary 6J validation tool.

### Four scenarios, 25 seeds each, same seeds across all tiers:

**T1 — Head-on formed:** 10v10 open field, both sides advance toward each other, Line in tight formation (~100 wu cluster spawn). Control case.

**T2 — Flank vs formed:** 10v10, Line in tight formation facing forward, Strike spawns 90° off-axis. Line is formed up — Strike's only advantage is geometry.

**T3a — Flank vs march column:** 10v10, Line units strung out in column (150 wu spacing between each unit along march axis). Strike attacks from 90° flank.

**T3b — Flank vs already-engaged:** 10v10 Strike vs 10 Line, PLUS 3 Bombards positioned at Line's 12-o'clock. Line advances into Bombards first. Strike arrives from Line's 3-o'clock after ~3 sec delay (60 ticks). Strike win = all Line dead, Bombard survival irrelevant.

### Measurements per scenario (all averaged across 25 seeds):

1. Strike win rate (fraction)
2. TTW — ticks from first damage to last death, mean ± stddev
3. Damage dealt ratio — total Strike damage / total Line damage
4. Firing% asymmetry — (Strike firing%) − (Line firing%), sampled every 50 ticks
5. First Strike kill tick — ticks until first Strike unit dies

### Output format:

```
============================================================
6J BEHAVIORAL GRADIENT — Strike vs Line, 25 seeds per tier
============================================================

Tier  Scenario              Strike Wins  TTW(mean±std)  TTW Ratio  Dmg Ratio  Fire% Δ  1st Kill(ticks)
----  --------------------  -----------  -------------  ---------  ---------  -------  ---------------
T1    Head-on formed        X/25         XXXX ± XXX     1.00×      0.XX       +X.X%    XXX
T2    Flank vs formed       X/25         XXXX ± XXX     X.XX×      0.XX       +X.X%    XXX
T3a   Flank vs column       X/25         XXXX ± XXX     X.XX×      0.XX       +X.X%    XXX
T3b   Flank vs engaged      X/25         XXXX ± XXX     X.XX×      0.XX       +X.X%    XXX

GRADIENT CHECK:
  TTW ratio T2/T1 >= 1.3: [PASS/FAIL]
  TTW ratio T3/T1 >= 1.6: [PASS/FAIL]  (use higher of T3a, T3b)
  Win rate T1 <= 5%:       [PASS/FAIL]
  Win rate T3 > T2 > T1:   [PASS/FAIL] (monotonic)
  Fire% Δ T2 > T1:         [PASS/FAIL]
  Dmg ratio T3 > T2 > T1:  [PASS/FAIL] (monotonic)
```

### Pass criteria:

- All six gradient checks pass
- Specific T2/T3 win-rate numbers are observed, not gated on

### Critical constraint:

**No RPS-aware targeting.** Bible says "closest threat gets shot." Do not add any category-based target selection. The gradient must emerge from geometry + stats + multipliers only.

### After the gradient test runs:

- If gradient is flat → geometry systems aren't producing enough effect, investigate collision/LOS tuning (radius, iterations)
- If gradient is steep but T1 > 5% → RPS triangle is too soft, HP gap or multiplier needs widening
- If gradient looks correct → proceed with CC's Phase 1 HP changes, then re-run gradient test + 6D/6C regression
