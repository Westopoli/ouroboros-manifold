# The beta staircase: the game assembled one approved step at a time, on its own gate channel

Westley, 2026-11-02: "there's not a beta.exe or command I can run that shows me the latest versions ... all I know is the work being done passes tests, but doesn't actually run. I want to ... use the same staged mechanism to put the pieces together of the beta." Approved by him the same morning; amended at once: B5 is one role in groups, not one unit.

Standing rules, unchanged from the lab staircase (DEC-lab-staircase-2026-10-31): one story, one branch, one `--no-ff` landing; tests first by a different Sonnet; the Sonnet look reviewer before any picture reaches his folder; every picture row carries "What to expect / Approve means / Deny means"; a stage is Seen only on his verdict in a scene he plays; the next stage is Ready the day the previous is Seen; every number below is an Architect draft until he rules; Fable writes no code.

New for the beta: every landing on the beta channel refreshes the standing build (`om-beta`, H-028) and its proof is a real screen capture of that build (H-031; the clerk wakes the monitors first, DEC-wake-monitors-for-proof-2026-11-02). A stage's five variants are five things he switches between inside the beta: a dev picker on the mission preparation screen (DRAFT-variant-picker; hidden in the shipping build), so one run line, `om-beta`, serves every stage.

## Where the beta lives

2026-11-02, Westley: "om-beta approved but I want to migrate M0 from wherever it is now into the godot project in the ouroboros directory. Amend the documentation for the beta (the original plan file), send out the beta dispatcher to accomplish the task, and come back to me with M0 when it's consistent with that request." The Architect reads "M0" as B0, the beta's stage zero.

The beta is the Godot project at the repository root, `~/Projects/ouroboros-manifold` (his checkout) and any clone of main; he opens `project.godot` in his editor and presses F5. `om-beta` is the pinned snapshot of that same project at one commit (an export under `~/Projects/om-push/beta/<sha>/`, installed launchers, `PLAYED.txt`), approved by him 2026-11-02 and kept for proofs and for a frozen view; it is not where the beta is built. The stage scenes (for example `scenes/beta/stage_field.tscn`) are scenes in that project. Nothing about the beta's code lives outside the repository except build output and the installed launcher; the pipe binary and the Steam libraries are produced into the project folder by `scripts/setup_editor.sh` (H-067). B0 was approved by Westley on 2026-11-02 and B1 may start while the editor route (H-067) is finished in parallel (his words in DEC-b1-go-2026-11-02).

## The two channels (H-059)

