# Roadmap

Last updated: 2026-10-18 (Architect): section 1 gains the sim lane pieces, the two mockups and the probes; section 2 step 6 macOS done; section 3 points at the decision pack; 3b T5 to T9, T18 restated, T19 added. Before that, 2026-10-07: section 2b added, the order of work after the beta workflow (Westley).

What is being built now, what is built next, and in what order. `PLAN.md` is the method; this file is the order. One row per plan.

Rules for this file:

- Rewrite, never append. History is `git log`.
- A row points to a plan doc and never restates it. No design text here.
- A plan enters "Queued" only when it has a doc path. An idea without a doc goes in "Not planned yet".
- Whoever starts, finishes or reorders a plan updates this file in the same commit.
- File ownership stays in `plans/push/pieces.toml`. Open questions stay in `ambiguity_register.md`. Rulings stay in `plans/2026-10-01-architect-rulings-2.md` and, for the programme, in the spec's `[W ...]` tags.
- Lane status lives in one place, the lane table of `plans/2026-10-07-visible-game-programme.md`; this file never copies it.

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

Shots waiting for a verdict (no scene to run, open the files): `docs/northstar/story_reviews/westley/`, one plainly named png per pending row and a README that maps each to its queue row. Section 3 "Now" names the six that matter.

Two folders hold what can be viewed:

- `~/Projects/om-push/wt/view-main`: current main, already imported. Refresh it before viewing anything new on main:
  `cd ~/Projects/om-push/wt/view-main && git fetch -q origin && git checkout -q --detach origin/main && ~/.local/bin/godot.real --headless --path . --import`
- `~/Projects/om-push/wt/proto-land-iter`: the land mockup's working copy (branch `push/proto-land-iter`), ahead of main.

If a scene prints "Could not find type" errors, the folder has not been imported since new scripts arrived: run the refresh line (or the same `--import` in that folder).

| Prototype | Command | State | Record (keys and open questions) |
|---|---|---|---|
| Layout mockup, pass 1: the flat diagram | `cd ~/Projects/om-push/wt/proto-layout && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/layout/layout_mockup.tscn` | Reference only: Westley 2026-10-06, the layout engine needs no prototype; the lab's layout search supplies the data | `research/layout_engine/README.md` section "Pass 1"; spec `plans/2026-10-04-layout-prototype-pass1-spec.md` |
| Land mockup, latest: the layout shapes the terrain | `cd ~/Projects/om-push/wt/proto-land-iter && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/landscape/landscape_mockup.tscn` | Pass 6b approved 2026-10-05 and 10-06 ("Landscape engine is also approved"); integrated as terrain stages 1 to 3 and lane C | `research/landscape_design/README.md` on branch `push/proto-land-iter`, sections Pass 4 to Pass 6 |
| Walkers and flyers on generated land | `cd ~/Projects/om-push/wt/proto-walkers && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/walkers/walkers_mockup.tscn` | Pass 1 approved final 2026-10-06; integrated in terrain stage 2 and lane C. Keys: F1-F3 seeds, B speed, G slope slows, C flyer climbs, 1-5 flyer layer, V view | `research/walkers/README.md` |
| High ground worth (chart, open the file) | `xdg-open ~/Projects/om-push/wt/proto-highground/docs/northstar/research/layer_dynamics/runs/2026-10-05_highground/highground_page.html` | 2026-10-05; a space-mechanics stand-in | `plans/2026-10-05-proto-highground-spec.md` |
| Land mockup as on main | `cd ~/Projects/om-push/wt/view-main && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/landscape/landscape_mockup.tscn` | Passes 4 and 5 | `research/landscape_design/README.md` |
| Space kit (same scene: press the Kit button until it reads space) | `cd ~/Projects/om-push/wt/view-main && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/landscape/landscape_mockup.tscn` | Pass 6 approved 2026-10-06 (vision-tube note Q-S3-01); lane D, held on the routed answers | `research/space_landscape/README.md` |
| Settlement mockup: a base that builds itself | `cd ~/Projects/om-push/wt/view-main && ~/.local/bin/godot.real --path . --display-driver x11 --rendering-driver opengl3 res://scenes/mockups/settlement/settlement_mockup.tscn` | Pass 1 approved 2026-10-06; its look is now built in the game by lane E (E1k), with a banded-contour prototype queued after it | `research/settlement_mockup/README.md` |
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

