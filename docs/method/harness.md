# Harness stories

Work on the method or the tooling. Same columns as `docs/bible/stories.md`, same loop, same trailers; the story file is `docs/stories/H-###.md`; the gate flag is `harness`. The nightly timers (play, sweep, token report) run from the clone `~/Projects/om-push/main` and are installed with `systemctl --user link <unit path>` then `enable --now`.

| Story | In Westley's words | Status | Depth |
|---|---|---|---|
| H-001 | "I type one command and today's main opens, built, in front of me; with a story id it opens at that story's scene." | Tested | `docs/stories/H-001.md` |
| H-002 | "One command prints what is in flight, what landed this week, what waits on me and the four numbers, from git alone." | Tested | `docs/stories/H-002.md` |
| H-003 | "Every night the token report writes the four numbers for the week, and the share of spend that went into building and testing is the first of them." | Tested | `docs/stories/H-003.md` |
| H-004 | "Every night the 30B plays today's main through the same command I use and what it finds shows up as harness stories, never as edits." | Tested | `docs/stories/H-004.md` |
| H-005 | "The method check after a compaction tests six rules against the chat's transcript and cites this directory, not the retired documents." | Tested | `docs/stories/H-005.md` |
| H-007 | "The 30B plays the nightly session itself, through the QA port, instead of the game sitting open." | On hold (Westley 2026-10-30) | no story file yet |
| H-006 | "The gate reads the story's flag from the story file and the merge message; it needs no pieces row and no owner table, so a story branch lands by itself." | Tested | `docs/stories/H-006.md` |
| H-008 | "The simulation lab finds where the lines cross; it is finished when the crossings are documented." | Spec'd, waits on Westley's read | `docs/stories/H-008.md` |
| H-014 | "The full suite runs on main by itself after three landings, two hours, or nightly, and writes its row; I never ask for a sweep." | Tested | `docs/stories/H-014.md` |
| H-015 | "A red sweep finds the landing that broke it by bisecting and reverts it with a Finding trailer." | Spec'd | `docs/stories/H-015.md` |
| H-016 | "The cache seed after a push actually seeds: it reads the candidate results stored under the gated sha." | Tested | `docs/stories/H-016.md` |
| H-017 | "A change under csrc runs the pinned csim tests before the push." | Tested | `docs/stories/H-017.md`; pins step exercised by the builder's real-tree run only; first csrc landing proves it |
| H-018 | "The pins warning tells stale pins from never-pinned tests." | Landed 9ab8a5eb | `docs/stories/H-018.md` |
| H-019 | "The gate's csim baseline cache survives docs-only commits on main because each suite declares only what it reads." | Tested | `docs/stories/H-019.md` |
| H-020 | "The gate's own toy-repo tests carry a story file like every real candidate, so a sweep of main is green again, and the landing that fixes a red sweep's tests may pass the sweep check it is fixing." | Tested | `docs/stories/H-020.md` |
| H-021 | "A red sweep row never blocks the next sweep: the slow tier reports the row as a warning and runs the suite that can replace it." | Tested | `docs/stories/H-021.md` |
| H-022 | "The csim xdist gate tests carry a story file and the tier they mean, like the rest of the toy gates." | Tested | `docs/stories/H-022.md` |
| H-023 | "a prototype to show unit scale in comparison to several 'strategic positions', with metrics for me to be able to understand how big each individual unit will be relative to other landscape pieces and buildings/cities and strategic positions, before we run the simulation engine with locked in unit scales." | Tested; unverified: viewport capture; re-prove under H-031 | `docs/stories/H-023.md` |
| H-024 | "a prototype full fidelity 60fps visual of a match vs what the screenshots at a specific configuration look like, then when I see the comparison I can effectively rule on timing" | Spec'd | `docs/stories/H-024.md` |
| H-025 | "Layouts are mass-produced from the recorded rules, each with a 3D shot and a predicted verdict, and Westley approves or denies each one with feedback; only approved layouts reach the lab." | Tested; unverified: viewport capture; re-prove under H-031 | `docs/stories/H-025.md` |
| H-026 | "`wt.py new --branch <b>` fails with an empty \"git worktree add failed:\" when a finished worktree still has that branch checked out; it should say so (`branch <b> is checked out in <path>`) and, for a finished tree, offer `wt.py reap` or detach (found 2026-10-30 by the H-023 builder)." | Ready | none yet (`wt-branch-flag`) |
| H-027 | "`desktop-test-import`: a fresh worktree needs `godot --import` before a desktop (.py qa) story test passes, and that import leaves .import and .uid noise that pre_gate rejects; pre_gate (or play.sh --check) should run the import in a scratch copy or accept the import's outputs as build outputs (found 2026-10-30 landing H-023; the clerk used a second tree with .godot copied in). H-035 closes the gate half: merge_gate.sh now imports for any tests/qa/ id or any acceptance file mentioning daemon_client or GodotGame; the desktop test import noise at pre_gate stays open." | Ready | none yet |
| H-028 | "a working, stable, beta version of the game always available for me to open and mess around with." | Held behind H-031 | `docs/stories/H-028.md` |
| H-031 | "A launched scene is proved visible the way Westley sees it: the window is mapped on his desktop and a real capture of the screen shows it, or the proof says unproven." | Tested; pieces one (60479600) and two (play.sh 1919x1080, portal screen capture, play proof) landed; Westley's desktop run of the Done-when check pending; the game-side fix is H-038 | `docs/stories/H-031.md` |
| H-032 | "Every line pre_gate.sh prints starts `PRE_GATE <step>`, as its header says, so the pre-gate's own clean-repo test is green on main again." | Tested | `docs/stories/H-032.md` |
| H-033 | "The nightly play files what it found as harness rows on a branch every night; a finding never dies in the timer's journal." | Tested | `docs/stories/H-033.md` |
| H-034 | "A sweep that cannot finish still writes its row, so a red or broken sweep shows in the status and never passes as silence." | Tested | `docs/stories/H-034.md` |
| H-035 | "A test that launches Godot runs against an imported tree in the gate, wherever the test file lives, so a fresh sweep tree never fails on a missing import cache." | Tested | `docs/stories/H-035.md` |
| H-036 | "A docs-only push to main while a landing sits in the gate does not cost that landing a re-merge: the stale-base check ignores commits that touch only docs/." | Spec'd, no story yet (H-034 landing re-merged twice on 2026-10-31 after two records pushes) | none yet |
| H-037 | "The specfactory baseline carries no pre-existing red: every one of the 164 failing tests of 2026-10-31 is retired with its ruling, fixed as a test-defect, or filed as a finding against the landing that broke it." | Spec'd, no story yet (test_method_metrics 130 go with the 20 dropped metrics; test_gate_tiers 20, test_token_ledger 5, test_gate_userdir 2, six singles ruled one by one; 7 changed assertions listed by the gate) | none yet |
| H-038 | "The game draws its first scene on my desktop whatever size the window comes up at, fullscreen included; I never see the splash and nothing else." | Ready (client; part 1 diagnosis first) | `docs/stories/H-038.md` |
| H-039 | "A fight the lab runs is written down as a small file of snapshots that any reader (the game scene, the page, me) can open: who stood where, facing where, with how much health, every few seconds, and who won against who I said would win." | Tested | `docs/stories/H-039.md` |
| H-040 | "I place two groups of one unit type on an open field, both attack-move, and I watch the fight happen in the game and see who won against who I said would win." | Spec'd (client; five parts after H-039; eyes gate) | `docs/stories/H-040.md` |
| H-029 | "No code in the gate still reads pieces.toml: the dead pieces-based functions and their tests are gone." | Tested | `docs/stories/H-029.md` |
| H-030 | `undertest-from-stories`: the undertest check reads every landed story's Tests line (git log trailers or docs/stories) instead of an ownership table and warns on a test file no story names. | Ready, no story yet | none yet |

Order: H-006 first (every later landing needs it; it carries the last pieces.toml row ever written, its own), then H-001, H-002, H-003, H-005, H-004.

Converted 2026-10-30 from pieces.toml rows (plan step 4): H-014 to H-019 are the held harness rows; their pieces rows stay until the file is retired. Not converted: HARNESS-cache-seed-alias and the H1023 trio (no spec paragraph found on main; on hold until one is written). The lab rows convert under H-008.