The lab and the beta land through separate gates so neither blocks the other (Westley 2026-11-02: "we have enough compute to run multiple gates at the same time"). `gate-lab.lock` and `gate-beta.lock` replace `gate.lock` for the gate stages; one short `push.lock` serialises fetch, merge, pre_gate re-check and the push; `play.lock` serialises every real-display play and capture (one window on his desktop at a time). Shared files made safe: `gate_runs.csv` appended under a flock; `baseline_cache` and `candidate_results` written through `mktemp` names. Worktree slots per channel. Each story carries a `Channel:` Machine line. A Dispatcher chat serves one channel: `ouroboros-manifold-lab` (today's `ouroboros-manifold-90`) and `ouroboros-manifold-beta` (new; Westley opens it; its context file is `plans/2026-11-02-beta-dispatcher-context.md`). The sweep stays one per main; a REJECT row blocks both channels, since a red main is red for both.

H-059 landed on 2026-11-02 (e23c303f): the beta channel has its own gate, `gate-beta.lock`.

## The stages

| Stage | Story | What he sees after Launch in `om-beta` | Five variants | Done when |
|---|---|---|---|---|
| B0 the build exists | H-028 (om-beta, Seen 2026-11-02) and H-067 (the project runs from the editor) | the project opens in his editor, F5 runs the chain (main menu, galaxy, mission preparation) after one setup command; om-beta (the pinned snapshot) opens the same main menu | none | he runs om-beta and reaches the main menu (done, approved 2026-11-02); the project opens in his editor, `scripts/setup_editor.sh` once, F5 walks the chain (H-067, in parallel; B1 does not wait for it) |
| B1 the approved screens | H-060 | main menu, galaxy, mission preparation as they stand (S-110, S-106, S-107 Seen; S-109 Seen by his word 2026-11-02); Launch leads to an empty field placeholder | none | he clicks through all three in `om-beta` and says they are the approved ones |
| B2 the layout, no units | H-061 | the mission's layout drawn flat on the ground as shapes (pads, gaps, plateaus, pockets, routes), camera rig live, no relief, no units | five layout kinds from the catalogue: open field, chokepoint, vantage, city, trap | he pans each and says the shapes read as the situation named |
| B3 the landscape engine | (id assigned when written) | the approved terrain-obeys-the-layout pass 2 integrated: relief, bands, the layout shaping the ground | the same five layouts with relief, seed fixed per layout | he pans each and agrees the ground obeys the layout; no visible map-edge void (his W1) |
| B4 buildings, objectives, cities | (id assigned when written) | settlement footprints, objective markers, city blocks on the B3 ground; nothing moves | the five layouts, each with its places | he says the places sit where the layout says and read as places |
| B5 one role, in groups | (id assigned when written) | groups of one role (DRAFT Vanguard, DRAFT 8 to 32 units) on the B4 ground; selection, click-move, attack-move, formation slots, facing triangles, 3D placeholders (his W6/W7 verdicts); the engine's movement over the real pipe; no enemy | the five grounds, one group each | he moves groups across hill, gap and street and says they walk the ground, hold formation and obey the order |
| B6 vision | (id assigned when written) | sight discs that follow the ground (his W2), fog outside them, enemy units of the same role that appear and vanish by the sight rules; ping if the role has it | the five grounds | he says who sees whom reads right on hill and in street |
| B7 layers, land era first | (id assigned when written) | height bands with the land era's layer rules (E-01): the groups climb and descend, the band change tells | the five grounds, vantage and city carrying the bands | he sees the climb slow a group and the band change tell |
| B8 all roles, real fights | (id assigned when written) | the six roles mixed on both sides, the enemy force under one doctrine, fights under the lab's engine rules (H-057 engage-on-sight and the per-type leash) | five fights, one per ground, enemy headcount per layout | he fights each and names what looks wrong; a wrong behaviour becomes a story, not a stage fix |
| B9 and after: the economy in pieces | (id assigned when written) | one piece at a time from E-22: a settlement that grows; one resource; one production line; one wave; the economy seat's orders | per piece | per piece, his verdict |

The five-variant choice for B2 to B7 (five layout kinds rather than five seeds of one) is the Architect's draft so that every stage is judged on the same five grounds and the pictures compare stage to stage. Steam (ROADMAP section 2, rows 5 to 8) follows B8.

Stories written Ready today: H-059 (channels), H-028 (B0, rewritten), H-060 (B1), H-061 (B2), and, as beta-channel stories outside the staircase, H-067 (the project runs from the editor: B0 piped into the project, in parallel with B1), H-069 (router warning) and H-041 (unit scale read-through, values by Westley 2026-11-02). B3 onward are Spec'd one stage ahead of the Seen stage, as the lab does.

## Beta Dispatcher brief (the first message of the `ouroboros-manifold-beta` chat)

Read `docs/method/runner.md`, then this file. Your channel is `beta`; your lock is `gate-beta.lock`. H-028 (93815871) and H-038 part 2 (d914f2e0) landed, build 1c2cce20 is published and proved, and Westley approved `om-beta` on 2026-11-02 and B0 as a stage with it (Seen 2026-11-02); the editor route (H-067) is finished in parallel (section Where the beta lives). Queue: H-060 (B1) now; H-067 and H-069 landing through the beta gate; H-041 (the sim reads Westley's per-role unit radius, a contract story, Ready) in parallel; H-061 (B2) after B1 is Seen. Standing rules: one report per landing group to the Architect (`beta-staircase-gate-channel`, ref 845ad1); stop rules in each story bind; no polling; every picture through the Sonnet look reviewer with the three sentences; Westley's checkout is fast-forwarded only when clean. H-031 piece three (crop the proof to the game window) stays Spec'd and is not a B0 precondition.

## Where things stand

Rewritten by whoever moves a stage, in the same commit (ROADMAP.md section 1 carries the one-line state per stage; this table carries the words).

| Stage | State 2026-11-02 |
|---|---|
| B0 | Seen 2026-11-02 (Westley: 'I saw B0 and approved it'). The editor route (H-067) is finished in parallel: builder done, landing queued on the beta gate. |
| B1 | H-060 build done (17 tests green); landing queued on the beta gate behind H-069 and H-067; the landings are blocked on environment faults (GPU memory held by a local ollama model, /tmp quota), not on code. |
| B2 | H-061 Ready; builds after B1 is Seen |
| B3 to B9 | Spec'd in this table only; story files written one stage ahead |