Branches only; main gets a piece only through the merge gate. Method rev 2 (`plans/retro_2026-10-10/README.md`): a Sonnet Dispatcher runs the programme, the Architect is on call by brief, every lane lands a skeleton with a shot before it fans out.

| Plan | Doc | State (2026-10-13) | Next |
|---|---|---|---|
| **The visible game programme**: every approved prototype into the game, the economy play, Steam phase B; stories acted out as the acceptance | `docs/northstar/plans/2026-10-07-visible-game-programme.md` (lane table = status), spec `plans/2026-10-07-visible-game-spec.md` rev 12f on `push/vg-kp-lots-spec` | IN FLIGHT since 2026-10-07, method rev 2 since 10-10; six lanes A to F plus contracts, harness and W walk routes; about 120 pieces landed, 0 stories Seen; every lane's second look (after the method fix) is in section 3 "Now" | lanes advance on Westley's verdicts; the record batch `push/vg-rec-12e` lands, then spec rev 13 (provenance tags) |
| Simulation viewer and the simulation lane (ROADMAP 2b step 1, started early) | `plans/2026-10-12-simviewer-plan.md`, `plans/2026-10-12-sim-lane-context.md` | SV-1 to SV-3 landed (d7d01f40); first findings pass run 2026-10-15 on the Mac: 17 ledger rows in `plans/sim_lane_2026-10-12/README.md` (mission swaps, opening relevance 0, chronicle family and chain entries missing, blank shells, 37 ALG rows untested) | Westley reads the ledger; `Q-` rows for rows 3, 10, 13; SV-0 and the pipe gaps queue behind VG-CONTRACT-E7 |
| Space lab: layout search | `plans/2026-10-06-layout-search-spec.md` rev 4 | run 1 landed a9ee5897; chart waits on Westley (`research/layer_dynamics/README.md` open list) | run 2 after the category table; the ground lab spec |
| Walk-route fix piece (`FINDING-walk-route-replan`) | none yet | W1 planner landed 6621ef96 (600-walker tick 64 ms to 10 ms); W2 stored routes queued (save 10 to 11, contract piece) | W2 builds; the fix piece is specced after W2's report |
| Sim lane pieces: SIM-LOGS, then the call sites, then chronicle.c rows 7 to 9, then CHRON-CONTEXT | `plans/2026-10-15-sim-logs-spec.md` rev 4 (three Sonnet audits spent); `sim_lane_2026-10-12/README.md` ledger | specced; W1, W2, W4 and the second-Fable audit route in the decision pack (B1 to B5); ring and append tests being written on the Mac 2026-10-18 | Westley's W rulings; Linux for the gate; CHRON-CONTEXT specced from the 2026-10-18 scout |
| Transition mockup, S-108 (prototype gate) | `plans/2026-10-15-transition-mockup-spec.md`; `push/proto-transition` 5537d3cb | pass 1b built on the Mac, 27 tests green; shots in `story_reviews/westley/` | Westley's verdict (pack B14); on approval an integration lane row here (guard 4) |
| Terrain obeys the layout, S-191 and S-189 (prototype gate; lane P rev 6 follows it) | `plans/2026-10-15-terrain-obeys-mockup-spec.md`; `push/proto-terrain-obeys` 804f666b | pass 1 built on the Mac: pads, choke and vantage produced and measured; routes not, the engine must carve them | Westley's verdict (pack B15); pass 2 with route carving; lane P rev 6 from its facts |
| Sim viewer probes and the offline runner | `scripts/simviewer/probes/` (03cd9502) | landed 2026-10-18; `offline_run.sh` runs the two sweeps, the csim suite and a lab layout-search batch unattended | results read after the offline window |
| Steam shipping, steps 6 to 8 of section 2 | `plans/2026-10-06-steam-multiplayer-wiring-spec.md` rev 6 | phase A landed e63483f6; phase B is lane F (skeleton lobby and net first tick on main); mingw-w64 and wine64 installed 2026-10-06 | per-OS pipe build after lane F's tactical hookup |

