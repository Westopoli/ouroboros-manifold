# The simulation lab: plan of record (2026-10-27)

**Status head.** State: PAUSED for the method fixes (HARNESS-mm-8, mm-9, RECORDS-mm-2 in the Dispatcher's hands); resumes on Westley's word after the first planned day (DEC-daily-allotment-2026-10-27). Last landing: LAB-REV3-B merged 7dd4d8fc (2026-10-23; records flip owed). Last batch run: layout run 1, 2026-10-08; batch one not yet run. Waits on Westley: section 5. Supersedes `~/.claude/plans/lovely-purring-wozniak.md` and `buzzing-greeting-sky.md` (DEC-plans-of-record-2026-10-27); the rev 2 spec, the rev 3 plan and `research/layer_dynamics/README.md` stay the detail; this file is the order and the status.

## 1. Goal, and when it is finished

The lab answers Westley's 2026-09-30 request: a simulator that varies what an RTS varies (position, orientation, damage, health, vision, landscape, layers) and finds **where the lines cross**: the settings at which a smaller force played with skill beats a larger force played without it, for each of the five skills (landscape, formation, layers, enemy position, unit-type matchup), with more than one such region allowed ("the lines can cross in multiple locations").

Finished (DEC-lab-finished-lines-cross-2026-10-27): the crossings are documented extensively. For every knob family and every skill: the regions of settings where the skilled smaller force wins, the crossing points (headcount ratio against the knob), the diagrams with the evidence marked on them (`feedback-lab-charts-show-layouts`), the counters that undo each play, and Westley's pass marks. When that document exists and he has read it, the lab is done and the beta resumes with its numbers.

## 2. Where it stands (from the lab audit of 2026-10-27)

| Step | State |
|---|---|
| Rev 2: the measure's blind spots closed, the 2026-10-13 rulings built (L1 to L8, BASE, SPEED, golden re-record) | landed 43bf9462, 2026-10-22 |
| LAB-VISION-CONTROL, L8M, L8M2 (re-engage stand-ins) | landed |
| Rev 3 A: coverage defects D3 to D6, T1, T2 probe | landed 1e5f8a7c |
| Rev 3 B: mixes M5 to M9, five-layer plays, Warden cap | merged 7dd4d8fc; `pieces.toml` still says queued, no landing row (records fix owed) |
| Rev 3 C: reach and vision as swept knobs, the paper prediction (positioning decides, in numbers), `no_reach_stall`, per-reach crossings | not started |
| Batch one: the coarse knob batch (smoke layouts 81, 78, 192; the layer-above, types-by-reach and five mix plays) | not run; waiting on Westley since 10-22 |
| E2 arc and cone, E4 radius guard (engine) | not built |
| Batch two: arc and cone families, guard, ground scene | after E2 and E4 |
| R9 sight-engagement engine piece, retire L8 | queued |
| FU-warden-no-stack | open, waits on the Warden rule |
| ALG rows for Q-008-03 | owed after batch one's analysis |
| The search (plan step 7): every region where the conditions hold, two ways | not specced |
| The crossings document (section 1) | not started |

## 3. Order of work when the lab resumes (revised 2026-10-27 after Westley's answers)

1. Records: B flip and landing row, ROADMAP row, the positioning-decides sentence in README sections 2 and 4, the ten coverage defects in README section 12. One clerk, under 1 M tokens.
2. E2 (firing arc, cone) and E4 (guard radius) as one cascade, with FU-warden-no-stack (a defect against R-083-03) in the same cascade: the combat behaviours before any batch (DEC-engine-before-batch-one). About 35 M.
3. The vision-asymmetry plays: the Architect checks which ping, going-dark and decoy plays are registered in `plays_space.py`, specs the missing ones, one cascade builds them (DEC-batch-one-vision-asymmetry). About 15 M.
4. Rev 3 C as one cascade (reach and vision as swept knobs, the paper prediction). About 15 M, ceiling 50 M.
5. R9 sight-engagement, retire L8. One cascade, about 15 M.
6. Batch one, the first night after 2 to 5 are on main: layer-above, types-by-reach, the five mix plays, the ping and dark plays; every layer pair the reach table allows; the arc, cone and guard families included. Compute; the review about 10 M.
7. Batch two and the ground scene; ALG rows, Q-008-03 closed.
8. The speed-up piece (FINDING-speed-marks-unmet, marks kept).
9. The search: spec by the Architect, audited, then built. Unestimated until specced.
10. The crossings document, read by Westley. Done.

Each day is planned against DEC-daily-allotment (300 M: 60 Dispatcher, 180 pieces, 60 reserve) in the Dispatcher's status table; actuals by `token_ledger.py` once HARNESS-mm-12 lands.

## 4. Rules in force for the lab (pointers)

Rulings 2026-10-13 (rev 2 spec); the positioning rule 2026-10-19 (`feedback-positioning-decides`: a better-positioned force wins by design, predict from the setup); the mixes R1 and the sight-engagement rule 2026-10-19 (rev 3 plan); decisions 46 and 47 (arc 30 degrees, arc grid); DEC-Q156 (no verdicts until the scale marks are confirmed); the draft numbers in README section 12.

## 5. What waits on Westley

Answered 2026-10-27: pass marks as drafted; layer pairs every allowed pair plus the vision-asymmetry plays in batch one; batch one after the combat behaviours; speed marks kept; the Warden aura does not stack (R-083-03, already in the bible). Open: nothing before step 6. At step 6: the batch's first page and diagrams for his reading.
