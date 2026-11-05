# Backlog seed (carried from the retired priority queue, 2026-09-10)

The one-queue workflow is retired under the north star. This file preserves the Soon, Backlog, Pre-Steam, research-only, and known-failure inventories from `docs/priority_queue.md` so nothing is lost before the Stage 4 product backlog (`docs/legacy/agora_era/backlog.md`) exists. Every item here that survives becomes a story in an epic or a backlog row; items already verdicted in the Stage 1 audit (A-537 through A-552) carry those verdicts. Multiplayer, multi-era, and their coupled items are core now (vision_v2), not research-only; the Lieutenant System and its decision engine are killed; pause-and-command language is stale everywhere it appears below.

**What:** Walk every idea in the bible with Westley and record keep / kill / rewrite / defer per row, after a vision interview. Runs in a separate Claude Sonnet 5 chat started from `docs/legacy/agora_era/stage1_brief.md`.
**Output:** `docs/legacy/agora_era/stage1_audit.md`, `docs/northstar/vision_v2.md`.
**Why next:** First stage of the north star (`docs/northstar/README.md`). Everything downstream (bible reformat, e2e definitions, tests, sprints) depends on it. This queue is retired in Stage 2 in favor of the product backlog.

---

## Soon (Westley to rank/confirm before promotion)

Seeded from prior queue + launch_todo harvest. Order below is a starting suggestion, not a decision.

### Fix the current game build error (blocks reference capture)
**What:** The existing Godot game does not run. Load of `privacy_modal.tscn` fails at `autoload/tactical_bridge.gd:64` — `Parser Error: Identifier "WsClient" not declared in the current scope`. Reported by Westley 2026-09-13 with an editor screenshot.
**Why:** Blocks capturing the existing in-game galaxy-view animation, which E-09 reuses as its reference (`docs/bible/references/E-09/notes.md`), and blocks any other live reference or playtest on the current build. Not part of the C rewrite; a small fix to the current client.
**Note:** `tactical_bridge.gd` is a client autoload, not a protected sim equation file.

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

## Pre-Steam-submission (picks up when game is closer to ready)

Distribution + store-page work. Not active now. Pulled from the dead Phase 1 ship plan but kept here so the inventory isn't lost. Each entry rescoped to "long-term, no rush" framing — no 30-day Steam Direct clock pressure, no Next Fest deadline.

- **Steam page draft** — short + long description, tag list. Tags from `docs/legacy/topics/steam_tag_overlap_2026.md`. Capsule copy: "pause-and-command tactical with generational chronicle." Avoid "RTS" / "Real-Time" surface strings (per market research at `docs/legacy/topics/rts_market_kill_zone_2026.md`).
- **Capsule plate art** — main capsule + small + header. Use existing tool subscriptions (Recraft-or-similar). Research at `docs/legacy/topics/steam_capsule_ab_norms.md`.
- **Screenshots (8–12)** — pause-frame compositions, chronicle text overlays, faction map shots. From in-game. Research at `docs/legacy/topics/screenshot_conversion_patterns.md`.
- **Trailer (60–90s)** — self-edited. Pause-frame shots, chronicle text overlays. Research at `docs/legacy/topics/trailer_structure_norms.md`.
- **Steam Direct $100 fee + 30-day waiting clock** — mandatory paid spend. Triggered when store page draft is ready. Not before.
- **Next Fest entry** — pick fest in launch window. Research at `docs/legacy/topics/festival_roster_and_timelines.md` + `docs/legacy/topics/steam_next_fest_timing.md`.
- **Community outreach posts** — r/grandstrategy, r/4Xgaming, r/IndieGaming, GameDiscoverCo public list. Research at `docs/legacy/topics/community_map_subreddit_discord.md`, `docs/legacy/topics/newsletter_and_curator_surfaces.md`, `docs/legacy/topics/press_outlet_map.md`.
- **Stage 13 packaging revival** — PyInstaller spec, Windows pass, privacy modal, clean-install verify. Spec deferred at `docs/stage_specs/_deferred/stage_13_spec.md` — pull back into active stages when this group fires.

---

## Research-only / not committed to implementation

Design directions alive as research, not committed to bible or stage specs. Each opens a fresh Design Lane fork if picked up — not a resurrection of the 2026-05-16 In Flux prose.

### Core gameplay directions

