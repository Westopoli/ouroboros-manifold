# Priority Queue

Single source of truth for what to build next. One feature at a time, done well, then merge before starting the next.

This is a **flat ordered list**. Top of the list = current focus. No batches, no waves, no umbrellas. If an item feels like two items, split it.

There is no ship deadline. There is no Pre-Zip gate, no beta wave, no Steam launch milestone. The project is long-term. Each feature lands with isolation tests + integration tests + doc updates + zero floating TODOs before the next one starts.

---

## How to use this queue

- **NEXT** = the one feature being worked on right now. Move it through `queued → in-progress → confirming → done`.
- **Soon** = next few features Westley has roughly ranked. They've had at least a pass of "is this still the right thing?"
- **Backlog** = everything else. Unranked. Grouped lightly by area for scanability.

Promotion from Backlog → Soon → NEXT requires a fresh look from Westley each time. The queue is not a contract; an item that doesn't pass that fresh look gets re-ranked or dropped.

### Definition of done (every item)

- Working code in `main`.
- Isolation test covering the core mechanic alone.
- Integration test covering the feature in a realistic scene with everything else running.
- Doc updates: any bible/spec/CLAUDE claim made wrong by this change is deleted or rewritten *in the same PR*.
- Zero floating TODOs in the changed files. TODOs that survive must point to a specific named feature in this queue.

If any of the above isn't true, the item is not done.

---

## NEXT

*(Empty — Westley to pick from Soon, or seed a new one here.)*

---

## Soon (Westley to rank/confirm before promotion)

Seeded from prior queue + launch_todo harvest. Order below is a starting suggestion, not a decision.

### Save/resume tactical mid-mission state
**What:** Player can quit mid-mission and resume with the same tactical state — units, positions, HP, objectives intact.
**Built:** `TacticalEngine.export_full_state()` + `restore_from_state()`, `write_tactical_state`, `load_tactical_state`, `consume_tactical_state`, `has_tactical_state` in sim. World-level save/resume v1 already shipped.
**Missing:** in-mission pause-menu UI, autosave hook on abandon/quit, resume-on-mission-start branch that loads tactical.json + calls `restore_from_state`.
**Why next:** large in-flight feature with substantial infra already built; finishing it clears the deck and produces a measurably better playtest experience.

### Pause menu (in-mission exit path)
**What:** In-mission ESC opens a menu with Resume / Settings / Exit-to-Main-Menu.
**Why:** prerequisite for the save/resume tactical work above; currently no clean way to leave a mission.

### In-game tutorial (lore-flavored)
**What:** First-run flow that explains movement, selection, control groups, the mission objective, and the chronicle, written in chronicle voice.
**Built:** `scenes/onboarding/onboarding.gd` (difficulty + archetype picker) + `onboarding_store.py`. Onboarding runs once before first mission.
**Missing:** tutorial content under `simulation/library/tutorial/`, trigger logic on first mission, hint surface in mission scene.
**Why:** any tester or future-Westley playing cold has no way in without it.

### Stage 6 Checkpoint J — RPS balance (combat identity)
**What:** Re-audit every L1–L4 fixture under the Testing Rigor Directive (control all variables; verify fixture before asserting on system). Then fix the actual balance bugs (L1 Strike vs Siege 0% wins; L4 soft RPS gradient broken).
**Why:** combat is the heart of the game; current state has known unwinnable matchups.

### Mission objectives clarity (first-time-player UX)
**What:** Pre-mission briefing screen names the objective in plain language, OR a first-time tutorial tooltip on the HUD objective entry. Likely solved together with the in-game tutorial.
**Built:** `scenes/tactical/hud.gd` objectives list w/ progress bars + 6 objective-type descriptions; `mission_marker.gd` in-world beacons; HUD + beacons populated from snapshot deltas.
**Missing:** the plain-language briefing surface.

### Mission map movement speed
**What:** Either retune `tactical.gd PAN_SPEED` default OR add a Settings slider for edge-scroll speed.
**Built:** `UIDataBus.edge_scroll_speed` (clamped 200–6000, persisted via ConfigFile), zoom-scaled pan.
**Missing:** UI surface for the slider, or just a retune.
**Why:** quick win that improves daily playtest.

---

## Backlog (unranked, grouped)

### Combat + balance
- Fix unit sizing (visual scales feel off)
- Fix unit balance (general pass beyond Stage 6 J)
- Stage 11f fairness redesign (blocked on playtest data corpus)

### World view + map
- Map view redesign (Settled Reach v2; needs design spec first)
- Color legend for world view (faction-color mapping)
- "Center view / zoom out" button on world view
- Border vs trade connection visual distinction (solid vs dashed)
- Smooth territory transitions (shader-uniform animation; Stage 11 known limitation)

### Tactical scene + controls
- Fix main camera pan/zoom feel (polish-tier; separate from movement speed)
- Pan/drag invert option in settings
- Command queuing (shift-queue multiple waypoints/orders)
- Fog of war terrain darkening (SC2-style)
- Hotkeys 1–4 auto-assign — pending full hotkey scheme rework; don't lock in new mappings

### Chronicle + content
- Improve chronicle output (tighten prose generation)
- Skip button for chronicle entries (per-entry + skip-all)
- Regenerate library names (AI-quality pass with better prompting/curation)

### Stage 11g checkpoints (deferred, defaults functional)
- Checkpoint M — faction palette integration (stable hues across time jumps; vivid/pale by size)
- Checkpoint N+O — chronicle mentions (click faction/region names → camera/panel navigates)
- Checkpoint P — bible amendments (docs-only; after M/N/O ship)
- Checkpoint Q — stage gate sign-off (depends on L+M+N+O+P)

### Performance + infra
- Performance budget profiling (50v50 mission frame time + sim tick metrics)
- Sim validator (automated invariant + regression system — spec lives at `docs/sim_validator_plan.md` if extant)

### Art + placeholder removal
- Remove static flyby ship animations (placeholder)
- Create production building assets (reinforcement structures need real art)

---

## Known pre-existing test failures (logged, not actively claimed)

Triaged when an item touches the relevant subsystem:

- `test_stage8_integration.py` — `numpy.int32` not JSON-serializable in `death_log`
- `test_checkpoint_h.py` — `chronicle_assembler.py:264` reads `region.name`, MockRegion missing it
- `test_stage7_checkpoint_k.py` — Raider spawn position drift
- `test_4b_selector.py` — lineage recency penalty insufficient
- `test_stage7_checkpoint_m.py`, `test_6j_{matrix,mixed,tuning}.py`, `test_siege_hp_sweep.py` — 180s timeouts
- `test_game_loop.py`, `test_stage7_5_checkpoint_i.py` — flaky under parallel; pass serial
