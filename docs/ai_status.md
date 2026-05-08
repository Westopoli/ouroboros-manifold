# AI Status Board

Shared coordination file for parallel Claude Code sessions working on the launch push. Up to **four concurrent sessions** are expected:

- **Stage 11g (C2)** — world view / chronicle / faction palette work
- **Track A** — sim balance, headless tuning (`docs/launch_tracks/track_a_sim_and_balance.md`)
- **Track B** — tactical mechanics & combat polish (`docs/launch_tracks/track_b_tactical_mechanics.md`)
- **Track C** — Stage 13 friends-ZIP packaging (`docs/launch_tracks/track_c_stage_13_packaging.md`)

A fifth seat — the **overlord** (Opus, summoned by Westley on demand) — mediates cross-track conflicts and escalations. It is not always running.

---

## Rules

1. **Read before pull.** First action in any session: `git pull`, then read this file end-to-end before claiming work or editing any file. The state here changes between every commit from any of the four sessions.

2. **Claim before edit.** Every code change requires a claim under "Active Claims." Commit and push the claim *before* editing code. The claim is the lock — if it isn't on `origin`, you don't hold it.

3. **One active claim per session.** Finish, release (move to "Completed"), then claim the next item. Don't hold claims you aren't actively working — others may be waiting on the file.

4. **Touch only your scope.** Each track doc has a "Scope (out)" table. Honor it. If a fix seems to require a file outside your scope, escalate; do not edit.

5. **Don't edit other sessions' lines.** You may edit only:
   - Your own claim line under Active Claims.
   - Append-only sections (Cross-Track Signals, Escalations, Completed).
   Never modify or delete another session's claim, signal, or escalation. If a signal directed at you is resolved, *you* mark it `[resolved YYYY-MM-DD]` inline — don't delete it.

6. **Status values for your own claim:**
   - `claimed` — actively working
   - `ready-for-confirm` — code done, waiting on Westley to verify visually or run checklist
   - `blocked` — cannot proceed; blocker note required
   - When done: move the line to "Completed" with date and one-line summary.

7. **Cross-Track Signals are append-only.** Format below. Anyone may post; only the addressee marks resolved. Never edit or delete another session's signal.

8. **Escalations are append-only and stop work.** When you escalate, you stop on that claim. Do not retry, do not pivot to "fix it differently," do not pick up another claim in the same area until Westley or the overlord responds. Escalation is the end of your turn.

9. **Shared-file protocol.** These files are touched by more than one track:
   - `project.godot` — `[autoload]` is C2's, `[application]` is Track C's. Different blocks merge cleanly, but post a Cross-Track Signal *before* editing the file so others know to pull.
   - `docs/launch_todo.md` — append-only completion edits; small surface, but post a signal before editing if your edit is more than a one-liner.
   - `simulation/pipe_transport.py` — flagged by both A and C. Coordinate via signal before any edit.
   - `build/pyinstaller_spec.py` — Track C owns; Track A appends to `hiddenimports` reactively only when C signals.
   - This file (`ai_status.md`) — claim and signal edits only; structural changes go through the overlord/Westley.

