# What Westley decides, 2026-10-21

Answer in answers.md, one line per key: `<key>: <approve | reject | a | b | c | note>`. Anything not listed here is already decided or is the Architect's.

## 1. Pictures

## 2. Questions

### Q-156-02 Lab pass marks

The lab's ten draft pass marks (mirror tolerance, skill beating the noise, rank agreement, stacking, dominance, dead skills, counters) are unconfirmed.

(a) The draft marks as written.  
(b) You set each of the ten (opens ten per-mark questions).  
(c) Report only, no pass or fail, until you confirm them.

unblocks: lab rev 2 runs with real marks instead of drafts.

(your 2026-10-21 note: not enough context)

### Q-147-01 Name the land era and the roster

The land era is "The Marble Reach" as a placeholder; its name, setting, tone and scale, and the order of eras after the first two, are unwritten. Give your words, or ask the Architect to draft candidates; also write the roster in order and mark each era earnable or purchase-only.

unblocks: the era pack form, the land era's identity and the roster the store sells.

(your 2026-10-21 note: Already decided this: Greek)

### Q-149-02 Which eras are purchase-only?

Which eras are exclusive to purchase and which earnable, and the naming of the base three on the store. Give your words.

unblocks: store work, after the beta.

## 3. Asked in chat, still open

### C1 Lab fight length
The lab's "attackers break a held line" fight runs 229 s against your 150 to 200 s window.
(a) widen the window to 230 s; (b) keep the window, the lab landing waits for a faster fight; (c) replace the fight.
unblocks: the whole lab rev 2 landing.

### C2 Lab speed
The rev 2 lab runs about 82 s per run in its Python against your 30 s mark (3.9 times slower than rev 1).
(a) accept 82 s now and speed it up after; (b) hold the landing until under 30 s; (c) a new mark.
unblocks: the same landing.

### C3 Known-red list for the gate
Let the merge gate carry a short list of tests known red for a named, recorded reason, so a landing is not rejected by a red that is already on record. yes / no.
unblocks: two Lane T landings and the lab landing.

### C4 Lab positive control
The lab's "a planted bad fight trips the detector" control reads green on main when it should trip.
(a) no lab landing until it trips; (b) land with it listed red and fix it next.
unblocks: the lab landing order.

### C5 Strongpoint damage (register Q-218-08)
A strongpoint is captured or destroyed, but nothing says units shoot it and take away its hp. Do units damage strongpoints?
(a) yes, by fire; rubble at zero hp; capture works as it does now; (b) capture only, never shot, and the unused damage code is deleted; (c) only the Siege category damages them.
unblocks: the strongpoint-damage piece.

### C6 Onboarding weights (register Q-074-05)
Your onboarding answers carry a weight for each mission kind and a mark for rare kinds, but mission selection does not read them yet (preference and difficulty are being wired regardless). How should they weigh the pool of candidate missions?
(a) the weights multiply each mission kind's score and the rare marks add the rare kinds to the pool; (b) they only feed the briefing's foreshadowing; (c) dropped from the design.
unblocks: the weights part of the onboarding work.

### C7 Housekeeping
Three yes/no, answer each as `C7i`, `C7ii`, `C7iii`:
(i) the clerks' scratch space: raise the /tmp quota, or keep all scratch under ~/Projects/om-push/tmp-*;
(ii) discard the dirty lab diagnostic worktree labdiag (29 files of uncommitted edits on an old lab base, believed throwaway, unreviewed), or have an engineer read its diff first;
(iii) widen the worktree-removal rule to treat Godot .import sidecars and dist/ as build outputs and to remove unmarked worktrees that are clean, on origin and older than three days.

### C8 Failed-play frames
Four ground-era story plays the reviewer judged "no", still pending with you, with no picture in your folder (all lane C, one run):
- S-236 (fully zoomed-in ground map): the zoom never reached the close-up band, so the shot shows the whole island from far away as colour-banded patches with tiny hexagon units; no up-close land detail.
- S-001 (slopes and blocked ground): no slope or blocked-ground marking exists; the opening frame shows coloured terrain bands but nothing marking blocked layers.
- S-004 (crossing layers): no unit entered a layer transit within 1000 ticks of a cross-map move, so no transit or halfway line was ever shown.
- S-132 (unit types readable): the force is collapsed or partly undrawn; four clusters of stacked identical hexagons with big cyan rings, types not distinguishable by shape.

