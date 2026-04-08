# 6D Fixes — Kill Attribution Bug + Spawn Formation

## Bug 1: "killed by unknown" Attribution

12 kills in the debug trace show "killed by unknown." Every kill must have a source unit. This is a bug, not a display issue.

Likely causes to check:
- AoE damage not recording the Bombard as the source when a unit dies to splash
- Simultaneous damage from multiple sources where the killing blow's source isn't tracked (unit takes damage from several attackers in the same tick, HP drops to zero, but the last-hit source isn't recorded)
- Unit dying to damage applied in the snapshot resolution step where the source reference is lost

Fix: ensure every damage application records the source unit ID. When a unit's HP reaches zero, the source of the killing blow (the last damage event that tick, or the largest contributor that tick) is stored on the death record. If multiple sources contribute in the same tick, pick the largest damage contributor. There should be zero "unknown" kills.

Verify: re-run the debug trace. Every kill line must show "killed by [faction]:[unit_type](#[id])". Zero "unknown" entries.

## Fix 2: Spawn Formation by Role

The current test spawns all units in a line/grid with no regard for combat role. This means Vanguards, Raiders, Wardens, and Bombards are interleaved, and whichever units happen to be closest to the enemy get first contact — often soft targets like Wardens or Interceptors getting caught by enemy Vanguards.

The bible defines clear unit roles:
- **Vanguard** — "the wall." Frontline. Should be closest to the enemy.
- **Warden** — support aura. Should be just behind Vanguards, within aura range.
- **Raider/Interceptor** — Strike. Fast flankers/screens. Should be on the wings or behind the line, not in front of the Vanguards.
- **Bombard** — long range fire support. Should be behind the line, within attack range (600 wu) of the front.
- **Bastion** — anchor. Behind the line or mixed with Vanguards.

Update the test spawn layout for mixed-composition scenarios (50v50, 100v100) to use role-based positioning:

```
Enemy side
─────────────────────────────────
        [ Vanguard line ]           <- closest to enemy, ~200 wu apart
     [ Warden ]   [ Warden ]       <- behind Vanguards, within aura radius
  [ Raider ] [ Interceptor ]       <- wings or behind
     [ Bombard ]  [ Bombard ]      <- behind line, within 600 wu range
        [ Bastion ]                 <- rear anchor
─────────────────────────────────
Player side
```

Exact positions don't need to be pixel-perfect — just ensure:
1. Vanguards are the front row (closest to enemy spawn)
2. Wardens are within aura radius of Vanguards (behind, not in front)
3. Strike units are on flanks or second row
4. Siege units are rear, within their attack range of the expected engagement zone
5. Both sides use the same formation (mirrored), so neither side has a layout advantage

This won't eliminate the snowball — first blood will still compound — but it ensures the snowball starts from the intended interaction (Vanguard vs Vanguard trading) rather than a Vanguard catching an out-of-position Warden.

## Re-run

After both fixes, re-run test_6d_debug.py (50v50 mirror, seed 1, per-tick diagnostics). Expected changes:
- Zero "killed by unknown"
- Early kills should be Vanguard-on-Vanguard, not Vanguard sniping soft targets
- Snowball may still occur but should be slower to develop (Vanguards have 1200 HP, take longer to kill than the 375 HP Interceptors that were dying first before)
- Winner's survivor count should be lower (closer fight)
