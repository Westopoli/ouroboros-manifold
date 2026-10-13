# Audit round1-parallelism (2026-10-07)

The worktree is removed. This is a read-only audit, so I changed nothing in the repo. Every figure below is my arithmetic on the spec's numbers, not a measurement. I assumed one piece costs 1 h in sequence (tests, build, check), a gate takes 0.75 h by day and 0.5 h by night, and 8 agent slots.

## 1. Critical path under the spec's sequencing
- **Chain in pieces (about 25):** GUARD/CONTRACT (K tests, K1, K2, K3, check) → A (tests, builds, A12) → C (C1, C2/C3, C4, C5, C6, C7/C8, C9) → D (D1, D2, D3, D4, D5, D8) → F5.
- **Chain in gates (11):** stage 3, land-1007a, the stale-row clerk, GUARD, CONTRACT, A, C, D, F5, plus the E1 and B gates, which queue but are not on the chain.
- **Total gates:** about 16 to 18 with B0, B-rest, E1, F, the E2 amendment and retries. At 12 a day that is 1.4 days of capacity, so gate throughput is not what binds. Chain latency is.
- **Timeline from T0 (stage 3 and phase A landed), in hours:**
  - CONTRACT lands at about 6.75.
  - A lands at about 11.25.
  - C lands at about 19.
  - D lands at about 25.75.
  - F5 lands at about 28.5, and the story plays finish at about 29.5.
- **Wall clock:** with a 1.25x retry factor (37% of doers stopped in the harness data) that is about 37 h. On a 24 h clock that is about 1.5 days. If the programme only runs by day it is 3.5 to 4 days.
- **Slot count by day:** scout 9 recommends 4 test-running agents by day with the lab at 8 workers. At 4 slots the A/B/E1/F phase doubles to about 12 h.

## 2. Phase table, spec sequencing
| Phase | Hours | Lanes active | Busy / 8 | Idle |
|---|---|---|---|---|
| GUARD + CONTRACT | 0 to 6.75 | 2 | about 3.2 (8 in hour 1, 1 by hour 4) | 4.8 |
| A, B, E1, F | 6.75 to about 14 | 4 | about 7 (48 pieces on 8 slots) | 1 |
| C after A | 11.25 to 19 | C, plus B/E/F tails | about 2.5 | 5.5 |
| D after C and E1 | 19 to 25.75 | D, plus B6..B9 | about 2 | 6 |
| F5 and plays | 25.75 to 29.5 | 1 | about 1.5 | 6.5 |

- Overall utilisation is about 100 agent-hours of work on about 240 of capacity, roughly 40%.
- Only phase 2 is slot-bound. Everything else is dependency-bound, so the cuts below are dependency cuts.

## 3. Pieces to pull earlier, and the dependency to cut
1. **All tests, for every lane, can be written at T0.** They are fenced files that need only the spec's section 2 field names. The test-writing third of every lane (about 26 agent-hours) disappears behind the prerequisite and contract phases.
2. **Contract doc-first gate "K0".**
   - K0 holds the `architecture.md` revision, the header and `signatures.toml` declarations with stub getters, and the bindings. This matches the CLAUDE.md rule that a contract lands documented before implementation.
   - Lane builds start at K0, about 2.75 h, against fixture dicts. Only their landing waits for the contract implementation. The spec says "A builds after CONTRACT" and the lanes need only the frame shapes.
3. **B0 to B5 and B7 need no contract.**
   - They depend on the stacks on `push/A54-*` and `A55-names` plus an 80-region fixture. 8-owners lists no file collision for B.
   - Only B6 (pipe events) needs K2 and only B8 (`scene_router.gd`) needs F.
   - Cut: change `VG-B depends_on` to the contract for B6 only. B can land during the prerequisite and contract window while the gate is otherwise idle.
