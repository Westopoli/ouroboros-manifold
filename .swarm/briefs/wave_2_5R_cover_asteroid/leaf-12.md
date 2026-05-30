---
leaf_id: leaf-12
spec_file: docs/test_specs/cover_asteroid_movement_spec.md
spec_lines: 46-52
test_file: simulation/test_asteroid_damage_and_targeting_gate.py
impl_file: simulation/damage.py
contract_imports:
  - tactical_map.TacticalMap
  - tactical_map.Asteroid
  - tactical_map.AsteroidField
  - fog_of_war.compute_visibility
  - damage.update_targeting
do_not_edit:
  - simulation/movement.py
  - simulation/config.py
  - simulation/test_asteroid_movement.py
  - simulation/test_asteroid_ai_los_gate.py
  - simulation/tactical_map.py
  - simulation/fog_of_war.py
  - simulation/gradient_placer.py
  - simulation/snapshot_serializer.py
  - simulation/tactical_engine.py
  - simulation/tick.py
  - simulation/drift.py
  - simulation/faction.py
  - simulation/region.py
  - simulation/events.py
  - simulation/event_engine.py
  - simulation/intent_resolver.py
  - simulation/border_friction.py
  - simulation/technology.py
  - simulation/diplomacy.py
  - simulation/world.py
  - simulation/templates.py
  - simulation/theme_scifi.py
  - simulation/test_asteroid_damage_gate.py
  - scenes/**
  - autoload/**
  - docs/bible/**
  - docs/test_specs/cover_asteroid_los_spec.md
  - docs/test_specs/cover_asteroid_movement_spec.md
  - docs/test_specs/cover_los_rework_spec.md
  - simulation/test_asteroid_umbrella.py
  - simulation/test_cover_umbrella.py
impl_line_budget: 100
test_assertion_budget: 18
wave: 4
---

## Task

Consolidated leaf: lands Wave 2.5R damage gate that L5 falsely reported clean PLUS Wave 2.6M AI targeting LOS gate. Single file: `simulation/damage.py`. Five concrete edits below — every one is pre-authorized; do NOT escalate any of them as scope expansion. If unrelated edits seem necessary, STOP and report.

**Edit 1** — Add import: `from fog_of_war import compute_visibility` at top of `damage.py` alongside other imports.

**Edit 2** — `_accumulate_single` (around lines 132-136 of HEAD damage.py): remove the three lines computing `cover` from `tactical_map.cover_density(...)` and remove `* (1.0 - cover)` from the `dmg = base_dmg * mult * (1.0 - cover)` line. Final form: `dmg = base_dmg * mult`. Per cover_asteroid_los_spec.md lines 162-166 (cover_density mult retired from damage path; visibility gate replaces it).

**Edit 3** — `_accumulate_aoe` (around lines 171-175 of HEAD damage.py): same three-line `cover` removal + `* (1.0 - cover)` strip. Final form: `dmg = base_dmg * mult`.

**Edit 4** — `resolve_damage`: after `compute_visibility(store, tactical_map)` is called once at top of function (add it after `navmesh = _ensure_navmesh(...)` line, store as `visibility`), then inside the per-attacker loop, after the `attack_range` distance check (around HEAD line 33-34), add: `if target not in visibility.get(uid, ()): continue`. This skips damage when target is hidden behind asteroid per spec section C line 51 (mid-engagement target loss handled by visibility gate). Place BEFORE the `has_combat_los` navmesh check.

**Edit 5** — `update_targeting`:
  (a) Signature: change `def update_targeting(store: UnitStore, tmap, rng=None)` to `def update_targeting(store: UnitStore, tmap, rng=None, dt=None)`. AUTHORIZED — `dt=None` default is backwards-compat for all existing call sites. Do not change other params.
  (b) After `cohort_this_tick` line, add: `visibility_map = compute_visibility(store, tmap)`.
  (c) In the `if not found_atk:` block (around HEAD line 252), replace the unconditional `store.auto_engage_target[uid] = -1` line with:
```python
pre_acquisition = int(store.auto_engage_target[uid])
if pre_acquisition < 0:
    store.auto_engage_target[uid] = -1
```
  This preserves player-issued or prior-AI-locked target. Per spec line 50: player intent respected.
  (d) Inside the `if store.attack_moving[uid]:` sensor-pursuit loop (around HEAD line 263-279), capture `uid_visible = visibility_map.get(uid, set())` before the `for other in tmap.spatial_hash.query(...):` line. Inside the loop, after faction/layer checks, add: `if other not in uid_visible: continue` as LOS gate.
  (e) When `best_uid >= 0` (around HEAD line 280-284), AUTHORIZED NEW BEHAVIOR: add `store.auto_engage_target[uid] = best_uid` before the existing `store.set_move_target(uid, ...)` call. This gives the attacker a target lock the moment a visible enemy enters sensor range, so the attack timer + firing path engages on the next tick when in attack_range. Pre-existing behavior set move_target only; consolidated leaf authorizes the lock-assignment per Westley 2026-05-23.

**Tests** (write RED first in `simulation/test_asteroid_damage_and_targeting_gate.py`):
- `resolve_damage`: huge asteroid blocks LOS attacker→target; attacker has target in auto_engage_target; `resolve_damage(store, tm, dt=1.0)` called; target HP unchanged.
- `resolve_damage`: no asteroid; same fixture; HP decreased.
- `_accumulate_single`: regex sweep — `re.search(r"\(1\.0?\s*[-−]\s*cover", open(damage.__file__).read())` returns None.
- `_accumulate_single`: pre/post damage equal across "with cover_density" vs "without" tactical_map fixtures (cover mult truly gone).
- `_accumulate_aoe`: same regex + behavioral parity.
- `update_targeting` LOS gate: huge asteroid hidden target + sensor-pursuit fixture (attacker attack_range=50, sensor_radius=500, attack_moving=True) → `auto_engage_target[attacker] == -1` after `update_targeting` runs through full cohort cycle.
- `update_targeting` no asteroid: same fixture → `auto_engage_target[attacker] == target` (new assignment behavior).
- `update_targeting` target steps into open between calls → second call acquires (`auto_engage_target` switches -1 → target).
- `update_targeting` player-issued target preserved when hidden: set `auto_engage_target[attacker] = target` manually, run `update_targeting`, assert still `== target`.
- `update_targeting` signature: callable as `update_targeting(store, tm)` (no dt) AND `update_targeting(store, tm, dt=0.1)`.

Use minimal `TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])` + `UnitStore()` + hand-built `AsteroidField` fixtures. Tests may need to call `update_targeting` `TARGETING_COHORT_COUNT` times per logical tick (cohort system). Acceptable helper.

## Acceptance

Run `cd simulation && python3 -m pytest test_asteroid_damage_and_targeting_gate.py -v`. Confirm RED. Implement in `simulation/damage.py` ONLY (test file is yours; impl is single file). Confirm GREEN.

**HARD RULE — STAGING ONLY, NO REAL-PATH WRITES:**

Write your final `test_file` and `impl_file` ONLY to `.swarm/pending/leaf-12/` mirroring repo paths:
- `.swarm/pending/leaf-12/simulation/test_asteroid_damage_and_targeting_gate.py`
- `.swarm/pending/leaf-12/simulation/damage.py`

Do NOT use the Write or Edit tool on the real paths `simulation/damage.py` or `simulation/test_asteroid_damage_and_targeting_gate.py`. The previous leaf (L11) bypassed staging by writing to real paths; that violation caused a full revert + redispatch (this leaf). If you must run pytest against a working copy, place the working copy inside `.swarm/pending/leaf-12/simulation/` and import it from there, OR temporarily edit real paths to run pytest then restore via `git show HEAD:simulation/damage.py > simulation/damage.py` before staging final outputs. The final staged version in `.swarm/pending/leaf-12/` is the authoritative deliverable. Parent runs /swarm-merge.

After staging, run pytest against the staged file path explicitly to confirm GREEN: `cd .swarm/pending/leaf-12/simulation && python3 -m pytest test_asteroid_damage_and_targeting_gate.py -v` (you may need sys.path setup). Or use the temp-restore method above.

Stop after staging.

## Escalation triggers

Stop and report to the parent if:
- A type the test imports is not in contract_imports.
- The impl would need to create a new file other than the staged test file.
- The impl would need to edit any file in do_not_edit.
- Any of the 5 listed edits cannot be applied as specified (line numbers in HEAD damage.py drifted, structure differs).
- `update_targeting` test cohort wrapper requires changing `TARGETING_COHORT_COUNT` config or other globals.
- Two assertions seem to require contradictory behavior.
- Impl approaches impl_line_budget with assertions still failing.

## Assumption log

Log every inference (exact line numbers in HEAD damage.py, cohort wrapper helper details, sys.path / staged-pytest invocation choice, any other inference) to `.swarm/briefs/wave_2_5R_cover_asteroid/leaf-12.ASSUMPTIONS.md`.
