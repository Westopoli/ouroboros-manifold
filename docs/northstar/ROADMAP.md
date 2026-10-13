# Roadmap

Last updated: 2026-10-07: section 2b added, the order of work after the beta workflow (Westley). Before that, 2026-10-06 (twelfth update): W1 to W5 in rulings-2 Addendum 68; L1, L2 and most of L3 answered in the register; the layout engine now leads the landscape engine.

What is being built now, what is built next, and in what order. `PLAN.md` is the method; this file is the order. One row per plan.

Rules for this file:

- Rewrite, never append. History is `git log`.
- A row points to a plan doc and never restates it. No design text here.
- A plan enters "Queued" only when it has a doc path. An idea without a doc goes in "Not planned yet".
- Whoever starts, finishes or reorders a plan updates this file in the same commit.
- File ownership stays in `plans/push/pieces.toml`. Open questions stay in `ambiguity_register.md`. Rulings stay in `plans/2026-10-01-architect-rulings-2.md`.
- A cell marked "to confirm" was not checked against the owning chat when the row was written.

## 0. Run a prototype

Copy a command, paste it in a terminal, look, give feedback. Whoever builds or moves a prototype updates its row in the same commit. The scene path must come last.

**On a Mac.** The mockups are plain Godot scenes and need no C sim (verified 2026-10-06: `tests/test_mockup_without_pipe.gd`). Install Godot 4.6.x (the .app), then in a clone of the repo:

```
git fetch origin && git checkout mac/prototypes && git pull
GODOT=/Applications/Godot.app/Contents/MacOS/Godot
$GODOT --path . res://scenes/mockups/walkers/walkers_mockup.tscn        # walkers and flyers on generated land (keys: F1-F3 seeds, B speed, G slope, C climb, 1-5 layer, V view)
$GODOT --path . res://scenes/mockups/landscape/landscape_mockup.tscn    # land mockup pass 6b (Kit button: space kit)
$GODOT --path . res://scenes/mockups/layout/layout_mockup.tscn          # layout engine pass 1
$GODOT --path . res://scenes/mockups/settlement/settlement_mockup.tscn  # settlement pass 1
```

The first launch imports assets (about a minute). `mac/prototypes` is main plus the prototype branches (`push/proto-land-iter`, `push/proto-walkers`, `push/proto-layout`), merged read-only; it is rebuilt when a prototype moves, never edited directly. The Linux lines below keep their x11/opengl3 flags; a Mac does not need them.

Two folders hold what can be viewed:

- `~/Projects/om-push/wt/view-main`: current main, already imported. Refresh it before viewing anything new on main:
  `cd ~/Projects/om-push/wt/view-main && git fetch -q origin && git checkout -q --detach origin/main && ~/.local/bin/godot.real --headless --path . --import`
- `~/Projects/om-push/wt/proto-land-iter`: the land mockup's working copy (branch `push/proto-land-iter`), ahead of main.

If a scene prints "Could not find type" errors, the folder has not been imported since new scripts arrived: run the refresh line (or the same `--import` in that folder).

