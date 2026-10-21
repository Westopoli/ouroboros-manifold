# What Westley decides, 2026-10-21

Answer in answers.md, one line per key: `<key>: <approve | reject | a | b | c | note>`. Anything not listed here is already decided or is the Architect's.

## 1. Pictures

## 2. Questions

### Q-B23b-01 Which renderer is the look?

Under the richer lighting the 3D ground wants, the see-through faction shells wash out the system dots (our pixel check reads 6 of 18); under the simpler lighting the checks use, the dots read fine. (picture ruled 2026-10-21; see the lane row).

(a) Ship the richer lighting, and the pixel check gains a run on it.  
(b) The wash is the approved look.  
(c) A small fix makes the shells fainter over the dots (the Architect's lean, shipping the richer path).

unblocks: the galaxy pixel test and fix piece.

### Q-C2-5-01 Owner colour at the dot

In the galaxy frame (P1), 14 of the 38 owned systems do not show their owner's colour at the dot: a neighbouring region's glow covers them or the additive light whitens the hue.

(a) That is the look you want; the colour test samples the wrong thing for those dots.  
(b) A glow must not cover a neighbour's dot.  
(c) The dot's core keeps its hue under the light.

unblocks: the galaxy pixel test's margin (it passes by one dot today).

### Q-156-02 Lab pass marks

The lab's ten draft pass marks (mirror tolerance, skill beating the noise, rank agreement, stacking, dominance, dead skills, counters) are unconfirmed.

(a) The draft marks as written.  
(b) You set each of the ten (opens ten per-mark questions).  
(c) Report only, no pass or fail, until you confirm them.

unblocks: lab rev 2 runs with real marks instead of drafts.

### Q-246-02 Who sets asteroid density?

A space mission needs an asteroid-field density; the mockup uses one value (35). You asked on 2026-10-13 to see a prototype of the options first. (picture ruled 2026-10-21; see the lane row) (the prototype shot is the one owed for this).

(a) One default for every mission.  
(b) The region decides, tight in some and open in others, within a range.  
(c) The mission type decides.

unblocks: the asteroid density work.

### Q-082-03 How does a big roster keep its shape?

With 20 to 40 unit types per era, how do the three categories and six roles stretch?

(a) Every unit belongs to one of the three categories and one of the six roles; the orderings hold within each category (recommended).  
(b) Categories only, roles free.  
(c) A free roster, balanced by the scoring check alone.

unblocks: the spec for the 20-to-40 type roster.

### Q-147-01 Name the land era and the roster

The land era is "The Marble Reach" as a placeholder; its name, setting, tone and scale, and the order of eras after the first two, are unwritten. Give your words, or ask the Architect to draft candidates; also write the roster in order and mark each era earnable or purchase-only.

unblocks: the era pack form, the land era's identity and the roster the store sells.

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

### C11 Building placement limits
The placement engine refuses a building on top of another placed building and refuses when the engine's lot table (8192) is full. Your words were "limits only from terrain" and "no lot count in the beta".
(a) the overlap refusal is physical and stays, the table size is a memory bound and is documented as not a rule (the Architect's reading); (b) remove the overlap refusal too: buildings may stack and the terrain alone limits; (c) something else.
unblocks: nothing today; the E1R shot.

### C12 September mockups without a verdict
Five September mockups (fog, hud, units, objectives, menus) have no recorded verdict from you.
(a) treat them as approved as built; (b) you look at each (commands in followups/01_transition.md section 1); (c) drop them.

### C13 Opening-frame camera pitch
The ground camera looks down 50 degrees. Your 10-18 note asked for about 15 more and "the classic RTS angle"; the research found StarCraft II and Warcraft III at 56, Age of Empires III at about 47, so the two asks point 9 to 20 degrees apart.
(a) 56, the StarCraft II angle; (b) 65, your plus 15; (c) restore the approved 55-degree lens first (it buys 10 of your 15 degrees at the top of the frame) and judge the pitch on the next shot.
unblocks: VG-A18-3d.

### C14 Where the empty half of the frame comes from
The army stands on the map's north edge and the camera faces north, so the map ends mid-screen.
(a) the opening camera faces away from the home edge toward the objective; (b) the home anchor moves inboard by the base pad (1200 wu); (c) both.
unblocks: VG-A18-3d's horizon test.

## Answered 2026-10-21 (chat)

- C1 "A": lab fight window widened to 230 s. DEC-C1-2026-10-21.
- C2 "B", improvable, investigate the convo: lab landing waits for under 30 s. DEC-C2-2026-10-21.
- C3 "yes": known-red list for the sim suites. DEC-C3-2026-10-21.
- C4 "Fix the issue before moving on": fix the G3 control first. DEC-C4-2026-10-21.
- C5 strongpoints can be shot, must be rebuilt; zones are captured. DEC-C5-2026-10-21.
- C6 "C": onboarding weights dropped. DEC-C6-2026-10-21.
- C7 "yes on all 3": housekeeping, widened removal rule. DEC-C7-2026-10-21.
- C8 "I believe I ruled on these already": Batch A 11 covers them. DEC-C8-2026-10-21.
- C9 "C": a quarter at a half share. DEC-C9-2026-10-21.
- C10 "A": two routes to every vantage and strategic point. DEC-C10-2026-10-21.

## 4. Drafts in force unless you veto

- DRAFT-b25-star-ref: 1080 px, 45 degree fov (Architect, 2026-10-21)
- DRAFT-startforce-pocket 400 wu, DRAFT-startforce-clamp 0.15, DRAFT-startforce-offset 200 wu (Architect, 2026-10-20)
- DRAFT-c25-patch-radius: 3 (Architect, 2026-10-21)
- Places lane drafts of rev 6a: DRAFT-shape-harm 0.5, DRAFT-first-ring-spread 2, DRAFT-field-cost-share 15 to 55 percent (Architect, 2026-10-21)
- Age-10 lots scope narrowing (Architect, 2026-10-21)

Parked by you (8): see batch_closed.md.