### C9 Starting force size
You wrote on 10-11: "players start with at least half-force when a match begins, if not as far down as 20% (specific number depends on ... scaled)". The frame you rejected today showed a one-third share: 176 of 330 (today's curve gives half at a quarter share, 0.6 at a half share, four fifths at a full share) and read to you as "still quite a few units, only decreased by ~25%".
(a) keep today's curve; (b) a third at a half share, same slide; (c) a quarter at a half share; (d) a number of your own.
unblocks: FINDING-s126-count-still-large; the starting-force shot re-run.

### C10 Vantage points need two paths?
The terrain prototype's lookouts were unreachable; the audit found no rule that gives a vantage two routes (R-189-07's two-route rule covers bases, the objective and economic sites; R-192-03 lets about 30 percent of peaks be unreachable on foot).
(a) every vantage and strategic point has at least two routes, like bases; (b) one slope path suffices and some peaks may stay unreachable (today); (c) two routes only for vantages within 1500 wu of a choke.
unblocks: the terrain-obeys pass 3 and the layout engine's vantage request.

### C11 Building placement limits
The placement engine refuses a building on top of another placed building and refuses when the engine's lot table (8192) is full. Your words were "limits only from terrain" and "no lot count in the beta".
(a) the overlap refusal is physical and stays, the table size is a memory bound and is documented as not a rule (the Architect's reading); (b) remove the overlap refusal too: buildings may stack and the terrain alone limits; (c) something else.
unblocks: nothing today; the E1R shot.

### C12 September mockups without a verdict
Five September mockups (fog, hud, units, objectives, menus) have no recorded verdict from you.
(a) treat them as approved as built; (b) you look at each (commands in followups/01_transition.md section 1); (c) drop them.

## 4. Drafts in force unless you veto

- DRAFT-b25-star-ref: 1080 px, 45 degree fov (Architect, 2026-10-21)
- DRAFT-startforce-pocket 400 wu, DRAFT-startforce-clamp 0.15, DRAFT-startforce-offset 200 wu (Architect, 2026-10-20)
- DRAFT-c25-patch-radius: 3 (Architect, 2026-10-21)
- Places lane drafts of rev 6a: DRAFT-shape-harm 0.5, DRAFT-first-ring-spread 2, DRAFT-field-cost-share 15 to 55 percent (Architect, 2026-10-21)
- Age-10 lots scope narrowing (Architect, 2026-10-21)

Parked by you (10): see batch_closed.md; added 2026-10-21: Q-208-01, Q-149-01.

## Answered 2026-10-21

- Q-B23b-01: It's fine as it is for now (recorded: docs/northstar/ambiguity_register.md)
- Q-C2-5-01: A, that is the look; the test samples wrong (recorded: docs/northstar/ambiguity_register.md)
- Q-246-02: Layout engine sets it, landscape engine conforms (recorded: docs/northstar/ambiguity_register.md)
- Q-082-03: defer to after beta (recorded: docs/northstar/ambiguity_register.md, parked)
- Q-100-01: B, arc width per category (Strike wide, Line medium, Siege narrow), widths still lab drafts (recorded: docs/northstar/ambiguity_register.md)
- Q-208-01: defer to after beta (recorded: docs/northstar/ambiguity_register.md, parked)
- Q-228-01: A, only the commanding seat has a ledger character (recorded: docs/northstar/ambiguity_register.md)
- Q-149-01: defer to post beta (recorded: docs/northstar/ambiguity_register.md, parked)
- B22 part 1: A, publish the real internal figures (recorded: docs/northstar/plans/push_ledger_2026-09-22.md, DEC-B22-part-1-2026-10-21)
- B22 part 2: A, name and quotes appear (recorded: docs/northstar/plans/push_ledger_2026-09-22.md, DEC-B22-part-2-2026-10-21)
- B22 publish: A, publish after his read (recorded: docs/northstar/plans/push_ledger_2026-09-22.md, DEC-B22-publish-2026-10-21)
- doc branch method ask 1: B, the method page becomes an internal page (recorded: docs/northstar/plans/push_ledger_2026-09-22.md, DEC-doc-branch-method-ask-1-2026-10-21)