| Prototype | Command | State | Record (keys and open questions) |
|---|---|---|---|
| Layout mockup, pass 1: the flat diagram | `cd ~/Projects/om-push/wt/proto-layout && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/layout/layout_mockup.tscn` | Pass 1 built 2026-10-04, branch `push/proto-layout` (`819d7a75`); waiting for Westley's review | `research/layout_engine/README.md` section "Pass 1"; spec `plans/2026-10-04-layout-prototype-pass1-spec.md` |
| Land mockup, latest: the layout shapes the terrain | `cd ~/Projects/om-push/wt/proto-land-iter && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/landscape/landscape_mockup.tscn` | Pass 6b, 2026-10-04; approved 2026-10-05 with markers (layout flawed; scale later polish) | `research/landscape_design/README.md` on branch `push/proto-land-iter`, sections Pass 4 to Pass 6 |
| Walkers and flyers on generated land | `cd ~/Projects/om-push/wt/proto-walkers && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/walkers/walkers_mockup.tscn` | Pass 1, 2026-10-05; approved. Keys: F1-F3 seeds, B speed, G slope slows, C flyer climbs, 1-5 flyer layer, V view | `research/walkers/README.md` |
| High ground worth (chart, open the file) | `xdg-open ~/Projects/om-push/wt/proto-highground/docs/northstar/research/layer_dynamics/runs/2026-10-05_highground/highground_page.html` | 2026-10-05; a space-mechanics stand-in | `plans/2026-10-05-proto-highground-spec.md` |
| Land mockup as on main | `cd ~/Projects/om-push/wt/view-main && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/landscape/landscape_mockup.tscn` | Passes 4 and 5 | `research/landscape_design/README.md` |
| Space kit (same scene: press the Kit button until it reads space) | `cd ~/Projects/om-push/wt/view-main && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/landscape/landscape_mockup.tscn` | Pass 6; parked (A207) | `research/space_landscape/README.md` |
| Settlement mockup: a base that builds itself | `cd ~/Projects/om-push/wt/view-main && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/settlement/settlement_mockup.tscn` | Pass 1, 2026-10-03; waiting for Westley's review | `research/settlement_mockup/README.md` |
| Galaxy mockup (September mockup ladder) | `cd ~/Projects/om-push/wt/view-main && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/galaxy/galaxy_mockup.tscn` | Pass 2, 2026-09-22 | `scenes/mockups/galaxy/` |
| Hud mockup (September mockup ladder) | `cd ~/Projects/om-push/wt/view-main && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/hud/hud_mockup.tscn` | Pass 2, 2026-09-22 | `scenes/mockups/hud/` |
| Layers mockup (September mockup ladder) | `cd ~/Projects/om-push/wt/view-main && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/layers/layers_mockup.tscn` | Pass 2, 2026-09-22 | `scenes/mockups/layers/` |
| Fog mockup (September mockup ladder) | `cd ~/Projects/om-push/wt/view-main && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/fog/fog_mockup.tscn` | Pass 2, 2026-09-22 | `scenes/mockups/fog/` |
| Menus mockup (September mockup ladder) | `cd ~/Projects/om-push/wt/view-main && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/menus/menus_mockup.tscn` | Pass 2, 2026-09-22 | `scenes/mockups/menus/` |
| Objectives mockup (September mockup ladder) | `cd ~/Projects/om-push/wt/view-main && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/objectives/objectives_mockup.tscn` | Pass 2, 2026-09-22 | `scenes/mockups/objectives/` |
| Units mockup (September mockup ladder) | `cd ~/Projects/om-push/wt/view-main && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/units/units_mockup.tscn` | Pass 2, 2026-09-22 | `scenes/mockups/units/` |
| Chronicle mockup (September mockup ladder) | `cd ~/Projects/om-push/wt/view-main && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/chronicle/chronicle_mockup.tscn` | Pass 2, 2026-09-22 | `scenes/mockups/chronicle/` |
| Skill lab chart: Formation Read (a web page, not a scene) | open https://claude.ai/artifact/GcVZDf8481tppLwSHE6Bqz | 2026-10-04; private to Westley | `research/layer_dynamics/runs/README.md` |

## 1. Now building

Updated 2026-10-10 (method rev 2). Branches only; main gets a piece only through the merge gate. Lane status is kept in one place, the programme file's lane table; this table holds no copy of it.

| Lane | Branch | State | Next |
|---|---|---|---|
| **The visible game programme** (`docs/northstar/plans/2026-10-07-visible-game-programme.md`): every approved prototype into the game, the economy play, Steam phase B; stories acted out as acceptance; guards in CLAUDE.md | lane status: the programme file's lane table (the one status location) | IN FLIGHT, paused by Westley 2026-10-10 09:15; method rev 2 adopted 2026-10-10 (`plans/retro_2026-10-10/README.md`); resumes with the harness pieces and the lane E1 skeleton | marked DONE in this row and in the plan header when the last lane's stories are Seen |
| Walk-route fix piece (proposed, FINDING-walk-route-replan) | none yet | advance to the next stored waypoint instead of replanning, early exit at the goal, reused buffers; owner `csrc/walk_route.c` and `csrc/tactical_move.c` | on the programme's "No eyes needed" list once the Architect specs it |
| Programme guard pieces: GDScript reach lint and lane story plays in the gate (from the 2026-10-09 drift check) | the gate | landed: HARNESS-gdreach, HARNESS-laneplays (fc986411), HARNESS-playsplit (7bb1f5a2), G-project daemon verb (f37a926f) | the gate runs the reach lint and each lane's story plays; DONE |
| Terrain stage 2: walkers, slopes, ground vision, era kind (`plans/2026-10-06-terrain-stage2-spec.md` rev 3) | landed on main 008de465 (2026-10-07) after three sim defects found by the lab's ground scene were fixed with tests | gate clean | done |
| Terrain stage 3: missions on generated ground, the client draws it, era toggle, save 7 (`plans/2026-10-06-terrain-stage3-spec.md` rev 3) | landed on main 0304d821 (2026-10-06) | gate clean, ground-era desktop case green | lane C of the visible game programme adds the 3D ground |
| Steam P2P beta (`plans/2026-10-06-steam-multiplayer-wiring-spec.md` rev 6) | phase A landed on main e63483f6 (2026-10-06): session catch-up, Steam transport, match pump, export tooling, portability; phase B is lane F of the visible game programme | gate clean | lane F: pipe frame flag, bridge wrappers, lobby, tactical hookup, pipe per OS, depot script |
| Space lab: layout search (`plans/2026-10-06-layout-search-spec.md`, Rev 4 2026-10-07) | pieces P1 to P4 landed (ccf03460); Rev 4 (feature-relative placement, roles, decided by survivors, the hold condition, both naive baselines) built; run 1 landed 2026-10-08 (a9ee5897), chart awaiting Westley | Westley reads the chart (open list in `research/layer_dynamics/README.md`) | the first chart to Westley; then D1 unit size (after K-a lands, both edit tactical_move.c), run 2 with the category table (Q-081-01 is not it: a new row), the ground lab spec |
| Unit size as a runtime setting (`plans/2026-10-06-unit-size-runtime-spec.md`) | spec | After stage 2 lands (same file) | Two Doer units |
| Sonnet chat briefs B1 to B11 (`plans/briefs/2026-10-06-sonnet-parallel-briefs.md`) | running in a parallel chat | mop-up line of sight, tick cap 12,000, method and era-pack drafts, doctrine synthesis, website refresh, flake root cause, worktree cleanup, lab throughput | Each pushes a branch; the planner lands it |

