# leaf-06 AUDIT — AI cover-peek clumping check

## Setup
- TacticalMap 2000x2000, no gradient sources, no spine nodes, no obstacles.
- 1 CoverPolygon (id=1), 12-vertex circle, center (500,500), radius 80.
- Defender: Warden, faction 1, position (500,500) — inside polygon. Attack range 350, sensor 800, attack_interval 1.5s (30 ticks).
- Attacker: Raider, faction 0, position (200,500) — outside polygon. Distance 300.
- No behavior_runners attached. Base `tactical_engine.TacticalEngine.step()` loop only.
- Seed 42.

## Run
60 ticks via `engine.step()`.

## Observations
| tick | defender target | attacker HP | defender pos |
|------|-----------------|-------------|--------------|
| 1    | -1              | 250.0       | (500,500)    |
| 6    | 1 (attacker)    | 244.0       | (500,500)    |
| 11   | 1               | 244.0       | (500,500)    |
| 30   | 1               | 244.0       | (500,500)    |
| 60   | 1               | 238.0       | (500,500)    |

Defender fired at least twice (HP 250 -> 244 -> 238, Warden Line vs Raider Strike multiplier 1.5 -> 6 dmg/shot, 6 dmg per attack_interval matches). Defender never moved. Defender never left cover polygon.

L5 visibility gate let damage through: defender saw attacker (attacker not in any polygon -> no symmetric-blind). Attacker saw nothing (defender in poly 1, attacker_polygon None != 1 -> blind), so attacker took damage with no return damage.

## Result
**No clumping pathology.** Defender naturally engages a visible attacker from cover through the existing targeting loop (`update_targeting` in `tactical_engine.py` -> `auto_engage_target` set -> `resolve_damage` visibility check passes). Phase B fix NOT required.

## Phase B
Skipped. No edits to `simulation/tactical_engine.py`.

## Test outcome
`simulation/test_cover_ai_peek.py` written as asserting-no-clumping. 4 tests pass.
