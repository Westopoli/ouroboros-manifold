# Piecemeal, then whole: the proposal for amending the lab documents

Status: DECIDED as a plan, 2026-11-02; built after the simulation lab is finished. Westley's answers are in section 7a. The plan of record for the idea is `docs/northstar/research/layer_dynamics/decomposition.md`; this file is the proposal and its history, and where the two differ `decomposition.md` wins (DEC-piecemeal-then-whole-2026-11-02, DEC-piecemeal-answers-2026-11-02). Nothing here changes the lab's order of work, a staircase stage or a story in flight.

## 1. What Westley asked

After the stage 2 pictures, 2026-11-02: "only testing *all* the variables might not be as informative as what we're doing now. Maybe a single simulation lab run of a single configuration should not only run *all* of them in a single fight, but specific layouts like what we're doing now, maybe individual segments (like role interactions) might not pass (lines don't cross), but when all the variables are included the lines do cross. What exactly that means I do not yet know, but I think the simulation lab would provide better data if we ran things piecemeal, and then all together, for each configuration, instead of only together." Two rules he gave in the same message: a lopsided result at equal counts and roles is a flag, "only a signal, not a conclusion" (L-0104); and an era configuration whose roster breaks the category triangle "would be flagged as invalid ... siege is designed to beat line, even double the force of line shouldn't beat siege" (L-0102).

## 2. What the lab documents say today

- `docs/northstar/plans/2026-10-27-lab-plan-of-record.md` section 1: the lab is finished when the crossings are documented for every knob family and every skill (landscape, formation, layers, enemy position, unit-type matchup): the regions where the skilled smaller force wins, the crossing points as headcount ratio against the knob. Every run in that plan is a whole fight: all five skills' plays are variations of one full fight with everything on; a skill is measured against its matched control arm, not against the other skills taken alone.
- `docs/northstar/research/layer_dynamics/README.md` section 2 (principle: number of units firing decides; "with everything identical the larger force wins" is the control), section 3 (five skills), section 4 (the measure: break-even headcount, margin, units firing, and two predictions per fight, count-only and type-weighted, both read from the opening window of a fight that ran whole), section 5 (how results are read: one page, a diagram per notable).
- `docs/northstar/story_reviews/westley/lab-staircase.md` (the staircase): adds one factor per stage. This is incremental, and each stage's fights run with all factors added so far. Nothing keeps the earlier stage's result as a column beside the later one, and nothing tests a role interaction on its own: stage 2 puts all six roles on one field in mixed layouts. Stage 6 (the scan) scales headcounts of complete layouts only.
- `docs/northstar/research/layer_dynamics/heuristics.md` and `docs/northstar/story_reviews/westley/crossings.md`: his percentages per layout kind and his per-picture reasoning (new today).

## 3. The gap

The lab answers "does this complete configuration cross?". It cannot answer "which part carried it, and which part fails alone?". L-0102 shows why that matters: a complete fight (16 Bastion against 32 Vanguard) failed, and the failure is a property of one role pair, visible without any layout. Stage 1 to 7 will keep adding factors, so every later fight will mix more causes into one number.

Rough arithmetic for L-0102, from the roster (E-11 R-082-01 and the category multipliers), ignoring range and arcs: a Bastion hits a Vanguard for 10.5 (Siege against Line 1.5) every 1.8 s, 5.83 per second; a Vanguard hits a Bastion for 5.62 (Line against Siege 0.75) every 1.2 s, 4.69 per second. 16 Bastions deal 93 per second against 16,000 Vanguard hit points: 172 s. 32 Vanguards deal 150 per second against 16,800 Bastion hit points: 112 s. The pair loses at 2:1 on these numbers and wins at 1:1 (93 against 75 per second, 16,800 against 8,000 hit points). The measured fight (7 Vanguards left at tick 6080) agrees in direction. This is an estimate, not a finding by the lab.

## 4. The proposal: a decomposition ladder per configuration