## 2. The beta critical path (rewritten 2026-10-06 night)

Target: a private Steam beta with multiplayer and every approved prototype integrated. Westley 2026-10-07: no date; "done right than fast"; efficiency, parallelism and no drift are the measures. The path below is now carried by the visible game programme (`plans/2026-10-07-visible-game-programme.md`); this table keeps the Steam-side steps.

| # | Step | State | Gate | Then |
|---|---|---|---|---|
| 1 | Terrain stage 2 lands on main | landing clerk running (three sim defects found by the lab's ground scene, all fixed with tests) | merge gate clean, csim ids equal main | 2, 3, 4 start |
| 2 | Terrain stage 3: missions on ground, the player sees it, era toggle (`plans/2026-10-06-terrain-stage3-spec.md` rev 3) | spec audited and pre-flighted | its gate plus a ground-era desktop playthrough | 5 |
| 3 | Unit size as a runtime setting (D1) | spec ready | gate | lab run 2 |
| 4 | Steam wiring phase A: session catch-up, Steam transport, match pump, export tooling, portability (`plans/2026-10-06-steam-multiplayer-wiring-spec.md` rev 5) | workflow running | gate on `push/net-wire-a` | 5 |
| 5 | Steam wiring phase B: pipe frame flag, bridge wrappers, lobby + menu, tactical hookup | after 2 and 4 | gate plus a two-process loopback match | 6 |
| 6 | Shipping the C pipe on Windows/macOS/Linux (cross-build, static link, path resolution in exports, signing) | scouted 2026-10-06: static pipe exe per OS, mingw-w64 cross build, client path fix (Steam spec W8); needs `mingw-w64` + `wine64` installed (Westley, sudo) | a build per OS runs the probe and matches checksums (Q-NET-05) | 7 |
| 7 | First real-Steam test: Westley's two accounts on Spacewar 480, Linux + Mac | after 5 and 6 | a match to its end, a stall, a leave | 8 |
| 8 | Beta build on Westley's app id, Dev Comp keys, tester guide (`docs/northstar/beta/`) | guide and store copy drafting now; app id is Westley's (T17) | one tester plays a mission and files an F12 report | public track (store page, Coming Soon) |

Off the critical path but running in parallel: the lab's layout search (run 1 tonight, run 2 after D1 and the category table), the bug-report piece T16 (built, awaiting the gate), the flake root cause T12, the gate harness fix (merge-base footprint, lab integration stage), the doc drafts (T5, T7, T9), the website refresh (T8).

## 2b. After the beta workflow completes: verification, polish, next features (Westley, 2026-10-07)

Three steps, in this order. Step 1 and step 2 run at the same time; step 3 starts when step 2 is finished. Building new features stops for the length of step 2.

1. **Verify the simulation still follows the stochastic rules written into the bible** (`docs/bible/algorithms.md`). The legacy Python version had a small viewer, built on a Python game library, showing the regions on a 2D plane, how they are exchanged as ticks pass, which events fired, what the simulation chose for each mission and how much time passed each time (`simulation/run_strategic_viewer.py` and `simulation/strategic_viewer.py`, pygame). The goal is to find regressions in the core of the game: mission choice, and the source of the chronicle. The viewer is `scripts/simviewer/` (spec `docs/northstar/plans/2026-10-12-simviewer-spec.md`).
2. **Pause new features until the existing ones are relatively perfected.** Westley gives feedback on each aspect of the game, a change is made, and he checks it again, repeated. Only when this is finished is the game ready for Steam posting.
3. **Assess the lay of the land** for prospective and unimplemented features and decide what to build next. Contrast the old ideas in the bible and the roadmap with the user feedback received, and prioritise between them.

## 3. Blocked on Westley

Every decision waiting on Westley, in the order that unblocks the most work. Candidates for each `Q-` flag are in `ambiguity_register.md`. An answer is recorded in the register and the epic, and its row is deleted here.

### Now (at most six; Westley 2026-10-10)

The Dispatcher keeps this table at six rows or fewer, ordered by what each unblocks, and adds a row only when one frees; everything else waits in the sections below. A verdict on a shot is one word per row (approved or rejected, with any note) in the Dispatcher chat.

| # | Item | Where | Unblocks |
|---|---|---|---|
| 1 | Galaxy density by eye (`Q-B24-01`): does the game's Overview need more star discs, like the prototype, or is the count as built right? Prototype beside game, overview and local zoom | `docs/northstar/story_reviews/westley/2026-10-13/galaxy-PROTOTYPE-overview.png` vs `galaxy-B23-overview.png`, `galaxy-PROTOTYPE-local.png` vs `galaxy-B23-local.png` (also `review-westley/` in your checkout) | `VG-B24` layout, then B25 |
| 2 | Two of your own ground units drawn one pixel apart at the opening zoom (`Q-132-03`): (a) they really overlap at that zoom, the check compares finer than a pixel; (b) a closer opening camera or a minimum drawn body size | `docs/northstar/story_reviews/westley/2026-10-13/s132-pairs-full.png` (pairs circled red) and `s132-pairs-crop.png` (4x crop) | lane C, S-132 |
| 3 | Galaxy dot colour re-shot after the colour fix: approved or rejected | `story_reviews/B.md`, run 20261013-0216-5f3ee95 | `VG-B24` |
| 4 | Which renderer is the galaxy look (`Q-B23b-01`): Forward+ (the shells wash the dots, the pixel test gains a Forward+ run) or the default renderer | `ambiguity_register.md` | lane B pixel test, B24 |
| 5 | Settlement look re-shot after E1k: approved or rejected | `story_reviews/E.md`, latest S-237 row | lane E look pieces, the banded-contour prototype |
| 6 | Net first tick shot (S-140, reviewer unclear): approved or rejected | `story_reviews/F.md`, run 20261012-2033-b12b47a | lane F, A16 |

Waiting behind the six: lane A's S-001 group shots (`story_reviews/A.md`), and a yes or no on a second worktree pass that removes unmarked, merged, clean worktrees under `~/Projects/om-push/wt/`.

### How the work is run

| # | Decision | Notes |
|---|---|---|
| W6 | DONE 2026-10-04 (Westley asked the planner chat to do it). Was: land the Agora QA fix so the 30B can play | The fix is verified on Agora branch `lf-lane3-build` (`74956c9`): QA profile clicks NEW CAMPAIGN, empty click no longer raises. Not landed because `~/Projects/agora` (on `wn/qa-director`) has your uncommitted edit to `scripts/qa_desktop.py`. Commit or stash it, `git -C ~/Projects/agora merge lf-lane3-build`, push, restart the QA session (pid 2931521 runs the old code). |
| W8 | 17 standing failures in `tests/specfactory/` on main | Same 17 before and after this work; nobody has ruled on them. |

### Prototypes ready for your eyes

Built 2026-10-03 while you were away. Each record lists the keys to fly it and the questions for you. The commands to run each one are in section 0.

| Prototype | Record | What to judge |
|---|---|---|
| Land mockup pass 4: where walkers can go | `research/landscape_design/README.md` "Pass 4" and "Pass 4 sweep"; screenshots in `mockup/pass4/` | The too-steep view at 30 and 35 degrees, the (X) cursor, the band view, ramps. Finding: 42 to 85 percent of land is too steep and a walker reaches under 15 percent of it |
| Land terrain options page | `research/landscape_design/options_2026-10-03_walkable_land.md` | DECIDED 2026-10-04: option A (layout first, terrain obeys); walking limit 35 degrees |
| Land mockup pass 5: the layout leads, the terrain obeys | `research/landscape_design/README.md` "Pass 5"; screenshots in `mockup/pass5/` | The prototype asked for under Q-191-04. Finding: carving a layout into finished terrain leaves broken edges and wide cut routes, and the old assault layouts cannot meet the equal-distance rule for the objective. Six questions in the record |
| Settlement mockup pass 1 | `research/settlement_mockup/README.md` | Which events start a wave (Q-193-01), whether four lot stages is right (Q-193-02), whether one 300 wu route per direction is enough way through (Q-193-06) |
| Galaxy density, 2026-10-13: the prototype beside the game (B23 on main) | `story_reviews/westley/2026-10-13/galaxy-PROTOTYPE-overview.png`, `galaxy-B23-overview.png`, `galaxy-PROTOTYPE-local.png`, `galaxy-B23-local.png` | `Q-B24-01`: enough star discs on the Overview, or add decoration systems up to the prototype's count (section 3 "Now" row 1) |
| Ground opening view, 2026-10-13: two own units one pixel apart | `story_reviews/westley/2026-10-13/s132-pairs-full.png`, `s132-pairs-crop.png` | `Q-132-03`: (a) compare finer than a pixel, or (b) closer opening camera or a minimum body size (section 3 "Now" row 2) |

Land mockup passes continue in a Sonnet chat working directly with Westley (`plans/briefs/2026-10-04-land-mockup-iteration-brief.md`, branch `push/proto-land-iter`); pass 6 fixes the cliff walls drawn on every contour and makes the layout shape the terrain as it is generated. View prototypes from `~/Projects/om-push/wt/view-main` (imported, kept at current main).

### Finishing the MVP loop: questions from the scouts

Full text and evidence: `plans/2026-10-03-finish-loop-rulings.md`.

| # | Question |
|---|---|
| F1 | R-026-04: event thresholds are meant to be noised at each jump start and never are. Wiring it changes every campaign's history and every recorded golden. Now, or with the balance simulation? |
| F2 | R-062-02 collapse successor: the register has Q-062-01 closed as (b); the code and ruling A15 use most regions and call it open. Which is right? |
| F3 | Chronicle entries for a fallen faction (R-062-04) and a dead commander (R-061-04): category and wording |
| F4 | Campaign end (R-062-03): how the client is told no faction survives |
| F5 | Enemy hooks (R-121-04, R-122-01): no mission registers a second force and no hook scripts exist |
| F6 | Timed transitions (R-121-02): the duration per force |
| F7 | Cautious break-off (R-120-03): the contact threshold |
| F8 | `om_faction_phase` (R-053): who consumes a faction's phase |
| F9 | Jump length (R-056-01, Q-056-01): the client sends raw ticks with no clamp to 20 to 100 |
| F10 | Regional commander on conquest (R-060-01): never created in play |
| F11 | Two tested functions disagree with their rule or the live path: `om_player_faction_collapsed` (returns false for a faction that no longer exists, against R-062-01) and `om_selector_resolve_fallback_pool` (can name a pool the live resolver skips, R-058). Fix, or remove with their tests? |
| F12 | Objectives (R-075-03, R-075-04): four of ten archetypes can never score. What is a designated target and how many; who the escorted units are and how many; where the extraction point is; where Interception's enemy force comes from. Red tests wait on `push/obj-tests` |
| F13 | Retention (R-077-01) is now live from the force as deployed. Do the commander's unit, units made mid-mission and structures count, and is a unit that leaves the map alive? |

### Land generator

| # | Decision | Flags | Unblocks |
|---|---|---|---|
| L1 | Part 1, the ground, what is left: the smallest layer step that reads as real height, judged in the band view of the mockup (he chose to look, not to give a number); what counts as unreasonably hard to reach on foot | Q-188-01, Q-189-04 | Queue row 3 |
| L3 | Part 2, the places, what is left (answers 2026-10-03 in the register): the figures the live prototype sets (choke widths, landform bias, counts, the distance measure) | Q-191-05 | Land generator part 2 |
| L8 | Was land mockup pass 3 (2026-09-21) approved? The record still says "awaiting Westley's third look" | none | The record only |
| L9 | Name and scope of the land era | Q-147-01 | S-147; a second era to play |

### Space generator

Parked (Westley, 2026-10-03, A207): space integration is not near, so S1 to S4 are not asked until the work before the space generator is done.

| # | Decision | Flags | Unblocks |
|---|---|---|---|
| S1 | Approve a space kit pass (5 built, 6 specified). Not approved: Westley has not opened it (A207) | Q-166-02 | Writing the space stories into the bible |
| S2 | Small craft size and the gap it fits | Q-166-05 | The second passability class |
| S3 | Camera among five stacked sheets | options not yet drafted | Space client view |
| S4 | Shared density on by default; the layer gap for space eras; how the small-craft sections are chosen | under Q-166-02 | Space generator plan |

### Movement, layers and search (held by the Architect chat)

Parked (Westley, 2026-10-03, A209): none of M1 to M10 is asked until the harness experiment has been run and he has the data. The draft pass marks gate nothing (A210).

| # | Decision | Reference |
|---|---|---|
| M1 | Pass marks C0 to C9 and the 0.05 win margin | rulings-2 A174; unblocks Phase E |
| M2 | Variant B scale miss: keep red, drop the 1.35 factor for that scene, or change the pass rule | A193 |
| M3 | Confirm the leash rewrite and attack-move holding formation until in range | A188, A199 |
| M4 | Scattered-group rule (450 wu) collapses a 32-wide line | R-095-03 |
| M5 | Leash before or after damage | Q-087-01 |
| M6 | Guard stance | Q-096-01, Q-208-01; unblocks the landscape batch |
| M7 | Same-spot fling; concentration of fire | Q-097-02, Q-008-05 |
| M8 | Should the gate run the scale suite; should the tactical rule bound the worst step | rulings-2 |
| M9 | Fight length | R-085-02, R-085-04 |
| M10 | Height-band numbers scaling with step height | Q-166-04 (the skill lab measures first) |

### Balance and housekeeping (not urgent)

| # | Decision | Reference |
|---|---|---|
| B1 | Knowledge Lost rate, player-collapse rate, mirror battle length | held for the new balance simulation |
| B2 | E-17 reds: field sampling 9.5 ms against 7.4 ms; map generator and objective drift | held on the map design |
| B3 | Galaxy stack; the galaxy build chat has not reported | `plans/2026-10-02-galaxy-bubble-field-spec.md` |
| B4 | Constants promotion to `algorithms.md`; snapshot fixture policy; world-generation speed target at 400 regions | rulings-2 |

### Needed for the two-week scope, not yet sorted

| Group | Flags | Notes |
|---|---|---|
| Multiplayer | Q-144-03 (re-asked: who hosts the next sitting of a locked universe). The lockstep drop is 30 s, so the 60 s provisional setting in `plans/2026-10-05-lockstep-backend-spec.md` needs updating by its owner | Blocks S-144 and the lobby. Everything else in S-140 to S-144 and the pair stories answered 2026-10-06 |
| Economy and bases | Q-159-07 to -13, Q-167-01 to Q-181-02, Q-177-01 to -05, Q-178-01 to -05 | E-22; the largest set. An ordered answer sheet is not yet drafted |
| Settlements | Q-193-04, Q-193-05 (parked until fights have been run in the simulation) | Answered 2026-10-06: the rest of S-193 and S-222. After the land generator |
| Strongpoints and weather | Q-219-02 (to be designed; Westley prefers the player not seeing a trouble coming), Q-219-04 (parked) | Answered 2026-10-06: the rest of S-218 and S-219. After the land generator |

## 3b. Parallel work (the TODO list)

Work that does not wait on the build lanes. Written 2026-10-06 from Westley's list ("there's more than just the code"); one row per item, who moves it next, what it waits on. Research is done as a Gemini deep-research run (Westley) followed by a Sonnet synthesis (planner chat). A row is deleted when its product exists.

| # | Item | Next mover | Waits on | Product |
|---|---|---|---|---|
| T1 | Settlement mockup pass 1 approved 2026-10-06; answered the same day: cliff openings cosmetic (Q-193-03 b), five stages (Q-193-02), more than one route per direction for a big city (Q-193-06), wave types alike for now (Q-193-01 parked as polish); still open: 20 s per street, density pull of placed buildings, Q-193-04/05 | Planner chat folds into E-17 S-193 | nothing | S-193 rewritten |
| T2 | Space landscape pass 6 approved 2026-10-06 with the vision-tube note (Q-S3-01); S1 to S4, Q-166-02, Q-166-05 to be folded | Planner chat | nothing | The space kit recorded as decided; S3 options page (T3) |
| T3 | Camera options page for S3 (space, five opaque sheets) and the remaining camera questions Q-103-04/05/06, Q-232-01 (the classic view, Angle Rack, Peel, flip and continuous zoom S-234 are already decided; `options/camera/options.md` A+C picked) | Planner chat drafts; Westley picks | T2 for S3 | `research/camera/options_s3.md` |
| T4 | Sense-of-scale prototype: the Sand Table / zoomed-out end of the one drawing (Q-103-05, Q-234-01 (c): "a prototype before I commit to it"); terrain stage 3 draws the ground, which is where scale is first seen in the game | Planner chat spec; Doer; Westley look | terrain stage 3 | A mockup pass; his verdict on R-166-01's "massive scale" against the real client |
| T5 | Methodology write-up: how strategic depth is measured, the skill lab method, the prototype gate, workflow discipline; one document from `agile.md`, `PLAN.md`, `layer_dynamics/README.md`, the ping doc, CLAUDE.md "Workflow specs" | drafted on `docs/method` (B3, 2026-10-06) | nothing | lands after Westley reads it |
| T6 | Map-design pillars: review `docs/map-design-pillars` (branch), accept or amend, then map each pillar to a measurable the lab's layout search records | Westley; then planner chat | nothing | `research/map_design/README.md` on main; the layout-search spec cites it |
| T7 | Military-strategy research (terrain in doctrine, air over ground, naval and space analogues) | synthesis drafted on `docs/military-doctrine` (B5, 2026-10-06) | nothing | lands after Westley reads it |
| T8 | Website refresh (`~/Projects/ouroboros-site`, Astro on Fly.io, public; copy pinned at `e10649a1`). Westley 2026-10-06: show the galaxy view, the space and the land landscape engines, and the walking prototype (route finding among layers); add `/method` and `/research` pages, no limit on internal reasoning ("I don't have a blue ocean here I'm just having fun and want to share it with people"); captures at 1920x1080 from the live client on the RTX box; regenerate the pinned copy | Planner chat spec; a Doer captures; a drafter writes; Westley reviews | nothing | New captures and pages; `fly deploy` by hand |
| T9 | Era pack form for 20+ eras: a one-page "how an era is written" from the hub's skeleton section and E-20 (identity, kind, roster by role, kits, prose pools) | drafted on `docs/era-pack-form` (B4, 2026-10-06) | nothing | lands after Westley reads it |
| T10 | Cosmetics and art direction: nothing exists past placeholders. Westley 2026-10-06: he cannot decide verbally; he needs example choices (Claude design or a mockup tool) to pick from. Westley 2026-10-07: the art direction is documented in the bible and some assets exist, so no example pass is needed now | Westley, with a design tool; not a planner-chat build | an example set of looks | An art brief; then a cosmetics plan |
| T11 | Economy "look" mockup (ROADMAP 4b: needed, none exists): lots and placement, what buildings show, disguise, lanes, the two economy screens | Planner chat spec; Doer; Westley look | T1 | A mockup pass |
| T12 | Flaky playthrough test `test_s_c8_09`: Westley 2026-10-06, find the root cause of the dropped click ("solve the root problem, not put a bandaid on a system that is effected down the sequence"); no re-click | Engineer: diagnose the input path in the first frames of a fresh scene | nothing | The cause named; a fix in the game or the driver |
| T13 | Body size: decided 2026-10-06 (Q-LAB-02 a): the engine reads the runtime collision radius; per-type sizes follow with the era rosters; the lab finds where the lines cross as size changes | Planner chat spec; Doer | nothing | A contract piece (one parameter read at every collision site) |
| T14 | Fight tick cap raised to 12,000 (provisional; Westley 2026-10-06 "raise the cap"), and never-engaged fights must not read as ties (Q-LAB-01) | Planner chat spec; Engineer | nothing | The cap changed; the mop-up rule and the outcome classes per Q-LAB-01 |
| T17 | Steam onboarding, public track (Westley, by hand): pay the app fee (21 to 30 days to any release), finish tax and identity (10 to 15 business days if not done), create the app, a Coming Soon page (live 2 weeks before release; review 3 to 5 business days), generate Dev Comp keys for the second account; Playtest as a child app once the page passes; install the Godot 4.6.3 export templates on this box (about 1 GB) and commit the `"4.6"` feature tag (Q-NET-01) | Westley | nothing | App id 5402100 (2026-10-06); keys; dates in `docs/research/topics/steam_p2p_and_beta_submission.md` |
| T16 | Feedback and bug reports (E-16 S-245, direction 2026-10-06): in-game F12 report with a 5 to 10 s capture replayable through the lockstep save and command log; website feedback into the same queue; classification; a local model fixes bugs through the gate | beta uses the F12 stack already on main (`autoload/bug_report_manager.gd`) plus the player's words and the seed; Q-245-01/02 closed from the record, Q-245-03 deferred post-launch | lockstep client wiring; the website refresh | one small client piece: words prompt after capture, seed in metadata, 10 s window |
| T15 | Stale `om-*` checkout folders under `~/Projects` | cleaned 2026-10-06 (report in the planner chat) | | |

## 4. Not planned yet

Decided or partly decided in the bible, with no plan doc. Order within this table is the proposed build order.

| Group | Stories | Epic | State | Why parked |
|---|---|---|---|---|
| Land terrain visual pass for Westley | none | E-17 | Not written; built on the Linux machine under its prototype method (A208) | Westley asked for two things to look at: the landscape engine's output with ground steeper than 35 degrees clearly marked, so he sees where players can and cannot go (Q-189-02, Q-189-04); and the benched and natural ratio varying per map (Q-189-03, answered). Comes before land part 1 because Q-189-02's exact figure waits on it. The terrain prototype may build the six landforms in batches (Westley, 2026-10-03), and its builder picks a measure of landscape variety and asks Westley, when presenting, whether it is the variety he had in mind (Q-187-02) |
| Layout library audit and archetype pairing | none | E-17, E-10, E-21 | Not written | Westley, 2026-10-03: the eight old layouts (`simulation/layout_library/`) were authored before the game changed, so they are audited and double checked before they are implemented, and archetypes are probably paired with layouts. Each layout must offer at least one layer play, so layout 07 needs one or a replacement; the vantage reach rule changes (about 30 percent of peaks unreachable on foot); choke widths become numbers (Q-191-05). Comes before the layout prototype above |
| Layout engine and places prototype for Westley's approval | none | E-17 | Not written; built on the Linux machine under its prototype method (A208), possibly as one prototype with the terrain pass above (to confirm) | Westley asked (Q-191-04 amendment) to see the layout engine, and how the landscape engine reacts to it, in a live prototype: the landscape engine is required to produce what the layout calls for (a choke, a peak). It also shows sites found with a scoring per kind of place (Q-191-01) and the significant resources at equal distances from both sides and the objective with as much variety of shape as that allows (Q-191-03, Q-191-05). The old layouts are node graphs (`simulation/layout_library/`, dot images in `simulation/tuning_output/stage7/checkpoint_f/`). Westley approves the product before it is integrated |
| Shared layer-mask contract | none yet (carries E-01 R-001-04, E-17 R-114-01) | E-01, E-17 | Not written | Lands first inside land part 1 as its own contract piece; written so space can use it; the small-craft class needs Q-166-05 |
| Space generator | none in the bible yet | E-17 | Research and mockup passes 1 to 5; pass 6 specified | Waits on decisions S1 to S4, the stories being written, and the mask contract |
| Land generator, part 2: the places | S-187, S-191, S-192, S-195, S-197, S-200, S-201, S-207, S-221 | E-17, E-01, E-11, E-13, E-02 | Design decided, 1 flag open | Waits on the flag sheet, the places prototype Westley approves (row above), and plan A. Q-191-04 closed 2026-10-03: the rewrites of S-112 to S-119 can now be written |
| Settlements and cities | S-166, S-193, S-222, S-237 | E-17, E-02, E-18 | Design decided, Q-193-04 and -05 parked | After the land generator |
| Zoom and drawing | S-194, S-234, S-236, S-240 | E-17, E-16, E-18 | Q-194-01 needs research first (keep the backend true to the ground without heavy snapping, Westley 2026-10-06); the Sand Table waits on its prototype (Q-103-05); budgets for thousands stay a direction | Client work, after a generator exists |
| Strongpoints and weather | S-218, S-219 | E-15 | Design decided, flags open | After the land generator |
| Economy and bases | S-167 to S-182, S-202 to S-206, S-209 to S-217 | E-22, E-11, E-12, E-13, E-10, E-14 | Design decided, flags open; S-182 open | Largest group; needs places from a generator |
| Cross-epic follow-ons | S-220, S-223 to S-228, S-230 to S-233, S-235, S-238, S-239, S-241 to S-244 | several | Mixed; S-224, S-225, S-226 open | Each follows its parent group |
| Port parity P4, map content | none | E-17 | Held | Waits on the generator design |

## 4b. Prototype state

Per `agile.md`, Prototype gate. A group marked "needed" is not planned until its prototype is approved.

| Group | Prototype | State |
|---|---|---|
| Loop fix workflow; finishing the MVP loop | Not needed (wiring) | |
| Land generator | Mockup: `scenes/mockups/landscape/` | Approved 2026-10-06 (Westley: "Landscape engine is also approved"), after pass 6b's markers of 2026-10-05 (scale and size are later polish). Integration: terrain stage 1 (the field) landing 2026-10-06; stage 2 walkers and slopes, stage 3 pipe and client, to plan |
| Walking and flying units on land | Mockup: `scenes/mockups/walkers/` (`push/proto-walkers`) | Approved final 2026-10-06 (Westley: "Walkers prototype approved, no need for any more iteration that one can be integrated as is"). Integration = terrain stage 2 (walking kind, slope routing, midline rule) |
| High ground worth | Instrument: `scripts/skilllab/highground.py` (`push/proto-highground`) | Built 2026-10-05; stands in a hill with space mechanics, so it is a space-lab result, not a ground answer; its fate open |
| Space generator | Mockup: space kit mode | Pass 6 approved 2026-10-06 with a note: a vision tube through covering layers is required of the camera (Q-S3-01) |
| Movement and layers | Instrument: skill lab | Phase D pages; pass marks open (M1) |
| Economy and bases, rules | Instrument, needed | None exists. Answers the number flags: costs, times, caps, yields, technology, doctrine weights |
| Economy and bases, look | Mockup, needed | None exists. Answers lots and placement, what buildings show, disguise, lanes, the two economy screens |
| Settlements | Mockup: `scenes/mockups/settlement/` | Pass 1 approved 2026-10-06; its numbers (Q-193-01 to -06) still his |
| Layout engine | No prototype (Westley, 2026-10-06: "Layout engine doesn't need a prototype, we'll get the data on what layouts work from the simulation engine") | The space lab's layout search supplies the data; the layout-engine chat's pass 1 (`push/proto-layout`) stands as reference only |
| Multiplayer | Not needed for transport; mockup needed for lobby screens | None exists |

## 5. Dependency notes

- **Layout before landscape (Westley, 2026-10-04, verbatim: "layout comes before landscape. The layout engine should be prototyped and integrated before the landscape engine.").** Order: prototype the layout engine and get his approval; integrate it (the C layout generator of S-112 to S-119 exists and is tested, but no live mission calls `om_map_generate`, so today's missions have no layout); then the landscape engine, which takes the layout as its input (option A). The layout library is audited and paired with archetypes first (Q-192-04).

- The mask contract and the generators' wiring pieces touch `csrc/tactical_mapgen.c`, movement and fog, which the movement and layers plan owns today: one owner at a time, wiring pieces queued.
- Both generators after the mask contract: a contract change lands first, alone, and consumers build after it. New code goes in new files behind the frozen header (`CLAUDE.md`, Architecture rules).
- Land before space (Westley, 2026-10-03): the land design is further along and space is still in his design loop. Space output is the general form that land is a special case of, so the mask contract is written for both.
- Both generators must use their own deterministic noise in C; the mockups use the engine's noise.
- Economy after a generator: bases, resources and expansion sites are places the generator finds (S-191).
- The landscape batch in the skill lab waits on the guard stance decision.

## 6. Recently finished

| Plan | Doc | Landed | Date |
|---|---|---|---|
| Refuse fix; long-mission suite (`tests/long`, seven seeds, 42 passed); Agora QA holds End Mission, timeouts, 30B plays loops | `plans/2026-10-03-finish-loop-rulings.md`; Agora `wn/qa-director` `3c03883` | `a136e3c0` | 2026-10-04 |
| Finish-the-loop batch: enemy rout and contested objective, commander death ledger, live retention, allowlist, gate setup check | `plans/2026-10-03-finish-loop-rulings.md` | `0d4006fd` (gate on `fd676ea9`: no stage rejected; playthrough 32 passed) | 2026-10-03 |
| MVP loop plays end to end; playthrough stage in the merge gate | `plans/2026-10-03-loop-fix-workflow-brief.md`, report on `push/lf-report` | `465d7145` (gate on `6244dec8`: no stage rejected; playthrough 32 passed, 151 s) | 2026-10-03 |
| Bible rewrite: E-22 added, E-17 terrain-first | `research/epics_audit_2026-10-02/` | `6b8a6c59`, `1fe25028`, `8b5d7d07`, `424055f8` | 2026-10-02 |
| Movement and layers, Phase A (port parity) and Phase C (layers in the engine) | `plans/2026-10-02-movement-layers-and-search-plan.md` | see rulings-2 Addenda 62 to 64 | 2026-10-03 |
| Space landscape mockup, passes 1 to 5 | `research/space_landscape/README.md` | `6c2989ec` | 2026-10-03 |