10. **Branch discipline.** Each track owns its own branch (named in your session's brief). Push frequently. Merges to the shared launch branch happen at Westley's call, not autonomously. Never `git checkout/restore/stash` without confirming the working tree state with Westley first.

11. **Escalation triggers (broader than the track docs' STOP lists).** Escalate immediately on any of:
    - A test fails after a change you made.
    - A test that previously passed now fails (even if you didn't change related code — `git pull` may have).
    - The track doc's "STOP-and-escalate" conditions trigger.
    - Output looks "off" but you're not sure why.
    - You'd need to widen an invariant, loosen a tolerance, or skip a test case the test was meant to catch.
    - You'd need to edit a file outside your scope.
    - Two checkpoints in the track doc seem to conflict.
    - Anything not explicitly covered by your track doc.

12. **The overlord is not always watching.** Westley relays escalations to the overlord when needed. Don't wait silently — when you escalate, **post the escalation here AND tell Westley in chat**. Then stop.

---

## Active Claims

- [ ] Improve chronicle text output — **claimed by: Opus session (rotation/chronicle)** — `claimed` — implementing 6-step plan: prose event names, region grounding, faction-attributed deltas, word-echo prevention, overlap dedup, fragment trimming. *(Track A's A5 should defer until this is released.)*

- [ ] Stage 11.5 / 11g — World View 3D Territory Visualization — **claimed by: Opus session (world view) [aka C2]** — `claimed` — actively iterating checkpoints. Tracks B and C must respect C2's scope (see track docs).

- [ ] Track B / B3 — Control groups swapping bug — **claimed by: Track B (tactical)** — `claimed` — `Ctrl+1..0` should assign selected units to a group (replacing prior membership); `1..0` should select that group; once in group N a unit stays there until reassigned. Currently units swap groups unexpectedly.
  - **Files expected to edit:** `scenes/tactical/input_router.gd` (control-group state + key handling). Read-only audit first to localize the bug before any edit.
  - **Files NOT touched:** `simulation/**`, `scenes/world/**`, `scenes/shared/world_view/**`, all `autoload/*`, `project.godot`, `scenes/privacy_modal/**`. No shared-list edits planned.
  - **Test plan:** add a headless input-router test under `tests/` (synthesize InputEventKey events, assert `_control_groups` and `selected_uids` state). Will not modify any existing test file per "no test file modification" rule.
  - **Possible interaction with B4:** B4 introduces `1..0` as auto unit-type-category selectors. Track doc explicitly orders B3 before B4 to resolve the conflict. Not picking up B4 until B3 is confirmed.

- [ ] Stage 13 — Friends-ZIP packaging (C1–C8) — **claimed by: Track C (packaging)** — `claimed` — Stage 13 spec implementer. Currently on C1 (PyInstaller sim bundle); see Escalations re: macOS host. Files this track will touch across the full spec:
  - **Track C owns (no coordination needed):** `build/pyinstaller_spec.py`, `build/build_zip.py`, `build/README.txt`, `build/feedback.txt`; new `scenes/privacy_modal/privacy_modal.tscn` + `.gd`; new `autoload/debug_overlay.gd`; `autoload/theme_constants.gd` (`IS_RELEASE_BUILD` → `OS.has_feature("release_build")`); `scenes/settings/settings.gd` (additive version label).
  - **Shared — will post a Cross-Track Signal before each edit:**
    - `project.godot` `[application]` block only (custom user dir, main scene). `[autoload]` block is C2's — if Checkpoint D needs `debug_overlay` registered as autoload, will signal C2 first per track doc.
    - `autoload/sim_bridge.gd` — release-mode `SIM_EXECUTABLE_PATH` + `--root` spawn args (Checkpoint B). Heads-up to the rotation session that already touched line 35 (`SIM_UNITS_PER_SIDE`).
    - `build/pyinstaller_spec.py` `hiddenimports` — Track C owns the file; Track A appends reactively when Track C signals a missing module per rule 9.
    - `simulation/pipe_transport.py` — starter commit's `--root` argparse already landed; no further sim changes planned. If anything is needed, will signal Track A first.
  - **Held items (will not pick up until C2 signals Stage 11g done):** 11G pause menu (new scene + `SceneRouter` touch); 11C1 connection line styling in `scenes/shared/world_view/renderers/shell_renderer.gd`. Slot in after C6, before C7.

- [ ] Track A / A1 — Force allocation scale tuning — **claimed by: Track A (sim-balance)** — `claimed` — sim_tuner sweep over `BUDGET_TO_POWER_SCALE` and `MILITARY_TO_POWER_SCALE` in `simulation/config.py:705-706`; pick values that hit bible engagement targets (min brawl 45 s, tactical ~2 min, 50v50 mirror 150–200 s) without breaking force-composition invariants. Files this track will touch across the full Track A spec (A1 → A3):
  - **Track A owns (no coordination needed):** `simulation/config.py` (A1 scale values; A2 per-unit stats only if A1 sweep surfaces a dominator/evaporator and Westley OKs the diagnosis).
  - **Read-only references (no edits unless audit demands and Westley OKs):** `simulation/force_allocator.py`, `simulation/force_composition.py`, `simulation/power_rating.py`, `simulation/sim_tuner.py` (invoke as harness; edit only if a new sweep dimension is needed), all `simulation/test_*.py` (per "no test file modification" rule — run only).
  - **Shared — will post a Cross-Track Signal before each edit:**
    - `docs/launch_todo.md` — one-liner completion mark when A1 lands. Per rule 9 a signal isn't required for a one-liner, but will post one anyway since Track C may also be appending here.
    - `build/pyinstaller_spec.py` `hiddenimports` (A3 reactive) — Track C owns; will append only after a `[track-c] → [track-a]` signal naming the missing module, then signal back resolved.
    - `simulation/pipe_transport.py` — Track C also flagged. No edits planned; if A1/A2 forces one, will signal Track C first.
  - **Cross-track heads-up planned for when A1 lands (not posted yet — values not chosen):** `[track-a] → [track-b]: BUDGET_TO_POWER_SCALE / MILITARY_TO_POWER_SCALE landed at <X>/<Y> at commit <sha> — pin B's visual confirms to that sha if unit counts matter.` Same heads-up to C2 if mission unit counts change rendering load expectations.
  - **Files NOT touched:** all protected engine files per `CLAUDE.md` (`tick.py`, `drift.py`, `faction.py`, `region.py`, `events.py`, `event_engine.py`, `intent_resolver.py`, `border_friction.py`, `technology.py`, `diplomacy.py`, `world.py`, `templates.py`, `theme_scifi.py`); `simulation/socket_server.py`; `simulation/tactical_engine.py`, `facing.py`, `damage.py`; `simulation/world_view/**` (C2); `simulation/chronicle_assembler.py`, `chronicle_distiller.py`, `events.py`, `library/chronicle/fragments.json` (rotation/chronicle session — A5 deferred per track doc); anything outside `simulation/` and `build/`.
  - **A4 (library name regen):** out-of-scope, not picking up.
  - **A5 (chronicle output polish):** deferred while rotation/chronicle session holds the claim.
  - **STOP triggers (will escalate, not solve):** any test fails, 50v50 mirror invariant fails, bible targets unattainable with reasonable scale values, or any need to widen an invariant / loosen a tolerance.

---

## Cross-Track Signals (append-only)

Format: `- YYYY-MM-DD [from-track] → [to-track]: message`
Resolution: addressee appends ` [resolved YYYY-MM-DD]` inline; never delete.

*(none yet)*

---

## Escalations to Overlord / Westley (append-only)

Format: `- YYYY-MM-DD [track]: <blocker> — tried: <what> — hypothesis: <best guess> — files touched: <list>`
After escalating, stop work on this claim.

- 2026-05-08 [track-c]: C1 needs a Windows host for the PyInstaller `.exe` build — this machine is darwin (macOS) and PyInstaller cannot cross-compile to a Windows binary. Per track doc note for Checkpoint A, the plan is: (a) draft `build/pyinstaller_spec.py` with the entry point and an initial `hiddenimports` list, (b) optionally run a Linux PyInstaller pass to validate that import list against the frozen sim, (c) stop and let Westley iterate the actual `ouroboros_sim.exe` build on a Windows machine. Confirming this plan before writing the spec. — tried: nothing yet (escalating before code per rule 12 / track doc "DO NOT TRY TO SOLVE PROBLEMS YOURSELF") — hypothesis: Westley owns the Windows iteration loop; Track C produces the spec + the rest of the host-agnostic build pipeline (`build_zip.py`, `README.txt`, `feedback.txt`) — files touched: none yet.

---

## Standing Notes (informational, not a queue)

- **SIM_UNITS_PER_SIDE changed from 1 → 10** in `autoload/sim_bridge.gd:35` by rotation session. Needed 10v10 to properly test facing. Affects unit counts in briefing data. Revert to desired value when rotation work is closed if needed.

- **Chronicle text improvement plan** (rotation/chronicle session) — purely Python-side text pipeline changes. Does NOT touch Godot files, scroll UI, or world view rendering. Files being modified:
  - `simulation/events.py` — adding `chronicle_prose` string field to each TEMPLATES entry (no behavioral changes)
  - `simulation/chronicle_assembler.py` — region grounding, word-echo prevention, faction-attributed deltas
  - `simulation/chronicle_distiller.py` — cross-entry overlap dedup
  - `simulation/library/chronicle/fragments.json` — trimming verbose fragments
  - World view session does not modify the `ScrollEntry` dataclass shape.

---

## Completed

- 2026-05-08 [track-b] B1 — Unit rotation: closed as already-working. Sim-side facing tests (`simulation/test_facing_convergence.py`, `simulation/test_facing_snapshot_propagation.py`) pass clean (5/5 + 9/9). Westley confirmed rotation is visible in playthrough. Prior `Opus session (rotation/visuals)` claim was stale and is removed; closing per Westley's permission.
- 2026-05-08 [track-b] B2 — Squad-member impact origins: confirmed by Westley. Added public `UnitRenderer.get_squad_world_position(uid, squad_idx=-1)` accessor; `attack_visual_manager.gd` projectile/beam/volley positions and `impact_feedback_manager.gd` burst position now sample a random squad mesh on the firer/target instead of the unit's logical center. Bloom emission glow left unit-centered (unit-wide damage flash, not a localized impact). Burst impact y now follows the squad's layer height (was hardcoded 0). Sim-side facing tests stayed green. Isolated harness scene at `scenes/debug/test_squad_impact_origins.tscn`.