Landed and closed since the last rewrite: terrain stages 2 and 3 (008de465, 0304d821), Steam phase A (e63483f6), the programme guard pieces (reach lint, lane plays, play split, daemon verb), the harness pieces of method rev 2 (pre-gate, status check, journal, provenance lint), unit scale (53ede72), the Sonnet briefs B1 to B11 (their branches `docs/method`, `docs/military-doctrine`, `docs/era-pack-form`, `docs/map-design-pillars` wait on Westley's reading, section 3b).

## 2. The beta critical path

Target: a private Steam beta with multiplayer and every approved prototype integrated. Westley 2026-10-07: no date; "done right than fast"; efficiency, parallelism and no drift are the measures. Steps 1 to 5 are carried by the programme; this table keeps the Steam-side steps.

| # | Step | State (2026-10-13) | Gate | Then |
|---|---|---|---|---|
| 1 | Terrain stage 2 on main | landed 008de465 (2026-10-07) | done | |
| 2 | Terrain stage 3: missions on ground, the player sees it, era toggle | landed 0304d821; the 3D ground is lane C | done; lane C's looks in section 3 | 5 |
| 3 | Unit size as a runtime setting (D1) | superseded for the programme by `VG-C-unitscale` (53ede72, body 11.5 / shadow 10 wu); the lab's per-type sizes follow the era rosters (3b T13) | | lab run 2 |
| 4 | Steam wiring phase A | landed e63483f6 | done | 5 |
| 5 | Steam wiring phase B: pipe frame flag, bridge wrappers, lobby, tactical hookup | lane F: skeleton lobby (dbe480a) and net first tick (b12b47a) on main; S-141 reviewer yes, S-140 unclear, both pending Westley | gate plus a two-process loopback match (S-141, S-142 green) | 6 |
| 6 | Shipping the C pipe on Windows, macOS, Linux (static pipe per OS, mingw-w64 cross build, client path fix, signing) | Windows: first probe matched byte for byte under wine (2026-10-06). macOS: done 2026-10-18 on the Mac, `scripts/build_pipe_macos.sh` static ad-hoc-signed pipe, full checksums equal the Linux pins at ticks 100 to 2000 (`plans/2026-10-18-macos-pipe-probe.md`); notarisation and a signing identity are Westley's | a build per OS runs the probe and matches checksums (Q-NET-05) | 7 |
| 7 | First real-Steam test: Westley's two accounts on Spacewar 480, Linux + Mac | after 5 and 6 | a match to its end, a stall, a leave | 8 |
| 8 | Beta build on Westley's app id, Dev Comp keys, tester guide (`docs/northstar/beta/`) | guide and store copy drafted; app id is Westley's (3b T17) | one tester plays a mission and files an F12 report | public track |

## 2b. After the beta workflow completes: verification, polish, next features (Westley, 2026-10-07)

Step 1 has its plan and spec now: `plans/2026-10-12-simviewer-plan.md` (pieces SV-0 to SV-3, owner rows on main) and the simulation lane context `plans/2026-10-12-sim-lane-context.md`; Westley opens that lane as its own chat. It runs beside the programme, not after it (Westley, 2026-10-12: "I've been meaning to double check on the simulation system anyway").

Three steps, in this order. Step 1 and step 2 run at the same time; step 3 starts when step 2 is finished. Building new features stops for the length of step 2.

1. **Verify the simulation still follows the stochastic rules written into the bible** (`docs/bible/algorithms.md`). The legacy Python version had a small viewer, built on a Python game library, showing the regions on a 2D plane, how they are exchanged as ticks pass, which events fired, what the simulation chose for each mission and how much time passed each time (`simulation/run_strategic_viewer.py` and `simulation/strategic_viewer.py`, pygame). The goal is to find regressions in the core of the game: mission choice, and the source of the chronicle. The viewer is `scripts/simviewer/` (spec `docs/northstar/plans/2026-10-12-simviewer-spec.md`).
2. **Pause new features until the existing ones are relatively perfected.** Westley gives feedback on each aspect of the game, a change is made, and he checks it again, repeated. Only when this is finished is the game ready for Steam posting.
3. **Assess the lay of the land** for prospective and unimplemented features and decide what to build next. Contrast the old ideas in the bible and the roadmap with the user feedback received, and prioritise between them.

## 3. Blocked on Westley

Every decision waiting on Westley, in the order that unblocks the most work. Candidates for each `Q-` flag are in `ambiguity_register.md`. An answer is recorded in the register and the epic, and its row is deleted here.

### Now (the 2026-10-18 batch; the six-row cap is suspended for it, Westley 2026-10-18)

Everything waiting on Westley is in one pack: `plans/decision_pack_2026-10-18/README.md` (how to answer; what each answer unblocks on the Linux box this week), with its appendices: the shots in `story_reviews/westley/` (one row per file in its README), the Architect's rulings of the week (B1 to B19 in the pack), the register extract (`register_extract.md`, every open flag grouped, full text), and the five doc branches digested (`doc_branches_digest.md`). After the batch the Dispatcher rebuilds this table at six rows or fewer from what is left.

Closed since the last rewrite: Q-191-14 (b), Q-191-05, Q-191-08/09/10, Q-188-01, Q-189-04, Q-082-06 (2026-10-15, Westley); Q-NET-05 measured on the Mac 2026-10-18 (`plans/2026-10-18-macos-pipe-probe.md`), its closing is pack item B12.

### Parked questions (not asked until the work before them is reached)

| Group | Items | Reference | Asked when |
|---|---|---|---|
| Finishing the MVP loop (scouts, 2026-10-03) | F1 event-threshold noise, F3 chronicle wording for a fallen faction and a dead commander, F4 campaign end over the pipe, F5 enemy hooks, F6 transition durations, F8 who consumes a faction's phase, F10 regional commander on conquest, F11 two functions against their rule, F12 objectives for four archetypes (red tests on `push/obj-tests`), F13 retention membership. F2, F7 and F9 are closed in the register (Q-062-01, Q-120-03, Q-056-01) | `plans/2026-10-03-finish-loop-rulings.md` "Westley" | the simulation lane (2b step 1) reads them first; the sim viewer makes F1, F3, F4, F10 visible |
| Land generator | L1 smallest readable layer step and "unreasonably hard to reach" (Q-188-01, Q-189-04); L3 the places' figures (Q-191-05); L9 the land era's name and scope (Q-147-01) | register | lane C's second era; the places (section 4) |
| Space generator (parked, A207) | S1 to S4: kit pass, small-craft size, camera among sheets, shared density | Q-166-02, Q-166-05, 3b T3 | lane D resumes |
| Movement, layers and search (parked, A209) | M1 to M10: pass marks, variant B, leash, scattered-group rule, guard stance, fling, scale suite, fight length, height bands | rulings-2 A174 to A199; Q-087-01, Q-096-01, Q-097-02, Q-166-04 | after the lab's data (layout search run 2) |
| Balance and housekeeping | B1 rates for the balance simulation; B2 E-17 reds; B4 constants promotion, snapshot fixture policy, generation budget at 400 regions (Q-224-01) | rulings-2 | the simulation lane |
| Economy and bases, open flags | Q-159-07 to -13, Q-167-01 to Q-181-02, Q-177-01 to -05, Q-178-01 to -05, Q-168-06, Q-193-04/05/07/08/09, Q-219-04, Q-E1-01 to -03 | register, E-22 and E-17 | lane E asks each as its piece reaches it, with a shot |
| Multiplayer | Q-144-03 who hosts the next sitting of a locked universe | register | lane F's lobby piece |

## 3b. Parallel work (the TODO list)

Work that does not wait on the build lanes. Written 2026-10-06 from Westley's list; states as of 2026-10-13.

| # | Item | State | Next mover |
|---|---|---|---|
| T1 | Settlement mockup pass 1 and its answers (Q-193-01 to -06) | done 2026-10-06; folded into lane E's spec (E1 part c and E1k) | lane E |
| T2 | Space landscape pass 6 approved; S1 to S4 to fold | approved 2026-10-06; folding waits on lane D's resume | Architect, when D resumes |
| T3 | Camera options page for space (five opaque sheets) and Q-103-04/05/06, Q-232-01 | not drafted | Architect, with lane D |
| T4 | Sense-of-scale prototype (Sand Table, Q-103-05, Q-234-01 c) | not built; the 3D ground on main (lane C) is where scale is first seen | after lane C's looks are Seen |
| T5 | Methodology write-up | drafted on `docs/method`; digested in the decision pack (`doc_branches_digest.md`): land after edits (rev 2 roles, pre-gate, guards) | Westley's a/b/c in the pack; then the re-draft |
| T6 | Map-design pillars | both branches are already ancestors of main (`research/map_design/`); the pillars page asks Q-MAP-01 to -05, not yet in the register; digested in the pack | Westley answers Q-MAP-01 to -05 in the pack; the clerk adds the rows and retires the two branches |
| T7 | Military-strategy research synthesis | drafted on `docs/military-doctrine`; digested in the pack (land as is, one cross-reference re-check) | Westley's a/b/c in the pack |
| T8 | Website refresh (`~/Projects/ouroboros-site`): galaxy view, the two landscape engines, the walking prototype, `/method` | S-106 Seen 2026-10-13; a draft branch `refresh-2026-10-18` is being built in the site repo (no deploy) | Westley reads the draft; publish is his |
| T9 | Era pack form for 20+ eras | drafted on `docs/era-pack-form`; digested in the pack: the era-kind row is wrong (Q-146-04 closed), the doctrine and building rows are stale (E1f, E1g), S-147/S-151 of 2026-10-15 missing | Westley's a/b/c in the pack; a clerk applies the named edits |
| T10 | Cosmetics and art direction | nothing past placeholders; Westley needs example choices to pick from | after the beta's looks are Seen (2b step 2) |
| T11 | Economy look mockup | superseded: lane E builds the settlement look in the game (E1k) and a banded-contour prototype after it (`PROTO-settlement-banding`); the economy screens (S-230 to S-235) are lane E pieces | lane E |
| T12 | Flaky playthrough click `test_s_c8_09`, root cause | the gate's flake re-run (G1) masks it; root cause not found | Engineer, `investigate` brief, after the programme's harness pieces land |
| T13 | Body size per type from the runtime collision radius (Q-LAB-02 a) | unit scale on main for the client (`VG-C-unitscale`); the sim's per-type radius follows the era rosters | lab, with the rosters |
| T14 | Fight tick cap 12,000 and never-engaged fights not read as ties (Q-LAB-01) | cap raised (brief B2); outcome classes not yet recorded | lab spec |
| T16 | Feedback and bug reports: in-game F12 capture, website feedback, classification | piece built 2026-10-06, awaiting its gate; the lockstep save it replays through is lane F | after lane F's tactical hookup |
| T18 | Branch triage (second audit done 2026-10-15, `plans/branch_triage_2026-10-15/`: 250 proven landed, 127 not proven; delete is pack item B11): 225 unmerged `origin/push/*` branches of 09-22 to 09-24 (B1 to B15m, C1 to C8, T1, F2, HDR, INV) and old tooling branches, nothing deleted; Westley 2026-10-15 chose (c): delete only what a second audit proves landed by another route | report in this chat 2026-10-15; second audit not run | Engineer, a second audit that proves each branch's patches landed by another sha before any deletion |
| T19 | Layout library audit against the lab's layout search (section 4 row 1) | being written 2026-10-18 (`research/layout_engine/library_audit_2026-10-18.md`) | Westley's pairing answers join the next pack |
| T17 | Steam onboarding, public track (app fee, tax and identity, Coming Soon page) | Westley by hand; no report yet | Westley |

## 4. Not planned yet

Decided or partly decided in the bible, with no plan doc. Groups that entered the programme are gone from here (settlements, economy and bases, zoom and drawing, strongpoints and weather are lane E and C pieces; the layer mask is the terrain contract).

| Group | Stories | Epic | State | Why parked |
|---|---|---|---|---|
| Layout library audit and archetype pairing | none | E-17, E-10, E-21 | Not written | Westley 2026-10-03: the eight old layouts (`simulation/layout_library/`) predate the game's change; audited against the lab's layout search before any pairing |
| Land generator, part 2: the places | S-187, S-191, S-192, S-195, S-197, S-200, S-201, S-207, S-221 | E-17, E-01, E-11, E-13, E-02 | Design decided; towns rulings 2026-10-13 (R-191-06, R-193-01, R-177-02); spec next (Architect), launch on Westley's go | The lane that builds economic locations, neutral towns grown to a seeded age, resources and the base kinds in the sim; lane E's settlement look follows it |
| Space generator in C | none in the bible yet | E-17 | Mockup pass 6 approved; lane D holds the sim side (D2 to D8 on main) | Waits on S1 to S4, the space stories, lane D's resume |
| The land era's identity and the era roster | S-147, S-151 | E-20 | Both packs exist (Settled Reach; Greek placeholder "The Marble Reach", reached by the era toggle); Q-147-01 open for the name, brief and ordered roster; the era pack form (3b T9); S-151's values come from the lab's crossings | Design, not build: Westley writes the brief and roster; the Climate of War values wait on the lab reporting more than one crossing |
| Cross-epic follow-ons | S-220, S-223 to S-228, S-239, S-241 to S-244 | several | Q-220-01/02, Q-224-01, Q-225-01/02, Q-226-02, Q-227-02/03, Q-228-01/02 open | Each follows its parent group; the simulation lane reads the sim-side ones |
| Port parity P4, map content | none | E-17 | Held | Waits on the generator design |

## 4b. Prototype state

Per `agile.md`, Prototype gate. A group marked "needed" is not planned until its prototype is approved. Integration state is the programme's lane table.

| Group | Prototype | State |
|---|---|---|
| Land generator | Mockup `scenes/mockups/landscape/` | Approved 2026-10-06; integrated (terrain stages 1 to 3, lane C) |
| Walking and flying units on land | Mockup `scenes/mockups/walkers/` | Approved final 2026-10-06; integrated (terrain stage 2, lane C, lane W routes) |
| Galaxy | `push/galaxy-field` | Look approved 2026-10-07; integrated by lane B (B22, B23); the second look is in section 3 |
| Settlements | Mockup `scenes/mockups/settlement/` | Pass 1 approved 2026-10-06; integrated by lane E (port E1q, look E1k); a banded-contour prototype is queued after E1k (`PROTO-settlement-banding`) |
| Space generator | Mockup, space kit mode | Pass 6 approved 2026-10-06 (vision-tube note Q-S3-01); lane D held |
| High ground worth | Instrument `scripts/skilllab/highground.py` | Built 2026-10-05; a space-lab result, fate open |
| Movement and layers | Instrument, skill lab | Phase D pages; pass marks open (M1) |
| Economy and bases, rules | Instrument, needed | None exists; the number flags are asked piece by piece in lane E |
| Economy and bases, look | In the game, not a mockup | Lane E (E1k, the economy screens); Westley judges shots per piece |
| Layout engine | No prototype (Westley 2026-10-06) | The lab's layout search supplies the data; `push/proto-layout` is reference only |
| Mission-to-galaxy transition (S-108) | Mockup `scenes/mockups/transition/` on `push/proto-transition` | Needed (Westley, 2026-10-15); spec `plans/2026-10-15-transition-mockup-spec.md`; a Doer builds it on the Mac |
| Multiplayer lobby | Mockup needed for the lobby screens | Lane F's skeleton lobby (S-141 shot) stands in; Westley's verdict pending |
| Simulation | The sim viewer (2b step 1) | Specced 2026-10-12, not built |

## 5. Dependency notes

- **Layout before landscape (Westley, 2026-10-04, verbatim: "layout comes before landscape. The layout engine should be prototyped and integrated before the landscape engine.").** Order: prototype the layout engine and get his approval; integrate it (the C layout generator of S-112 to S-119 exists and is tested, but no live mission calls `om_map_generate`, so today's missions have no layout); then the landscape engine, which takes the layout as its input (option A). The layout library is audited and paired with archetypes first (Q-192-04).

- The mask contract and the generators' wiring pieces touch `csrc/tactical_mapgen.c`, movement and fog, which the movement and layers plan owns today: one owner at a time, wiring pieces queued.
- Both generators after the mask contract: a contract change lands first, alone, and consumers build after it. New code goes in new files behind the frozen header (`CLAUDE.md`, Architecture rules).
- Land before space (Westley, 2026-10-03): the land design is further along and space is still in his design loop. Space output is the general form that land is a special case of, so the mask contract is written for both.
- Both generators must use their own deterministic noise in C; the mockups use the engine's noise.
- Economy after a generator: bases, resources and expansion sites are places the generator finds (S-191).
- The guard stance is ruled (R-096-08, 2026-10-13); the landscape batch runs on the built guard until the step-and-return engine piece lands.

## 6. Recently finished

| Plan | Doc | Landed | Date |
|---|---|---|---|
| Restart point 400k context; ROADMAP rewritten; galaxy density and S-132 shots committed for Westley | CLAUDE.md, `workflows_2026-10-07/`, `story_reviews/westley/2026-10-13/` | bb30cd9c, 7ccc8dbe, 26cdb319 | 2026-10-13 |
| Sim viewer spec SV-0 to SV-3 and owner rows; the simulation lane context | `plans/2026-10-12-simviewer-plan.md`, `plans/2026-10-12-sim-lane-context.md` | dc7da0ac, c4d3d939, c7961d75 | 2026-10-12 |
| Programme landings of 2026-10-11 to 10-13: K-e5/K-e6 contracts, settlement port E1q, F-SKEL lobby, F-NETTICK, K-d1, A16, A17, VG-C-unitscale, VG-B23b dot colour, S-004 play fix, W1 planner | `plans/2026-10-07-visible-game-programme.md` lane table | `scripts/journal.sh` | 2026-10-11 to 13 |
| Retrospective and method rev 2: Sonnet Dispatcher, Architect on call, skeleton first, pre-gate, tests on the built tree, method check at every compaction | `plans/retro_2026-10-10/README.md`, `workflows_2026-10-07/dispatcher.md`, `method_check.md` | 393a1d04 and the rev 9 spec | 2026-10-10 |
| Programme stage 3 under method rev 1: lanes A to F first pieces (98 planned plus 37 unplanned), guard pieces (reach lint, lane plays, play split, daemon verb) | programme file, `retro_2026-10-10/` | fc986411, 7bb1f5a2, f37a926f and the lane table | 2026-10-07 to 10-10 |
| Terrain stages 2 and 3; Steam phase A | `plans/2026-10-06-terrain-stage2-spec.md`, `-stage3-spec.md`, `2026-10-06-steam-multiplayer-wiring-spec.md` | 008de465, 0304d821, e63483f6 | 2026-10-06 to 07 |
| Refuse fix; long-mission suite; Agora QA plays loops | `plans/2026-10-03-finish-loop-rulings.md` | a136e3c0 | 2026-10-04 |
| Finish-the-loop batch; MVP loop plays end to end; playthrough stage in the gate | `plans/2026-10-03-finish-loop-rulings.md`, `plans/2026-10-03-loop-fix-workflow-brief.md` | 0d4006fd, 465d7145 | 2026-10-03 |
| Bible rewrite: E-22 added, E-17 terrain-first; movement phases A and C; space landscape passes 1 to 5 | `research/epics_audit_2026-10-02/`, rulings-2 Addenda 62 to 64, `research/space_landscape/README.md` | 6b8a6c59, 1fe25028, 8b5d7d07, 424055f8, 6c2989ec | 2026-10-02 to 03 |
