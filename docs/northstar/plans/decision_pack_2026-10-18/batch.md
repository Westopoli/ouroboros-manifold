# The batch (2026-10-18, slimmed 2026-10-21): what only Westley decides

Fourteen open design questions, in the order they unblock work, and eight you have parked. The implementation choices the Architect took, the rows the record already answers, the duplicates, the moot rows and the 2026-10-18 shots are in `batch_closed.md` (veto any of them in one line).
Answer in `answers.md` beside this file, one line each: `<key>: <letter>` or `<key>: <letter> - <your words>`; `<key>: open - <your words>` when none fits. Skip anything you do not want to rule yet.
Shots still waiting for your eye are in the page table `../../story_reviews/westley/README.md`. Q-069-03 is answered (2026-10-19) and moved out.

## Open design questions

### 1. Which renderer is the look?
**Question.** Under the richer lighting the 3D ground wants, the see-through faction shells wash out the system dots (our pixel check reads 6 of 18); under the simpler lighting the checks use, the dots read fine.
(a) Ship the richer lighting, and the pixel check gains a run on it. (b) The wash is the approved look. (c) A small fix makes the shells fainter over the dots (the Architect's lean, shipping the richer path).
**Unblocks.** The lane B pixel test and fix piece.
<sub>key: Q-B23b-01</sub>

### 2. Lab pass marks
**Question.** The lab's ten draft pass marks (mirror tolerance, skill beating the noise, rank agreement, stacking, dominance, dead skills, counters) are unconfirmed.
(a) The draft marks as written. (b) You set each of the ten. (c) Report only, no pass or fail, until you confirm them.
**Unblocks.** Lab rev 2 runs with real marks instead of drafts. Picking (b) opens the ten per-mark questions (C0 to C9, in `batch_closed.md`).
<sub>key: Q-156-02</sub>

### 3. Who sets asteroid density?
**Question.** A space mission needs an asteroid-field density; the mockup uses one value (35). You asked on 2026-10-13 to see a prototype of the options first.
(a) One default for every mission. (b) The region decides, tight in some and open in others, within a range. (c) The mission type decides.
**Unblocks.** The lane D density work. Answer when the prototype shot arrives (it is owed).
<sub>key: Q-246-02</sub>

### 4. How does a big roster keep its shape?
**Question.** With 20 to 40 unit types per era, how do the three categories and six roles stretch?
(a) Every unit belongs to one of the three categories and one of the six roles; the orderings hold within each category (recommended). (b) Categories only, roles free. (c) A free roster, balanced by the scoring check alone.
**Unblocks.** The spec for the 20-to-40 type roster.
<sub>key: Q-082-03</sub>

### 5. Name the land era and the roster
**Question.** The land era is "The Marble Reach" as a placeholder; its name, setting, tone and scale, and the order of eras after the first two, are unwritten. Open: your words, or ask the Architect to draft candidates.
Name and brief the land era, write the roster in order, and mark each era earnable or purchase-only.
**Unblocks.** The era pack form, and the land era's identity and the roster the store sells.
<sub>key: Q-147-01</sub>

### 6. Firing arc
**Question.** You ruled on 2026-10-13 that a unit fires only inside an arc about its facing. Width, and whether it varies by type, are yours after the lab shows the effect.
(a) One arc for every type, 120 degrees as a draft the lab sweeps. (b) Width per category: Strike wide, Line medium, Siege narrow. (c) An arc for Siege only; the others fire all round.
**Unblocks.** The final arc rule. It comes after the lab chart, so it is later than its place in this list suggests.
<sub>key: Q-100-01</sub>

### 7. Can a force hold fire?
**Question.** A guard steps up to engage and returns to its post. Nothing lets you order a force to wait unseen and not shoot.
(a) A hold-fire setting on the guard stance. (b) A separate hold-fire order. (c) No hold fire; an ambush is made by going silent alone.
**Unblocks.** The movement lane, after the lab data.
<sub>key: Q-208-01</sub>

### 8. Who gets a ledger character in a team?
**Question.** A chapter has one commander today; how the economy seat of a pair and each sub-commander enter the chapter record and the ledger is unsettled.
(a) Only the commanding seat has a ledger character; the economy seat has none. (b) Every player has a ledger character and a lineage. (c) Other: your words.
**Unblocks.** Pairs reaching the chronicle.
<sub>key: Q-228-01</sub>

### 9. How is an era earned?
**Question.** Eras can be earned by play as well as bought; the condition is not set.
(a) Complete a 10-chapter campaign in the preceding era. (b) Reach Tier 3 in any campaign. (c) Other: your words.
**Unblocks.** Store work, after the beta.
<sub>key: Q-149-01</sub>

### 10. Which eras are purchase-only?
**Question.** Which eras are exclusive to purchase and which earnable, and the naming of the base three on the store. Open: your words.
**Unblocks.** Store work, after the beta.
<sub>key: Q-149-02</sub>

### 11. Show the internal figures on the website?
**Question.** The website refresh draft (built, not deployed) has a page on how the game is made. Does it publish the programme's internal figures?
Yes: publish the real figures. No: keep them out.
**Unblocks.** Nothing in the queue waits on it; decide with items 12, 13 and 14.
<sub>key: B22 part 1</sub>

### 12. Your name and quotes on the site?
**Question.** May the same draft name you and quote you?
Yes: name and quotes appear. No: the site speaks anonymously.
**Unblocks.** Nothing in the queue waits on it.
<sub>key: B22 part 2</sub>

### 13. Publish the site at all?
**Question.** The draft shows the galaxy view, both landscape engines, the walking prototype and the method page. Nothing deploys until you say.
Yes: publish after your read. No: hold it.
**Unblocks.** Nothing in the queue waits on it.
<sub>key: B22 publish</sub>

### 14. Is the method page the public face?
**Question.** A branch holds an outsider-readable page on how the game is built (tests first, prototypes approved before planning, a fight-measuring lab, ten draft pass marks).
(a) Yes, it stays an outsider page. (b) It becomes an internal page. (c) Not wanted.
**Unblocks.** How openly the project explains itself; nothing in the queue waits on it. Decide with items 11 to 13. The branch verdict is "land after named edits".
<sub>key: doc branch method ask 1 (docs/method)</sub>

## Parked by you

| id | topic | your parking words |
|---|---|---|
| Q-083-03 | How trait cards are earned | Post-launch work. |
| Q-132-02 | One silhouette per type | "Beta doesn't need to answer questions like this" (2026-10-07). |
| Q-159-09 | Disguising a building | "Skip this for now" (2026-10-07). |
| Q-238-01 | Drawing a disguised building | Follows the disguise design ("skipped for now", 2026-10-07). |
| Q-173-01 | How mission tech is derived | "Post-beta". |
| Q-173-02 | Tech levels per era | "Post-beta". |
| Q-165-01 | Travel lanes as a mode (also covers pacing tools in the layout kit) | "Only an idea, not a decision." |
| Q-180-01 | Form of the solo dial: three positions, a slider or a triangle | Asked with a shot when the economy lane reaches it. |

Everything else from the batch is in `batch_closed.md`.
