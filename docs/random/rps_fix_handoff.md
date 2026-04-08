# Strike vs Siege RPS Fix — Claude Code Handoff

## Problem

Strike vs Siege is inverted (Siege wins 5/5, 88% retention). The 1.5x/0.75x multiplier is correct but Bombard AoE hitting clustered low-HP Strike units produces a blowout before Strike can deal meaningful damage. The damage system is working correctly — the damage cap config value is too generous for this matchup.

## Fix

Lower `AOE_DAMAGE_CAP_MULTIPLIER` from 4.0 to 3.0 in config.

This caps a single Bombard shot at 105 total damage (35 × 3.0) across all targets in the AoE circle, down from 140. This specifically limits the "5 Raiders stacked in one blast" blowout without changing Bombard performance against 1-2 targets or the Siege > Line matchup (Line units are fewer and larger, rarely hit the cap).

## What NOT to change

- Do not change AoE radius (150 wu). Leave it alone unless the cap change is insufficient.
- Do not change the RPS multiplier matrix (1.5x/0.75x/1.0x).
- Do not change any unit HP or DPS values.
- Do not change Bastion stats.

## Verification

Re-run the Checkpoint 6C test with the new config value. Expected results:

- **Strike > Siege:** Strike should now win majority (3/5+). Retention doesn't need to match the other favored matchups exactly — just needs to not be inverted.
- **Siege > Line:** Should remain ~100% win rate, ~90% retention. If this drops significantly, the cap change was too aggressive.
- **Line > Strike:** Should be unaffected (no AoE involved).
- **Mirror matches:** Should be unaffected or negligibly changed.

If Strike vs Siege is still inverted after the cap change, report the results and stop. Next lever would be AoE radius reduction (150 → 120), but don't apply it without showing the cap-only results first.

## Not fixing now

Engagement duration targets (45s minimum brawl, etc.) are Checkpoint D's job. Don't tune HP/DPS for duration in this pass.