For each configuration (an era's roster values, plus a layout and orders when one is given), the lab runs the same configuration in several arms and reports them side by side. The whole arm is what the lab runs today.

| Arm | What is on | What it answers |
|---|---|---|
| R: role pairs | two roles only, flat field, mirrored positions, no features, one orders rule | for every ordered role pair, where the lines cross as the headcount of each side varies (break-even headcount, margin, units firing), as a curve or a map, with every crossing region it shows; no fixed ratio such as 1:1, 2:1 or 1:2 is a pass or a fail (Q2 in section 7a; `decomposition.md` section 3) |
| F: one factor | the whole force, one factor at a time off its neutral setting. The list is provisional and expands when the variables are specified concretely (Q3 in section 7a): positioning (arc, surround), formation (block, interleaved), terrain features, sight, height bands, orders | what each factor does to the firing count and the result alone |
| P: factor pairs (selected) | two factors together where a stage suspects an interaction (arc plus choke) | whether two factors that fail alone cross together |
| W: whole | everything on, the layout as authored | the result the lab reports today |

Reporting, one table per configuration, in `docs/northstar/story_reviews/westley/crossings.md` (its columns would grow by `parts` and `whole` when this is built): rows are the arms, columns are the winner, the margin, the firing counts, and a flag column. Four readings, each named in words on the page: all pass; the parts pass and the whole fails; a part fails and the whole crosses (Westley's case); all fail. Flags are signals, never verdicts (his L-0104 words); a configuration is invalid only by a rule he states (today only the L-0102 sentence in section 1).

Era configuration check (the L-0102 rule made mechanical, later): arm R run over a roster prints, per role pair, the crossing it finds and flags a pair that contradicts a rule he has stated; a roster with such a flag goes back to him, not to a release.

What stays as it is: fights end by elimination or a flagged stall; seeds are deterministic until later stages add variance; his percentages remain heuristic targets, unscored; the staircase order is the build order of the factors, and the same list is the F arm's list.

## 5. What was recorded on 2026-11-02, and where

Recorded, in documents only:

1. `docs/northstar/research/layer_dynamics/decomposition.md` (new): the idea in his words, the seven strategic-depth preconditions it keeps, the arms (R as crossing curves, F provisional, P, W), what is decided and what is not, and when.
2. `docs/northstar/research/layer_dynamics/README.md`: a "Parts and whole" bullet in section 2, a pointer in section 8 step 7, and three open items in section 12.
3. The plan of record and the staircase: section 6 of `docs/northstar/plans/2026-10-27-lab-plan-of-record.md` ("After the lab") and one paragraph after the stage 7 section of `docs/northstar/story_reviews/westley/lab-staircase.md`. Neither adds a step, a stage or a done-when.
4. `docs/northstar/ROADMAP.md` section 1: one lab row, no story yet.
5. `docs/northstar/story_reviews/westley/decisions.md`: DEC-piecemeal-then-whole-2026-11-02 now Decided as a plan, and DEC-piecemeal-answers-2026-11-02.

NOT done (deferred until the build, which comes after the lab is finished; Westley, 2026-11-02): the per-stage "Arms" lines in the staircase and the "done when" sentences about with-and-without strips; the story-template `Arms:` line; the additions to the plan of record's section 1 ("Finished") and its order of work; the `parts` and `whole` columns of `crossings.md`; the README section 4 and 5 additions; any story for arm R, arm F or the era check.

## 6. First deliverable, cheap and useful at once (PARKED)

Parked: Westley acts on this topic after the simulation lab is complete. No story H-064 exists and none is Ready; the sizing below used the fixed ratios 1:1, 2:1 and 1:2, which the crossing-curve wording of section 4 replaces.

Arm R on today's roster: 36 ordered role pairs at 1:1, 2:1 and 1:2 is 108 fights of the arena runner, about 18 seconds each (stage 1 measure), under an hour serial and minutes parallel, one seed each (deterministic). Output: a 6 by 6 table of winners and margins, the triangle edges marked PASS or FLAG, and the L-0102 pair (Bastion against Vanguard at 1:2) among them. It needs only the existing runner plus a layout generator for pure role pairs; no new engine behaviour. Whether it is the first story, and how arm R scans, is decided when this is specified, after the lab.

## 7. Questions for Westley (player-level)

1. The triangle: are the three edges exactly Siege beats Line, Strike beats Siege, Line beats Strike, each holding at 2:1 for the weaker category (his L-0102 words give the first edge)? Is there a fourth rule, for example no role beats every other role (a dominant role)?
2. Does Strike against Line (the weak edge) also have a headcount at which it should still win, or may it simply lose at any ratio?
3. Factor list for arm F: positioning, formation, terrain, sight, height bands, orders. Anything missing, anything he would never test alone?
4. Should a failing pair block a configuration from the later batches (the plan's step order), or only flag it?

## 7a. Answers (Westley, 2026-11-02)

Verbatim, to the questions of section 7 (his spelling kept):

- Q1: "No additional rules needed."
  Changed: no rule is added beyond the triangle (which way each category's advantage points) and his L-0102 sentence; there is no fourth rule such as "no dominant role".
- Q2: "it does not have a headcount, this can vary where the lines cross. Strategic depth can't be diluted to a specific number as simple as that, there's extensive research/documentation on strategic depth in the repo, read it BEFORE you start updating documentation as this plan specifies. Use the context from that when updating the documentation, those preconditions are vitally important for the effectiveness of the simulation lab. There may be multiple "headcounts" in which strategic depth is induced."
  Changed: the weak edge has no required headcount; arm R reports where the lines cross (a curve or a map, possibly several crossing regions), not pass or fail at fixed ratios; the strategic-depth preconditions are written into `decomposition.md` section 2.
- Q3: "Beyond F I'd just say let's make sure we ammend the documentation regarding this piecemeal idea we're planning. When it comes time to specificy, very concretely and specifically, all the different variables, we may want to expand this list. Make sure that's clear in the documentation."
  Changed: the arm F list is provisional and expandable, and the documents say so; the amendments of section 5 are made.
- Q4: "Flag it, how we'll do that is a decision for a later time when we're actually building this (post simulation lab creation)."
  Changed: a failing pair is flagged; whether a flag ever blocks a configuration from later batches is decided at build time, after the lab.

He added that this topic is acted on after the simulation lab is complete: the amendments record the plan and change no order of work.
