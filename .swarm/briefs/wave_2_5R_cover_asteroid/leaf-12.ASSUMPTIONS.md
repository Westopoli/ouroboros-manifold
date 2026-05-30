# leaf-12 Assumption Log

## Execution method
Chose method (A): working-copy-in-staging. Staged damage.py + test file both in `.swarm/pending/leaf-12/simulation/`. Real simulation/ files untouched throughout. Pytest run from staged dir.

## Import isolation discovery
`sys.path.insert(0, staged_dir)` insufficient — pytest rootdir discovery inserts real `simulation/` into sys.path before test module loads, winning priority. Resolution: `importlib.util.spec_from_file_location("damage", staged_path)` + `module_from_spec` + `exec_module` to force explicit staged load regardless of sys.path order. Registered in sys.modules["damage"] so all test references resolve to staged version.

## Exact HEAD line numbers verified
- `_accumulate_single` cover block: lines 132-136 (HEAD). Confirmed: `cover = 0.0`, conditional assignment, `dmg = base_dmg * mult * (1.0 - cover)`.
- `_accumulate_aoe` cover block: lines 171-175 (HEAD). Same pattern.
- `resolve_damage`: lines 13-67. `navmesh = _ensure_navmesh(...)` at line 15. Visibility gate inserted after navmesh line, before attack_range check exit, before has_combat_los block.
- `update_targeting`: line 191 (HEAD). `cohort_this_tick` at line 194. `if not found_atk:` block at lines 251-274. Sensor-pursuit loop inner body at lines 263-268. `if best_uid >= 0:` block at lines 271-274.

## Edit 4 placement decision
Brief says "after attack_range distance check (around HEAD line 33-34)". Placed visibility gate AFTER `if dist > attack_range: continue` and BEFORE `if navmesh is not None and navmesh.has_obstacles:` check. This matches brief order: "Place BEFORE the has_combat_los navmesh check."

## Edit 5(c) behavior inference
Brief says: `pre_acquisition = int(store.auto_engage_target[uid])` then `if pre_acquisition < 0: store.auto_engage_target[uid] = -1`. When `pre_acquisition >= 0` (player-locked target), the assignment is skipped — target preserved. This handles the "player-issued target preserved when hidden" case. `attack_moving=False` means sensor-pursuit block never runs, so only the 5(c) guard matters for that test.

## Edit 5(d) — sensor-pursuit LOS gate
`uid_visible = visibility_map.get(uid, set())` placed before the `for other in tmap.spatial_hash.query(...)` loop. `if other not in uid_visible: continue` placed after faction/layer checks inside the loop (order: faction → layer → LOS gate → distance). Matches brief "after faction/layer checks".

## Edit 5(e) — auto_engage_target lock assignment
`store.auto_engage_target[uid] = best_uid` placed immediately before existing `store.set_move_target(...)` call. Gives attacker target-lock on next tick when in attack_range. Pre-authorized per brief.

## TARGETING_COHORT_COUNT = 4
Confirmed in config.py line 592. Cohort helper runs `TARGETING_COHORT_COUNT * n` calls. Used `n=2` (8 calls) to ensure attacker's cohort slot fires at least twice. Attacker uid=0, target uid=1; `uid % 4 == 0` so cohort_this_tick must equal 0. With global `_targeting_tick`, first cohort slot fires on tick 4, 8, etc. 8 calls guarantees ≥2 hits.

## _targeting_tick is global
Global state persists across test instances in same pytest session. Covered by running cohort `n=2` (8 calls) to ensure multiple cohort cycles complete regardless of where `_targeting_tick` starts.

## test_no_asteroid_target_acquired — target at 400,500
Distance attacker(200,500)→target(400,500) = 200wu. attack_range=50 (not in range). sensor_radius=500 (in sensor range). With no asteroid, compute_visibility grants mutual visibility; uid_visible contains target. Sensor pursuit acquires → auto_engage_target set to target uid.

## test_player_issued_target_preserved — attack_moving=False
`attack_moving=False` means `if store.attack_moving[uid]:` block never runs. Only Edit 5(c) path matters: `pre_acquisition = int(target) >= 0` → assignment skipped → target preserved at `auto_engage_target[attacker] = target`. No sensor-pursuit overwrite possible.

## Regex test uses both `-` and `\u2212` (unicode minus)
Covers both ASCII hyphen-minus and Unicode minus sign in source text. Source uses ASCII only; match would be `(1.0 - cover`. After edits, zero occurrences in staged damage.py.

## Files not touched
movement.py, config.py, tactical_map.py, fog_of_war.py, all do_not_edit list files. Confirmed by empty `git diff HEAD simulation/damage.py`.