- **Lieutenant System** — personality-driven AI sub-formations the player commands instead of direct unit control. Research: `docs/legacy/topics/lieutenant_pivot_niche_brief.md` + feeder briefs + research_lane_queue Q4/Q5/Q9/Q11/Q12/Q14/Q24. Precedent: `docs/legacy/games/menace.md`.
- **Lieutenant decision-engine architecture** — Utility AI engine + named "intentions" (15–30 pre-authored short ordered plans) + voice library indexed by (personality, intention, phase). Offline pre-gen via existing AI pipeline. Was parked pending player-interaction-loop fork. Coupled to Lieutenant.
- **Sim depth expansion ("Cheap-Wide" package)** — new decision dimensions added to factions/regions: Legitimacy + Cohesion + Ideology-faction + Diplomacy-deepen + Logistics-derived + Intel-Lite. Foundation-feel substrate.
- **Multiplayer / per-mission co-op** — drop-in tactical co-op while the macro layer stays single-player. Research: `docs/legacy/topics/mp_session_model_precedents.md`, `docs/legacy/topics/delegated_command_precedents.md`.
- **Grand-strategy economy depth** — Arma-style economy/strategic depth additions beyond current "commander not king" framing. No research artifacts; would start fresh.
- **Hard Mode difficulty tier** — 4th tier beyond Easy/Medium/Hard. All-army hotkey disabled, tighter timers, tougher enemy comps. Demands genuine multi-front skill.

### Multi-era catalog (all coupled to multi-era decision)

- **Multi-era DLC ladder / per-era pack catalog** — 7-era × 6-DLC progression catalog. Architecture (Sacred Principle #3 era-agnostic engine) supports it. Research: `docs/legacy/topics/dlc_pricing_ladders.md`, `docs/legacy/topics/dlc_attach_rates.md`, `docs/legacy/topics/per_era_dlc_structure.md`, `docs/legacy/topics/free_tier_paid_dlc_precedents.md`, `docs/legacy/games/ck3_dlc_ladder.md`, `docs/legacy/games/stellaris_dlc_ladder.md`, `docs/legacy/games/rimworld_dlc_ladder.md`.
- **Branch System** — each era ships multiple "branches" expressing signature mechanical stances across tempo / info-warfare / attrition axes. Settled Reach Branch 1 = fast-burst tempo target.
- **Branch combat parameterization** — move HP / damage / reinforcement rates / fog density / sensor range / cross-layer detection from global constants to per-era manifest config. Config-driven only — Sacred Principle #3 stays clean (no code-branched era logic).
- **Settled Reach combat retcon** — rebalance HP and engagement timings downward for Branch 1 fast-burst tempo. Stage-6-scale tuning pass; gated on Branch System + Branch combat parameterization landing first.
- **Multi-stage tutorial across hallmark eras** — tutorial threaded through multiple eras as design hook. Coupled to multi-era catalog being real.
- **Era pack tooling** — skeleton/skin expansion toolchain to build era packs at production cadence.
- **Inspection mode for non-owned eras** — preview locked eras for storefront/upsell. Coupled to multi-era + DLC entitlement.

### Save/rewind robustness

- **Crash recovery, multi-branch save tree, cloud saves** — beyond Stage 8 rewind-with-reseed. Crash recovery is most independent; multi-branch tree UI + cloud saves are bigger lifts.

### Player-facing polish

- **UI layout customization** — settings mode to reposition HUD elements (minimap, hotkeys bar, etc.), flip map orientation, preview live within settings screen.
- **Sound design, music** — production-quality audio pass. No commitment yet.

---

## Known pre-existing test failures (logged, not actively claimed)

Triaged when an item touches the relevant subsystem:

- `test_stage8_integration.py` — `numpy.int32` not JSON-serializable in `death_log`
- `test_checkpoint_h.py` — `chronicle_assembler.py:264` reads `region.name`, MockRegion missing it
- `test_stage7_checkpoint_k.py` — Raider spawn position drift
- `test_4b_selector.py` — lineage recency penalty insufficient
- `test_stage7_checkpoint_m.py`, `test_6j_{matrix,mixed,tuning}.py`, `test_siege_hp_sweep.py` — 180s timeouts
- `test_game_loop.py`, `test_stage7_5_checkpoint_i.py` — flaky under parallel; pass serial
