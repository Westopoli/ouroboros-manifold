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

### Q-100-01 Firing arc

You ruled on 2026-10-13 that a unit fires only inside an arc about its facing. Width, and whether it varies by type, are yours after the lab shows the effect (so this one comes after the lab chart).

(a) One arc for every type, 120 degrees as a draft the lab sweeps.  
(b) Width per category: Strike wide, Line medium, Siege narrow.  
(c) An arc for Siege only; the others fire all round.

unblocks: the final arc rule.

### Q-208-01 Can a force hold fire?

A guard steps up to engage and returns to its post. Nothing lets you order a force to wait unseen and not shoot.

(a) A hold-fire setting on the guard stance.  
(b) A separate hold-fire order.  
(c) No hold fire; an ambush is made by going silent alone.

unblocks: the movement lane, after the lab data.

### Q-228-01 Who gets a ledger character in a team?

A chapter has one commander today; how the economy seat of a pair and each sub-commander enter the chapter record and the ledger is unsettled.

(a) Only the commanding seat has a ledger character; the economy seat has none.  
(b) Every player has a ledger character and a lineage.  
(c) Other: your words.

unblocks: pairs reaching the chronicle.

### Q-149-01 How is an era earned?

Eras can be earned by play as well as bought; the condition is not set.

(a) Complete a 10-chapter campaign in the preceding era.  
(b) Reach Tier 3 in any campaign.  
(c) Other: your words.

unblocks: store work, after the beta.

### Q-149-02 Which eras are purchase-only?

Which eras are exclusive to purchase and which earnable, and the naming of the base three on the store. Give your words.

unblocks: store work, after the beta.

### B22 part 1 Show the internal figures on the website?

The website refresh draft (built, not deployed) has a page on how the game is made. Does it publish the programme's internal figures?

(a) Yes: publish the real figures.  
(b) No: keep them out.

unblocks: nothing in the queue; decide with the next three.

### B22 part 2 Your name and quotes on the site?

May the same draft name you and quote you?

(a) Yes: name and quotes appear.  
(b) No: the site speaks anonymously.

unblocks: nothing in the queue.

### B22 publish Publish the site at all?

The draft shows the galaxy view, both landscape engines, the walking prototype and the method page. Nothing deploys until you say.

(a) Yes: publish after your read.  
(b) No: hold it.

unblocks: nothing in the queue.

### doc branch method ask 1 Is the method page the public face?

A branch holds an outsider-readable page on how the game is built (tests first, prototypes approved before planning, a fight-measuring lab, ten draft pass marks). The branch verdict is "land after named edits".

(a) Yes, it stays an outsider page.  
(b) It becomes an internal page.  
(c) Not wanted.

unblocks: how openly the project explains itself; nothing in the queue waits on it. Decide with the three site questions.

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
You wrote on 10-11: "players start with at least half-force when a match begins, if not as far down as 20% (specific number depends on ... scaled)". The frame you rejected today showed half (176 of 330, the player holding half the strongpoints) and read to you as "still quite a few units, only decreased by ~25%".
(a) keep half at a half share, sliding to a fifth at no strongpoints (today); (b) a third at a half share, same slide; (c) a quarter at a half share; (d) a number of your own.
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

Parked by you (8): see batch_closed.md.

## Answered 2026-10-21

- Q-B23b-01: It's fine as it is for now (recorded: docs/northstar/ambiguity_register.md)
- Q-C2-5-01: A, that is the look; the test samples wrong (recorded: docs/northstar/ambiguity_register.md)
- Q-246-02: Layout engine sets it, landscape engine conforms (recorded: docs/northstar/ambiguity_register.md)
- Q-082-03: defer to after beta (recorded: docs/northstar/ambiguity_register.md, parked)
