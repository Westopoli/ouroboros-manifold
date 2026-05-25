# leaf-07 Assumption Log

## A1 — Cluster geometry: hand-built vs place_asteroid_fields

Used hand-built asteroid grid, NOT `gradient_placer.place_asteroid_fields`.

Reasons:
- `place_asteroid_fields` needs `InstantiatedLayout` object + config constants for density/scale distribution; creates overhead and indirection for a fixed integration fixture.
- Random placement gives no determinism guarantee that every run covers the attacker→defender line; test opacity requirement demands determinism.
- Brief explicitly permits either approach ("call place_asteroid_fields … OR hand-build asteroids").

Grid: center (500,500), radius 80, step = radius_xy × 1.8 = 27wu. Produces exactly 25 asteroids (verified empirically). Slight overlap ensures no ray gaps through interior.

## A2 — Asteroid dimensions

`radius_xy=15`, `height=300`, `scale_class="huge"`.

- radius_xy=15 with step_factor=1.8 yields exactly 25 asteroids in cluster — matches spec "~25 asteroids skewed huge".
- height=300 >> all LAYER_Z_CEILINGS (max ~300) → blocks all layers; no edge-case with z-range check.
- scale_class="huge" per spec "skewed huge".

## A3 — Attacker positions: deviation from brief

Brief says (50,500) and (50,600). These are geometrically impossible for assertion 3.

Geometry: ray from (50,600) to (900,500) at x=500: y=600−100×(450/850)≈547. Distance from (500,500)=47wu < cluster radius 80 → ray hits cluster → defender at (900,500) still hidden. Same for (50,500)→(900,500) (y=500, passes through cluster center, distance=0).

Used (50,100) and (50,900) instead:
- Ray from (50,100)→(500,500): hits cluster center → BLOCKED ✓
- Ray from (50,900)→(500,500): hits cluster center → BLOCKED ✓
- Ray from (50,100)→(900,500): at x=500, y≈312. Distance from (500,500)=188wu > 80 → CLEAR ✓
- Ray from (50,900)→(900,500): at x=500, y≈688. Distance from (500,500)=188wu > 80 → CLEAR ✓

Positions honor spec INTENT (two attackers blocked by cluster; defender visible in open) even if not exact coordinates.

## A4 — Store API

Used `UnitStore.spawn(unit_type, faction_id, x, y, layer=0, stats=dict)` with explicit stats dicts (not config.UNIT_STATS lookup). This gives fixture independence from config changes.

`auto_engage_target` is `store.auto_engage_target[uid]` — int32 numpy array initialized to -1. Set directly in test for assertion 2 (attackers→defender) and assertion 4 (defender→attacker).

## A5 — FIELD_* constants source

All FIELD_* constants imported from `unit.py` per contract_imports. No `store.py` module — umbrella test has a bug (`from store import ...`) but that's parent-owned; not our concern. Our test imports from `unit`.

## A6 — resolve_damage dt parameter

Used `dt=2.0` for assertions 2 and 3 to ensure `FIELD_ATTACK_TIMER` fires (timer initialized to 0, so any dt > 0 triggers). `attack_interval=0.8` for Raider means after resolve_damage with dt=2.0, timer fires and resets to 0.8 — damage applied on first call if timer <= 0.

## A7 — Asymmetry assertion (test 4)

Spec line 49 says "no fire-reveal". The defender's own `compute_visibility` does NOT reveal attackers because:
- Cluster blocks ray from defender (500,500) to attackers at (50,100) and (50,900) — verified in geometry check (A3 symmetric rows confirm defender→attacker also blocked).
- Setting `auto_engage_target` on defender does NOT change fog-of-war computation; visibility is purely geometric.

Test asserts attacker NOT in defender's vis set; this is actually the same cluster-blocking mechanism from defender's POV, not a separate "fire-reveal" flag.

## A8 — No third file needed

Fixture + test are two files only. No helpers, no config patches, no new modules. Clean.
