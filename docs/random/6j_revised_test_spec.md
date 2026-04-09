# Revised 6J Test Spec — Soft RPS Behavioral Gradient

## Design Intent (from bible)

The bible does NOT say Strike should reliably beat Line with flanking. It says:

- "Line absorbs and overwhelms Strike" — this is the **default**.
- "Strike units need to avoid Line engagement, not win it" — Strike's correct play is **disengagement**.
- "A Strike wing that catches Line units **out of formation** can win" — upsets require **defender mistakes**, not just attacker positioning.
- "Positioning and abilities can overcome a bad matchup, but you're fighting uphill" — upsets are **possible**, not **expected**.
- L4 severity is "warning" and the spec itself says "the specific percentage is a tuning target, not a hard constraint."

The system is working when there's a **steep behavioral gradient** across scenario types — not when a single win-rate threshold is hit.

---

## Revised L4 Claim

**L4 (revised): Positioning creates a measurable gradient in Strike vs Line outcomes.**

The soft RPS system exhibits correct behavior when ALL of the following are true simultaneously:

| Tier | Scenario | Win Rate | TTW Ratio vs Tier 1 | What It Validates |
|------|----------|----------|---------------------|-------------------|
| T1 | Head-on, formed up | 0–5% | Baseline (1.0×) | "Line absorbs and overwhelms Strike" |
| T2 | Flank vs formed Line | 5–15% | ≥1.3× | LOS/collision geometry matters mechanically |
| T3 | Strike catches Line out of formation | 15–40% | ≥1.6× | "catches Line out of formation can win" |

**The tuning target is the gradient shape, not any single cell.**

- If T1 ≈ T2 ≈ T3 (all near 0%): positioning has no mechanical effect → geometry systems broken.
- If T1 ≈ T2 ≈ T3 (all near 30%+): Line doesn't beat Strike → RPS triangle broken.
- If T1 near 0%, T2 slightly better, T3 meaningfully better: **bible-correct behavior.**

---

## Scenario Definitions

### Tier 1 — "The bible says this is hopeless"

**T1: Head-on, formed Line** — 10v10, open field, both forces start at opposite ends, advance toward each other. Line is in tight formation (clustered spawn, ~100 wu spread). Strike approaches head-on.

This is the "dies fast in a straight fight against Line" scenario. Strike should almost never win. This is the control case.

### Tier 2 — "Geometry should help, but Line is ready"

**T2: Flank vs formed Line** — 10v10, open field or chokepoint map. Line starts in tight formation facing forward. Strike spawns 90° off-axis and approaches from the flank.

Line is formed up and at full strength — the only advantage Strike gets is the geometry (LOS blocking, arrival angles). This tests whether the collision/LOS systems create any mechanical advantage at all. Modest improvement over T1.

### Tier 3 — "Catching Line out of formation"

This is the bible's actual upset condition. It requires modeling **defender disadvantage**, not just attacker advantage. Two sub-scenarios:

**T3a: Line in march column** — Line units are strung out in a column (sequential spawn positions with ~150 wu spacing along the axis of march, not clustered). Strike attacks from the flank. This models "out of formation" — Line can't bring all units to bear simultaneously.

**T3b: Line already engaged** — Line force is mid-fight with a small Siege detachment (3 Bombards) when Strike arrives from a flank. Line has taken some damage and its formation is disrupted by the ongoing fight. This models "catches Line units out of formation" in the most literal bible sense — Line's attention and HP are split.

---

## Measurements Per Scenario (25 seeds each)

1. **Win rate** — fraction of seeds where Strike eliminates all Line units (or Line eliminates all Strike units). Report both sides.

2. **Time-to-wipe (TTW)** — ticks from first damage to last death. Report mean and stddev. The TTW ratio between tiers tells you how much positioning extends the fight — even in losses, longer fights mean Strike is dealing proportionally more damage and creating the window where a real player would retreat or reposition.

3. **Damage dealt ratio** — total damage dealt by Strike / total damage dealt by Line, averaged across seeds. Even in a loss, if Strike deals 60% as much damage when flanking vs 30% head-on, the geometry is working.

4. **Firing% asymmetry** — (Strike firing%) − (Line firing%), sampled every 50 ticks during combat. Positive means the LOS/collision system is favoring Strike's geometry. This is the direct measurement of whether the mechanical systems are doing their job.

5. **Survival time of first Strike kill** — how many ticks until the first Strike unit dies. Longer = more time for positioning to compound. Compare across tiers.

---

## Output Format

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
  TTW ratio T3/T1 >= 1.6: [PASS/FAIL]
  Win rate T1 <= 5%:       [PASS/FAIL]
  Win rate T3 > T2 > T1:   [PASS/FAIL] (monotonic increase)
  Fire% Δ T2 > T1:         [PASS/FAIL]
  Dmg ratio T3 > T2 > T1:  [PASS/FAIL] (monotonic increase)
```

---

## Pass Criteria

**L4 passes when:**
- All four gradient checks that test monotonic increase pass (TTW, win rate, fire%, damage ratio all increase from T1→T3)
- T1 win rate ≤ 5% (Line decisively beats Strike head-on)
- TTW ratio thresholds met (T2 ≥ 1.3×, T3 ≥ 1.6×)

**L4 fails (escalate) when:**
- Gradient is flat (positioning has no measurable effect)
- T1 win rate > 10% (Line doesn't reliably beat Strike — RPS triangle broken)
- Monotonic increase doesn't hold (T3 worse than T2, etc.)

The specific win-rate percentages for T2 and T3 are **observed outputs, not pass/fail thresholds** — we read them to understand the system, not to gate on them. The gradient shape is what matters.

---

## Guard Rails (unchanged)

After any config changes, still verify:
- L5: 5v5 all type permutations ≥ 10s
- L6: 100v100 mixed > 60s
- L7: 50v50 mixed mirror 45–75s
- L3: Line beats Strike >60% force retention (6C test) — head-on must still be decisive

---

## Important: No RPS-Aware Targeting

The bible (line 215) explicitly states: "No RPS-aware targeting, no priority lists — closest threat gets shot." Do not implement or suggest any targeting changes that make units prefer targets based on category. The RPS advantage comes purely from the multiplier matrix and stats. Targeting is always nearest-enemy.

---

## Implementation Notes for CC

- T3b requires spawning a small Siege detachment (3 Bombards) allied to neither side, or allied to Strike, positioned so Line engages them first. Simplest: spawn 3 Bombards at Line's 12-o'clock, Strike at Line's 3-o'clock. Line advances into Bombards, Strike arrives after ~3 seconds of Line-vs-Siege fighting. The Bombards are expendable — they exist to disrupt Line's formation and split its HP, not to contribute to Strike's win.
- T3a column spacing: 150 wu between each Line unit along their march axis. This means the last unit is ~1350 wu behind the first — Strike hitting the flank will engage front units well before rear units can close.
- All scenarios use the same 10v10 composition as existing tests (pure Strike vs pure Line) unless otherwise noted.
- T3b counts as a Strike win only if Strike eliminates all Line units, regardless of Bombard survival.
- Seed range: 1–25 for all tiers. Same seeds across tiers for paired comparison.
