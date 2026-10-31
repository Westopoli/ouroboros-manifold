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
| H-016 | "A landing of two stories at once runs both stories' tests, and the cache seed after a push actually seeds." | Spec'd | `docs/stories/H-016.md` |
| H-017 | "A change under csrc runs the pinned csim tests before the push." | Spec'd | `docs/stories/H-017.md` |
| H-018 | "The pins warning tells stale pins from never-pinned tests." | Spec'd | `docs/stories/H-018.md` |
| H-019 | "The gate's cache hits on a docs-only merge because each suite declares only what it reads." | Spec'd | `docs/stories/H-019.md` |
| H-020 | "The gate's own toy-repo tests carry a story file like every real candidate, so a sweep of main is green again, and the landing that fixes a red sweep's tests may pass the sweep check it is fixing." | Tested | `docs/stories/H-020.md` |
| H-021 | "A red sweep row never blocks the next sweep: the slow tier reports the row as a warning and runs the suite that can replace it." | Tested | `docs/stories/H-021.md` |
| H-022 | "The csim xdist gate tests carry a story file and the tier they mean, like the rest of the toy gates." | Tested | `docs/stories/H-022.md` |
| H-023 | "a prototype to show unit scale in comparison to several 'strategic positions', with metrics for me to be able to understand how big each individual unit will be relative to other landscape pieces and buildings/cities and strategic positions, before we run the simulation engine with locked in unit scales." | Tested | `docs/stories/H-023.md` |
| H-024 | "a prototype full fidelity 60fps visual of a match vs what the screenshots at a specific configuration look like, then when I see the comparison I can effectively rule on timing" | Spec'd | `docs/stories/H-024.md` |
| H-025 | "Layouts are mass-produced from the recorded rules, each with a 3D shot and a predicted verdict, and Westley approves or denies each one with feedback; only approved layouts reach the lab." | Tested | `docs/stories/H-025.md` |
| H-026 | "`wt.py new --branch <b>` fails with an empty \"git worktree add failed:\" when a finished worktree still has that branch checked out; it should say so (`branch <b> is checked out in <path>`) and, for a finished tree, offer `wt.py reap` or detach (found 2026-10-30 by the H-023 builder)." | Ready | none yet (`wt-branch-flag`) |
| H-027 | "`desktop-test-import`: a fresh worktree needs `godot --import` before a desktop (.py qa) story test passes, and that import leaves .import and .uid noise that pre_gate rejects; pre_gate (or play.sh --check) should run the import in a scratch copy or accept the import's outputs as build outputs (found 2026-10-30 landing H-023; the clerk used a second tree with .godot copied in)." | Ready | none yet |

Order: H-006 first (every later landing needs it; it carries the last pieces.toml row ever written, its own), then H-001, H-002, H-003, H-005, H-004.

Converted 2026-10-30 from pieces.toml rows (plan step 4): H-014 to H-019 are the held harness rows; their pieces rows stay until the file is retired. Not converted: HARNESS-cache-seed-alias and the H1023 trio (no spec paragraph found on main; on hold until one is written). The lab rows convert under H-008.
