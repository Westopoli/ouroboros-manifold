# Phase 1 Ship Plan — Pause-Tactical Reframe (2026-05-18, revised 2026-05-21)

> **Authoritative for current work.** This file is the master directive for what new chats should be doing on this project. If anything in `docs/bible/**`, `docs/priority_queue.md`, `docs/stage_specs/**`, or memory conflicts with this file, **this file wins** for the duration of Phase 1 (locked 2026-05-18). Reopen criteria at the bottom.
>
> **New-chat reading order:**
> 1. This file.
> 2. `docs/priority_queue.md` Pre-Zip Beta Readiness Gate (Phase 1 BLOCKERs + S#1–S#7 Steam tasks).
> 3. `docs/bible/game_bible.md ## In Flux ### PIVOT 2026-05-18` (hub-level resolution).
> 4. Spoke files only when a task touches them — all spokes carry SUPERSEDED banners pointing back here.
> 5. Memory `project_current_focus.md` (points here).
>
> **Live plan-mode artifact:** `/Users/westley/.claude/plans/synchronous-stargazing-widget.md`. Same content as this file at lock time. Plan file is a planning artifact only — not graphify-indexed, not the authoritative source after plan-mode exit.

---

## Context

Westley reframed 2026-05-18:

1. Current Ouroboros is **RTS at heart** → kill-zone per research (Stormgate, Tempest Rising, Homeworld 3, ZeroSpace all collapsed 2024-2025).
2. Real goal: **side hustle, $500-$1000/mo floor** (happy with more).
3. **2-4 weeks max more work** on Ouroboros, then walk away.
4. Decision locked 2026-05-18: ship existing engine as **pause-and-command tactical with chronicle**, NOT as RTS. Same engine, different positioning, exits kill-zone w/o code rebuild.
5. Side-hustle income vehicle (solo SaaS) lives in separate chat. This plan = Ouroboros only.

---

## Why Reframe (Not Rebuild)

- RTS positioning = death; pause-and-think tactical = alive (CK3, Wildermyth, Battle Brothers, Old World at $20-$30).
- Indie game hit rate at $500/mo: 1-5%. Strategy genre player-motivation declining (Quantic Foundry 50th → 33rd percentile 2015-2024).
- Median indie lifetime gross revenue (Steam 2025): $249.
- Turn-based pivot infeasible in 2-4 wk window.
- **Reframe = same code, different tribe.** Tactical engine + pause coordinator (Stage 11g L done) + chronicle + faction sim already support pause-and-command framing.

**Expected outcome Phase 1:** lifetime revenue $5-25k; probability $500/mo sustained 15-25%. Steam page becomes audience asset regardless of revenue.

---

## Scope Freeze

**IN:**
- Pause-and-command tactical engine (existing)
- Chronicle + faction sim + region map (existing)
- 10 mission archetypes (existing)
- Pre-Zip BLOCKERs (save/resume, tutorial, mission objectives, packaging — see `docs/priority_queue.md`)
- 2.5D layering visual polish on existing renderer
- Roman era only

**OUT (killed for Phase 1):**
- Lieutenant System redesign
- Multi-era DLC ladder
- Multiplayer / Steam SDR
- Grand-strategy economy depth
- Any non-BLOCKER queue item

---

## 4-Week Ship Plan

### Week 1-2: Pre-Zip BLOCKERs + Visual Polish
Close BLOCKERs in `docs/priority_queue.md`: save/resume world v1, save/resume tactical mid-mission, mission map movement speed, mission objectives clarity, in-game tutorial, Stage 13 packaging. Visual polish: 2.5D layering pass on existing renderer; asset polish via existing Sloyd + Recraft subscriptions.

### Week 3-4: Positioning + Ship Prep
- **Steam page draft:** Tags: Strategy + Tactics + Story-Rich + Sci-Fi + Indie. NEVER RTS / Real-Time-Strategy.
- **Capsule copy:** "Pause-and-command tactical with generational chronicle." No "RTS" string anywhere.
- **Screenshots:** pause-frame composition, chronicle text overlays, faction map shots.
- **Trailer:** self-edited 60-90s, pause-frame shots, chronicle overlays, NO frantic-click footage.
- **Launch ops:** Price $10-$15. Submit nearest Steam Next Fest. Pay $100 Steam Direct fee → 30-day waiting clock.

### Marketing Budget
$0 additional default. Sloyd + Recraft + self-edited trailer = full Phase 1 coverage. Steam Direct $100 is the only mandatory paid spend. Open to "very minimal IF high bang for buck" — flag candidates at decision moments only.

### Post-Launch
- No DLC roadmap promised.
- No community management beyond critical bugfix.
- Attention pivots to SaaS sprint (separate chat).

---

## Decisions Locked

1. **Ship as pause-and-command tactical, not RTS.** No code rebuild; positioning + tagging + copy work.
2. **Scope frozen at current BLOCKERs + 2.5D polish.** Lieutenant / multi-era / MP / grand-strategy excluded permanently for Phase 1.
3. **Price $10-$15.** Portfolio + tail-revenue framing.
4. **Marketing spend = $0 additional default.**
5. **Walk away post-launch.** No DLC promised, no community management beyond bugfix.
6. **SaaS sprint owned by separate chat.**

---

## Phase 1B — Implementation Test Architecture

### Operating constraints
- **Single chat** running on project (no more parallel implementer/design/research lanes).
- **Heavy TDD + parallel sub-agents** — long planning turn fans out into many Sonnet sub-agents working independently on bite-sized test pairs.
- **Terminal testing primary.** Visual Godot confirmation by Westley reserved for animation/look-and-feel checks in latter half of project.

### Westley questions, answered

1. **Stage 13 packaging still needed?** YES, KEEP. Without PyInstaller bundle there is no friends-ZIP to ship. Audit (2026-05-16) confirmed Stage 13 is mostly wiring on top of built infra. Real work: 1-line `project.godot` autoload fix, Windows `pyinstaller_win.spec` scaffold, privacy modal scene, clean-install verify Mac+Win. Estimate: ~1 day.
2. **Iterate-config loop for movement speed (BLOCKER 4)?** Pattern valid but **not needed for B4**. Settings slider already wired end-to-end (`scenes/settings/settings.gd:150`, `UIDataBus.edge_scroll_speed`). B4 = Westley plays one mission → picks number → agent retunes `PAN_SPEED` default in `scenes/tactical/tactical.gd:5`. Iterate-config loop pattern reserved for POST-BETA balance work (Q#7 RPS, A2 duration retune).
3. **Single chat acknowledged.** All implementation orchestration goes through this chat.

### Apex E2E ship test

**Test name:** `test_phase1_apex_ship.py` (Python sim side) + `test_phase1_apex_ship.gd` (Godot side, headless when possible). Full spec: `docs/test_specs/apex_ship_test.md`.

**Scenario walk:**
1. **Cold boot:** fresh `saves/` dir. Launch Godot → main menu.
2. **Onboarding:** difficulty + archetype picker completes → `onboarding.json` written.
3. **Tutorial:** first-mission tutorial fires → asserts scripted state transitions hit.
4. **World view:** sim boots → first time-jump fires → autosave `sim.json` written. Format matches `serialize_world()` schema v3.
5. **Mission entry:** click region → `mission_briefing.gd` opens → pre-mission briefing names objective in plain language (B2 wire).
6. **Tactical layer:** mission scene loads → mission marker beacons populated → HUD objectives list populated.
7. **Tactical mid-mission save:** pause menu opens (B6) → autosave writes `tactical.json` → quit to main menu.
8. **Resume:** CONTINUE → sim reboots with `--load <slot>` → world state restored verbatim → tactical state restored verbatim → resume tactical scene at saved tick.
9. **Mission resolution:** win or lose → debrief screen → autosave fires → world view returns.
10. **Clean exit:** quit → process tree closes, no hung subprocess.

**Reusable harness:** `simulation/setup_sim_env()` + `simulation/sim_tuner.py` scenario runner + `simulation/test_pipe_load_resume.py` patterns. Godot side leans on existing `tests/test_*.gd` pattern.

### Per-BLOCKER test pairs (isolated + integration per CLAUDE.md testing rigor directive)

| BLOCKER | Isolated test | Integration test | Parallel-safe? |
|---|---|---|---|
| **B2 Objectives clarity** | `test_b2_briefing_text.py` — `mission_briefing.gd` reads from `UIDataBus.get_mission_briefing()` returns objective name in plain language for all 6 archetypes | `test_b2_briefing_integration.gd` — fresh mission start → briefing opens → objective text rendered → dismissed → tactical scene loads w/ matching HUD objective | YES (own scene) |
| **B3 Tutorial** | `test_b3_tutorial_lib.py` — `simulation/library/tutorial/` lookups return scripted hint text for 5 tutorial beats; library cache works | `test_b3_first_mission_integration.gd` — fresh save → onboarding → first mission triggers tutorial overlay → scripted input → final beat completes | YES (own files) |
| **B4 Movement speed** | `test_b4_pan_constant.gd` — `PAN_SPEED` default produces target screen-cross-time at default zoom | n/a — slider wired; covered by apex test | YES (1-line) |
| **B5 Packaging** | `test_b5_pyinstaller_build.sh` — Mac + Win specs both build; binaries exist | `test_b5_clean_install.sh` — fresh user dir, unzip release, launch headless, exit clean | YES (own build dir) |
| **B6 Tactical save** | `test_b6_tactical_serializer.py` — `TacticalEngine.export_full_state()` + `restore_from_state()` round-trip: units, RNG, objectives, command queue, reinforcement structures byte-identical | `test_b6_pause_resume_integration.gd` — mid-mission pause → autosave → quit → CONTINUE → tactical resumes at saved tick → mission completes correctly | NO — overlaps B3 pause menu; serializes after B3 |

### Sub-agent dispatch model

**Orchestration (this chat, Opus):**
1. Pick BLOCKER from gate.
2. Read relevant code (Grep / Read / Graphify).
3. Write test pair spec inline (fixture, assertions, fail modes).
4. **WAVE BRIEFING (mandatory pre-dispatch):**
   - Before dispatching ANY parallel sub-agent wave, orchestrator writes a wave brief to chat in caveman mode containing, per sub-agent:
     - Sub-agent name + role
     - Target file paths it will read
     - Target file paths it will write/edit
     - Test fixture spec (inputs, seeds, mocks)
     - Assertion list (numbered, specific)
     - Fail-look-fors
     - Scope guardrails (engine files protected, no design latitude, caveman directive)
   - Westley reviews wave brief → approves or amends.
   - **Only after explicit approval** does orchestrator dispatch parallel `Agent` tool calls.
   - Re-run waves get a delta-only re-dispatch brief, Westley re-approves.
5. Dispatch one Sonnet sub-agent per test (or paired test+impl). Sub-agent writes test red, then impl green, then refactor. Returns diff + test output.
6. Read sub-agent output. Green + clean diff → commit on `wn/feat-blocker<N>-<slug>`. Fail → diagnose, re-brief, re-dispatch.
7. After all BLOCKER tests pass, run apex E2E once → confirm no regression.

**Parallel dispatch rules:**
- Up to 4 sub-agents in flight when test + impl files share zero overlap.
- B2 + B3 + B5 can run parallel (own surfaces). B4 is 1-line. B6 serializes after B3 (pause menu).
- Each sub-agent gets caveman directive per `feedback_subagent_caveman.md`.

**Why the briefing step exists:** Westley cannot babysit each sub-agent during the wave (whole point of parallel fan-out is reduced babysitting). The briefing IS the babysitting — done once, up front, against a written spec Westley reads in caveman mode. Wrong brief caught pre-dispatch = minutes. Wrong brief caught post-dispatch = wave-worth of bad commits + revert. Per `feedback_stop_and_ask.md`.

### Headless Godot CI bootstrap

No `godot --headless --quit-after` runner today. Add `scripts/run_godot_tests.sh` — wraps `godot --headless --path . --script res://tests/test_X.gd --quit-after 30`. Captures exit code. Local runner only — not a CI service.

### Iterate-config loop pattern (POST-BETA reserve)

Documented now, used later:
1. Spec target behavior numerically (e.g., "engagement duration mean 30-45s across 5 seeds").
2. Sub-agent picks config knob from `simulation/config.py`.
3. Loop: edit config → run `sim_tuner.py` scenario → measure → compare → adjust → repeat. Max N iterations or convergence.
4. Commit best config + measurement log. Orchestrator reviews.
5. **Bounds:** sub-agent must not touch protected engine files (per CLAUDE.md), must not widen invariants.

Reserved for: Q#7 RPS rebalance, A2 duration retune, any balance task where target is bible-numerical and config covers the search space.

### Critical files for implementation

**Existing infra to reuse:**
- `simulation/setup_sim_env()` — sim harness
- `simulation/sim_tuner.py` — scenario runner
- `simulation/test_pipe_load_resume.py` — integration test template
- `simulation/test_world_serializer.py` — serializer test template (apply to B6)
- `simulation/save/world_serializer.py` — `serialize_world` / `deserialize_world` pattern
- `simulation/save/autosave.py` — autosave trigger
- `simulation/save_writer.py` / `save_loader.py` — `write_tactical_state` / `load_tactical_state` stubs present
- `simulation/tactical_engine.py:139–245` — `export_full_state` / `restore_from_state` already implemented
- `scenes/mission_briefing/mission_briefing.gd` — 25KB scene, needs linkage
- `scenes/settings/settings.gd:150` — edge-scroll slider wired end-to-end
- `autoload/debug_overlay.gd` — F3-toggle FPS/tick/units built

**Missing surfaces (build):**
- `simulation/library/tutorial/` directory + content JSON
- In-mission pause menu scene (`scenes/tactical/pause_menu.gd`)
- `build/pyinstaller_win.spec` scaffold
- Privacy modal scene
- `scripts/run_godot_tests.sh`
- `project.godot [autoload]` — add `DebugOverlay="*res://autoload/debug_overlay.gd"`

### Verification for this phase

1. Apex E2E test passes end-to-end on a fresh checkout.
2. Each BLOCKER's isolated + integration test green.
3. All BLOCKERs flipped `[x]` in `docs/priority_queue.md` gate.
4. Friends-ZIP builds clean on Mac AND Win, launches on fresh host, exits clean.
5. Westley does ONE manual playthrough end-to-end before friends-ZIP ships.

### Order of execution

0. **Save plan to docs.** This file + `docs/test_specs/apex_ship_test.md`. DONE.
1. **Bootstrap:** `scripts/run_godot_tests.sh` + `DebugOverlay` autoload line. ~30 min.
2. **Apex test spec** (`docs/test_specs/apex_ship_test.md`) — 10-step walk + assertions. ~1 hr.
3. **Wave 1 brief** (B2 + B3 + B5 isolated tests, 3 sub-agents) → approve → dispatch.
4. **Wave 1 review** — collect results, integrate, isolated tests green.
5. **Wave 2 brief** (B2 + B3 + B5 integration tests) → approve → dispatch.
6. **B4 retune** (after Westley plays). 5 min direct.
7. **Wave 3 brief** (B6 isolated + integration after B3 pause-menu surface lands) → approve → dispatch.
8. **Apex E2E run** — confirm no regression. ~30 min.
9. **Westley manual playthrough** — final sign-off.
10. **Stage 13 clean-install verify** Mac + Win → friends-ZIP cut.

Total: 2-4 weeks at sub-agent fan-out + nightly Westley confirms.

### Doc-save plan

- `docs/phase1_ship_plan.md` — **THIS FILE.** Authoritative source for Phase 1. Graphify-indexed.
- `docs/test_specs/apex_ship_test.md` — apex E2E spec.
- `docs/test_specs/blocker_<N>_<slug>.md` — per-BLOCKER test pair spec, written before each wave brief.
- Wave briefs themselves live in chat — throwaway after approval+dispatch.

---

## Wave 2.5 — Cover-LOS Rework (added 2026-05-21)

### Context

Wave 2 (mission briefing + tutorial overlay + A3 map cover) completed. During H4 audit (`docs/test_specs/cover_semantics_bible_audit.md`), Westley surfaced spec conflict: live `simulation/damage.py:132-136,171-175` implements cover as continuous-gradient damage multiplier per bible (`bible_combat.md:421,440`, `bible_world.md:144`). Westley locked new design 2026-05-21:

**Cover = SC2-style binary LOS-blocker. Polygon model. Symmetric blind. No proximity reveal. No fire-reveal. Non-destructible Phase 1. AI peek = audit + minimal fix.**

Bible revision, not bug fix. Cover-as-damage-reduction language dated 2026-04-02 / 2026-04-06 (commits `e0508de`, `ee6d512`).

### Spec source-of-truth

`docs/test_specs/cover_los_rework_spec.md` — locked design contract, file scope, type contract, algorithms, test expectations.

### Leaf decomposition (swarm skill)

| Leaf | Scope | Parallel? |
|---|---|---|
| L1 | Bible rewrite: `bible_world.md:144`, `bible_combat.md:421/440/529`. Docs only. | Independent |
| L2 | `tactical_map.py` cover polygon data + `is_in_cover` + `cover_polygon_containing` + tests | Independent |
| L3 | `gradient_placer.py` cover-source → polygon conversion + tests | After L2 |
| L4 | `fog_of_war.py` symmetric-blind cover-occluder pass + tests | After L2 |
| L5 | `damage.py` rip `(1.0 - cover)` mult + visibility-gate + tests | After L4 |
| L6 | AI targeting audit + minimal cover-peek fix + tests | After L5 |
| L7 | Apex integration test addendum + combat balance re-baseline | After L5/L6 |

L1, L2 parallel start. L3, L4 after L2. L5 after L4. L6, L7 after L5.

### Wave 3 parallelism

Wave 2.5 (sim + bible + damage) and Wave 3 (B6 pause menu UI + B3 tutorial wiring + B4 PAN_SPEED) run fully parallel. Zero file overlap.

### Estimate

Wave 2.5 realistic: 4–5 days. Wave 3 parallel: 1–2 days. Combined critical-path: ~5–6 days within Phase 1's 2–4 week budget.

### Cross-pointers

- Spec: `docs/test_specs/cover_los_rework_spec.md`
- Audit that surfaced conflict: `docs/test_specs/cover_semantics_bible_audit.md`
- Plan file: `/Users/westley/.claude/plans/synchronous-stargazing-widget.md` (Phase 1C section)
- Memory: `project_cover_los_decision.md`

---

## Reopen Criteria

This plan re-opens only if (a) Phase 1 launches AND revenue beats $25k lifetime ceiling within 60 days post-launch, AND (b) Westley re-evaluates side-hustle vehicle stack. Until both conditions met, scope kills stand.

---

## Critical Files (Reference Only)

- `docs/bible/game_bible.md` — hub bible, In Flux entry points here
- `docs/priority_queue.md` — Pre-Zip BLOCKERs + Steam launch tasks (S#1-S#7)
- `docs/research/topics/rts_market_kill_zone_2026.md` — confirms reframe escapes contamination
- `docs/research/topics/steam_tag_overlap_2026.md` — tag bundle guidance
- `docs/research/topics/audience_psychographics_2026.md` — capsule + trailer voice reference
- `docs/research/topics/wishlist_conversion_benchmarks_2026.md` — funnel-math reference
