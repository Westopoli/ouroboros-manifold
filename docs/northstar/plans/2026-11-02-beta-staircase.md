# The beta staircase: the game assembled one approved step at a time, on its own gate channel

Westley, 2026-11-02: "there's not a beta.exe or command I can run that shows me the latest versions ... all I know is the work being done passes tests, but doesn't actually run. I want to ... use the same staged mechanism to put the pieces together of the beta." Approved by him the same morning; amended at once: B5 is one role in groups, not one unit.

Standing rules, unchanged from the lab staircase (DEC-lab-staircase-2026-10-31): one story, one branch, one `--no-ff` landing; tests first by a different Sonnet; the Sonnet look reviewer before any picture reaches his folder; every picture row carries "What to expect / Approve means / Deny means"; a stage is Seen only on his verdict in a scene he plays; the next stage is Ready the day the previous is Seen; every number below is an Architect draft until he rules; Fable writes no code.

New for the beta: every landing on the beta channel refreshes the standing build (`om-beta`, H-028) and its proof is a real screen capture of that build (H-031; the clerk wakes the monitors first, DEC-wake-monitors-for-proof-2026-11-02). A stage's five variants are five things he switches between inside the beta: a dev picker on the mission preparation screen (DRAFT-variant-picker; hidden in the shipping build), so one run line, `om-beta`, serves every stage.

## The two channels (H-059)

The lab and the beta land through separate gates so neither blocks the other (Westley 2026-11-02: "we have enough compute to run multiple gates at the same time"). `gate-lab.lock` and `gate-beta.lock` replace `gate.lock` for the gate stages; one short `push.lock` serialises fetch, merge, pre_gate re-check and the push; `play.lock` serialises every real-display play and capture (one window on his desktop at a time). Shared files made safe: `gate_runs.csv` appended under a flock; `baseline_cache` and `candidate_results` written through `mktemp` names. Worktree slots per channel. Each story carries a `Channel:` Machine line. A Dispatcher chat serves one channel: `ouroboros-manifold-lab` (today's `ouroboros-manifold-90`) and `ouroboros-manifold-beta` (new; Westley opens it; its context file is `plans/2026-11-02-beta-dispatcher-context.md`). The sweep stays one per main; a REJECT row blocks both channels, since a red main is red for both.

Until H-059 is on main (it lands through today's single gate, after H-057), the beta channel does records-only work.

## The stages

| Stage | Story | What he sees after Launch in `om-beta` | Five variants | Done when |
|---|---|---|---|---|
| B0 the build exists | H-028 (unheld, beta channel) with H-038 part 2 and H-031 piece three | `om-beta` on his desktop opens the main menu; refreshed on every beta landing; the proof capture cropped to the game window | none | he runs `om-beta` and reaches the main menu; the status line says "beta: sha, refreshed date" |
| B1 the approved screens | H-060 | main menu, galaxy, mission preparation as they stand (S-110, S-106, S-107 Seen; S-109 Seen by his word 2026-11-02); Launch leads to an empty field placeholder | none | he clicks through all three in `om-beta` and says they are the approved ones |
| B2 the layout, no units | H-061 | the mission's layout drawn flat on the ground as shapes (pads, gaps, plateaus, pockets, routes), camera rig live, no relief, no units | five layout kinds from the catalogue: open field, chokepoint, vantage, city, trap | he pans each and says the shapes read as the situation named |
| B3 the landscape engine | H-062 | the approved terrain-obeys-the-layout pass 2 integrated: relief, bands, the layout shaping the ground | the same five layouts with relief, seed fixed per layout | he pans each and agrees the ground obeys the layout; no visible map-edge void (his W1) |
| B4 buildings, objectives, cities | H-063 | settlement footprints, objective markers, city blocks on the B3 ground; nothing moves | the five layouts, each with its places | he says the places sit where the layout says and read as places |
| B5 one role, in groups | H-064 | groups of one role (DRAFT Vanguard, DRAFT 8 to 32 units) on the B4 ground; selection, click-move, attack-move, formation slots, facing triangles, 3D placeholders (his W6/W7 verdicts); the engine's movement over the real pipe; no enemy | the five grounds, one group each | he moves groups across hill, gap and street and says they walk the ground, hold formation and obey the order |
| B6 vision | H-065 | sight discs that follow the ground (his W2), fog outside them, enemy units of the same role that appear and vanish by the sight rules; ping if the role has it | the five grounds | he says who sees whom reads right on hill and in street |
| B7 layers, land era first | H-066 | height bands with the land era's layer rules (E-01): the groups climb and descend, the band change tells | the five grounds, vantage and city carrying the bands | he sees the climb slow a group and the band change tell |
| B8 all roles, real fights | H-067 | the six roles mixed on both sides, the enemy force under one doctrine, fights under the lab's engine rules (H-057 engage-on-sight and the per-type leash) | five fights, one per ground, enemy headcount per layout | he fights each and names what looks wrong; a wrong behaviour becomes a story, not a stage fix |
| B9 and after: the economy in pieces | H-068 onward, split when B8 is Seen | one piece at a time from E-22: a settlement that grows; one resource; one production line; one wave; the economy seat's orders | per piece | per piece, his verdict |

The five-variant choice for B2 to B7 (five layout kinds rather than five seeds of one) is the Architect's draft so that every stage is judged on the same five grounds and the pictures compare stage to stage. Steam (ROADMAP section 2, rows 5 to 8) follows B8.

Stories written Ready today: H-059 (channels), H-028 (B0, rewritten), H-060 (B1), H-061 (B2). B3 onward are Spec'd one stage ahead of the Seen stage, as the lab does.

## Beta Dispatcher brief (the first message of the `ouroboros-manifold-beta` chat)

Read `docs/method/runner.md`, then this file. Your channel is `beta`; your lock is `gate-beta.lock` once H-059 is on main, `gate.lock` before (one landing at a time with the lab until then). B0 is done on your side: H-028 (93815871) and H-038 part 2 (d914f2e0) landed, build 1c2cce20 is published and proved, and it waits only on Westley's verdict. Queue in order: H-060 (B1) once B0 is Seen, then H-061 (B2). Standing rules: one report per landing group to the Architect (`beta-staircase-gate-channel`, ref 845ad1); stop rules in each story bind; no polling; every picture through the Sonnet look reviewer with the three sentences; Westley's checkout is fast-forwarded only when clean. H-031 piece three (crop the proof to the game window) stays Spec'd and is not a B0 precondition.

## Where things stand

Rewritten by whoever moves a stage, in the same commit (ROADMAP.md section 1 carries the one-line state per stage; this table carries the words).

| Stage | State 2026-11-02 |
|---|---|
| B0 | Built and proved: H-038 part 2 (d914f2e0) and H-028 (93815871) landed; build 1c2cce20 published at `~/Projects/om-push/beta/current`, `om-beta` and the desktop entry installed, `PROOF OK`; waits only on Westley's verdict (Seen). H-031 piece three is not a precondition and stays Spec'd |
| B1 | H-060 Ready; tests round 2 in flight on `s/H-060-beta-b1-approved-screens`; builds after B0 Seen |
| B2 | H-061 Ready; builds after B1 is Seen |
| B3 to B9 | Spec'd in this table only; story files written one stage ahead |