4. **F build scripts need no contract.**
   - W8a, W8d and the depot script are new files, so they can start at T0 and land early.
   - They feed Westley's human steps (Mac codesign, Steam dashboard, Spacewar match), which are the longest wall-clock items in the programme.
   - Only W5 (F5) and the exe-path/`_setmode` items need K2 and K3.
5. **Lane C: C2, C3, C4, C7 and C8 do not need A.**
   - C2 (ground mesh), C3 (camera rig) and the pick/projection math in C4 are new files that need only the heights fixture.
   - The only real A-dependencies are C5 (edits `tactical_view.gd` and `qa_state`) and C6 (needs A1's shapes).
   - The "C after A" rule comes from the `scenes/tactical_c/**` glob shared with VG-A.
   - Cut: give C and D their own directories (`scenes/ground3d/**`, `scenes/space_field/**`) and make the `VG-C` and `VG-D` rows depend only on K0. A small "view-edit" row then holds the three one-hour edits to `tactical_view.gd` (C5, the D hook, F5), chained after A12.
   - C's post-A chain drops from 7 pieces to 3 (C5, C6, C9).
6. **Lane D does not need C or E1 as a whole.**
   - D7 is 2D top-down in the SubViewport-free shell, so it has no real dependency on C. D1 to D4 are pure C. D8 is tests.
   - D5 is a one-line hook in `mission.c`. It only has to follow E1's single `mission.c` wiring edit, not the whole of E1.
   - Cut: E1's first piece adds an `economy_init/step` hook stub in `mission.c` and `save.c`. Later E pieces then touch only new files.
   - D1 to D3 sit in one `space_field.c`, so they serialise. Split it into `space_noise.c`, `space_plates.c` and `space_raster.c`. The Makefile wildcard makes that free.
7. **F5 does not have to be last.** It is independent of C and D content. Place it right after A12 on the view-edit chain so multiplayer is testable earlier. It is only last because of the owner chain.

## 4. Separation of tasks
- **Same-file pieces that serialise inside a lane:**
  - D1, D2, D3 (`space_field.c`).
  - C2, C7, C8 (the ground mesh), split into mesh, bands and LOD files.
  - E1b and E1c (economy lots and waves).
  - Every E piece that wires into `mission.c` or `unit.c`: one wiring piece, then new files only.
  - A12, C5, the D hook and F5 all edit `tactical_view.gd`. That is four serial gates on one file.
- **Pieces over one file or about 100 lines that should be two or more:**
  - K1: 17 getters across lanes, so split by lane group.
  - K2: roughly eight changes in `om_pipe.c` (dead-slot fix, `_setmode`, `net_step`, frame fields, events, profiles, three verbs, doc). Split into K2a (dead-slot fix, `_setmode`, `net_step`), K2b (frame fields) and K2c (verbs and dumps). Extracting `write_tactical` and the dumps into new files first lets them run in parallel.
  - K3.
  - A1 (shapes, scale, tier, tint, ring and facing), A3 (rings, dimming, strip and order input), A5 (cover, obstacles, zones, boundary, beacons and rings), A7 (selection, groups 1..9, group bar), A8 (ticker, banner and clock), C5 (touches 3 files), D3 (rasterise and carve), E1b to E1e, E1g.
- **Ownership gaps and duplicates to fix before launch:**
  - K4 puts `csrc/save.c` in the contract, but VG-E owns `save.c` and E1j also bumps the format. Move K4 into E1j.
  - C1 and K3 both decode heights. D6 and K3 both decode `space_field`. E1f is in both the contract and E1. Each should be one piece.
  - Fire events and `om_structure_*` need getter bodies in C files that VG-CONTRACT does not own. `csrc/tactical_events.c` belongs to VG-A, and 8-owners marks "does event emission touch `mission.c` or `unit.c`" as unverified. If it does, A and E serialise.
  - The spec names `csrc/space_field.c` but the owner row says `csrc/space_kit.c`.
  - E1i (ticker beats) overlaps A8's `events_feed.gd`. Make it a new file feeding A8.
- **Tests and build by the same agent:**
  - The spec does not imply this for A, B, C, D or F, whose tests are in separate columns.
  - Four places are ambiguous. G1 to G8 are "Engineer-owned" with no separate test writer (a second Engineer is needed). The E1 list says "tests per piece" inside the build list. A12's element-inventory test is inside the shell piece. C9 and D8 bundle the story plays, which are tests, with builds.
- **Budget:** the spec lists about 79 pieces (guard 8, contract 5, A 12, B 11, C 9, D 8, E1 18, F 8), but the 52M expected budget was computed for 50. At 0.707M per piece plus clerks and retries that is about 68M against a 75M ceiling. Restate the budget.

## 5. Contract wave: split or not
- **K1+K2 then K3+K4, as asked:** it adds one gate (about +0.75 h of queue) but shortens the lane-visible wait. A, B, E1 and F need frame shapes and pipe behaviour, not the bridge.
- **Which pieces need K3:** C1, D6 and E1g (heights, space field and lots wrappers). Frames pass through the bridge unchanged.
- **K4:** it belongs to E, so it is not part of the split.
- **A failed combined gate is more costly.** A K1+K2+K3+K4 gate carries csim, transport, Godot and save pins in one candidate, and the kill rule stops the run after two contract rejections.
- **Recommendation: three gates.** K0 is doc, header and stubs (about 20 min). The pipe implementation (K2a to K2c) follows. The bridge (K3) comes last. That is one more gate than the spec, but it unlocks lane builds at about 2.75 h instead of 6.75 h.

## 6. Clerks
- **Landings:** the spec has GUARD, CONTRACT, A, B, C, D, E1, F and F5, which is nine, not eight. B0 plus the rest of B makes ten.
- **Sharing windows:** disjoint, both-green lanes can land in one candidate. Good pairs are B with F build scripts, and E1-sim with D-sim (sequence the two `mission.c` hooks inside the candidate). That saves 2 to 3 gates (about 1.5 to 2 h of queue) and about 1.5M eq of clerk polling.
- **Do not share GUARD.** It changes the gate itself, so land it alone and let the next gate exercise it.
- **GUARD:** G1 to G4, G6 and G7 are independent and land first. G6 (baseline capture of every current screen) must precede any lane landing. G5 waits on Agora relays and G8 waits on nothing, so both can land late.

## 7. The lab
- **Contention:** csim (276 to 382 s) and playthrough (Godot import up to 300 s plus about 160 s) contend with lab workers. specfactory contends less. The gate has no lab stage, so the contention is on CPU only.
- **Evidence:** skilllab slowed 1.74x (741 to 1288 s) under contention, and gates go from 30 to 40 to 45 min.
- **Run 1 (about 68 min at 12 workers):** pin it to a night slot, or to the build window right after K0, when no gate is running.
- **By day:** run the lab at 4 workers, and give gates priority via `CPUWeight`.

## 8. Recommended re-sequencing
1. At T0, start all tests, GUARD (G1 to G4, G6, G7), B0 to B5 and B7, the F build scripts, and D1 to D4, D7 and D8.
2. Land K0 at about 2.75 h, then start the lane builds against fixtures.
3. Run K2 and K3 in parallel with the lane builds.
4. Land order after the contract is A, then the other lanes' sim pieces, then the view edits (C5, the D hook, F5).
5. Land pairs where files are disjoint.

**Estimated wall clock, T0 to the story plays done:**

| Plan | At 8 slots | With retries (1.25x) |
|---|---|---|
| Spec sequencing | about 29.5 h | about 37 h |
| Re-sequenced | about 14.5 h | about 18 h |

The re-sequenced plan is limited by work volume (about 100 agent-hours on 8 slots, floor about 12.5 h) plus a 3 to 4 h view-edit tail. At 4 slots by day the work floor is about 25 h.
