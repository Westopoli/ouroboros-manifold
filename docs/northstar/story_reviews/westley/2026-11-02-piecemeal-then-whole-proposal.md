# Piecemeal, then whole: a draft proposal for amending the lab documents

Status: DRAFT proposal, 2026-11-02 (Architect). Nothing in the lab documents is changed by this file; the amendments in section 5 are made only after Westley reads it and rules (DEC-piecemeal-then-whole-2026-11-02, status Proposed).

## 1. What Westley asked

After the stage 2 pictures, 2026-11-02: "only testing *all* the variables might not be as informative as what we're doing now. Maybe a single simulation lab run of a single configuration should not only run *all* of them in a single fight, but specific layouts like what we're doing now, maybe individual segments (like role interactions) might not pass (lines don't cross), but when all the variables are included the lines do cross. What exactly that means I do not yet know, but I think the simulation lab would provide better data if we ran things piecemeal, and then all together, for each configuration, instead of only together." Two rules he gave in the same message: a lopsided result at equal counts and roles is a flag, "only a signal, not a conclusion" (L-0104); and an era configuration whose roster breaks the category triangle "would be flagged as invalid ... siege is designed to beat line, even double the force of line shouldn't beat siege" (L-0102).

## 2. What the lab documents say today

- `docs/northstar/plans/2026-10-27-lab-plan-of-record.md` section 1: the lab is finished when the crossings are documented for every knob family and every skill (landscape, formation, layers, enemy position, unit-type matchup): the regions where the skilled smaller force wins, the crossing points as headcount ratio against the knob. Every run in that plan is a whole fight: all five skills' plays are variations of one full fight with everything on; a skill is measured against its matched control arm, not against the other skills taken alone.
- `docs/northstar/research/layer_dynamics/README.md` section 2 (principle: number of units firing decides; "with everything identical the larger force wins" is the control), section 3 (five skills), section 4 (the measure: break-even headcount, margin, units firing, and two predictions per fight, count-only and type-weighted, both read from the opening window of a fight that ran whole), section 5 (how results are read: one page, a diagram per notable).
- `docs/northstar/plans/2026-10-31-lab-staircase.md` (the staircase): adds one factor per stage. This is incremental, and each stage's fights run with all factors added so far. Nothing keeps the earlier stage's result as a column beside the later one, and nothing tests a role interaction on its own: stage 2 puts all six roles on one field in mixed layouts. Stage 6 (the scan) scales headcounts of complete layouts only.
- `docs/northstar/research/layer_dynamics/heuristics.md` and `docs/northstar/story_reviews/westley/crossings.md`: his percentages per layout kind and his per-picture reasoning (new today).

## 3. The gap

The lab answers "does this complete configuration cross?". It cannot answer "which part carried it, and which part fails alone?". L-0102 shows why that matters: a complete fight (16 Bastion against 32 Vanguard) failed, and the failure is a property of one role pair, visible without any layout. Stage 1 to 7 will keep adding factors, so every later fight will mix more causes into one number.

Rough arithmetic for L-0102, from the roster (E-11 R-082-01 and the category multipliers), ignoring range and arcs: a Bastion hits a Vanguard for 10.5 (Siege against Line 1.5) every 1.8 s, 5.83 per second; a Vanguard hits a Bastion for 5.62 (Line against Siege 0.75) every 1.2 s, 4.69 per second. 16 Bastions deal 93 per second against 16,000 Vanguard hit points: 172 s. 32 Vanguards deal 150 per second against 16,800 Bastion hit points: 112 s. The pair loses at 2:1 on these numbers and wins at 1:1 (93 against 75 per second, 16,800 against 8,000 hit points). The measured fight (7 Vanguards left at tick 6080) agrees in direction. This is an estimate, not a finding by the lab.

## 4. The proposal: a decomposition ladder per configuration

For each configuration (an era's roster values, plus a layout and orders when one is given), the lab runs the same configuration in several arms and reports them side by side. The whole arm is what the lab runs today.

| Arm | What is on | What it answers |
|---|---|---|
| R: role pairs | two roles only, flat field, mirrored positions, no features, one orders rule; every ordered role pair at 1:1, 2:1 and 1:2 | do the roles hold the category triangle: Siege beats Line, Strike beats Siege, Line beats Strike, each even at 2:1 against it; does any role dominate or fail every pair |
| F: one factor | the whole force, one factor at a time off its neutral setting: positioning (arc, surround), formation (block, interleaved), terrain features, sight, height bands, orders | what each factor does to the firing count and the result alone |
| P: factor pairs (selected) | two factors together where a stage suspects an interaction (arc plus choke) | whether two factors that fail alone cross together |
| W: whole | everything on, the layout as authored | the result the lab reports today |

Reporting, one table per configuration, in `docs/northstar/story_reviews/westley/crossings.md` (its columns grow by `parts` and `whole`): rows are the arms, columns are the winner, the margin, the firing counts, and a flag column. Four readings, each named in words on the page: all pass; the parts pass and the whole fails; a part fails and the whole crosses (Westley's case); all fail. Flags are signals, never verdicts (his L-0104 words); a configuration is invalid only by a rule he states (the triangle at 2:1).

Era configuration check (the L-0102 rule made mechanical): arm R run over a roster file prints, per role pair, PASS or FLAG against the triangle; a roster with a FLAG on a triangle edge is "invalid: the lines are not crossing" and goes back to him, not to a release.

What stays as it is: fights end by elimination or a flagged stall; seeds are deterministic until later stages add variance; his percentages remain heuristic targets, unscored; the staircase order is the build order of the factors, and the same list is the F arm's list.

## 5. Amendments, file by file (applied only on his go)

1. `docs/northstar/plans/2026-10-27-lab-plan-of-record.md` section 1, "Finished": add that each documented crossing is accompanied by its decomposition (the R, F and W rows) and by the era-configuration check result; section 3 order of work gains step "arm R and the era check" before batch one, because a roster that fails the triangle makes the later batches measure a broken configuration.
2. `docs/northstar/research/layer_dynamics/README.md`: section 2 gains a bullet "Parts and whole" (a configuration is judged by its parts and by its whole, and a part may fail where the whole crosses); section 4 gains "The decomposition arms" with the table above and a pointer to `decomposition.md`; section 5 gains the interaction table as a page form; section 12 gains the open questions of section 7 below.
3. New `docs/northstar/research/layer_dynamics/decomposition.md`: the arm definitions, the triangle invariants in his words, the flag rule ("signal, not conclusion"), the report table.
4. `docs/northstar/plans/2026-10-31-lab-staircase.md`: every stage's layout block gains "Arms": the stage's layouts also run with the stage's new factor off (the stage 3 control strip of H-063 is the pattern, generalised), and stage 6's scan runs on arms F and W as well as complete layouts; "Done when" for each stage adds that the page shows the with and without strips.
5. `docs/northstar/story_reviews/westley/crossings.md`: columns `parts` and `whole`.
6. Story template (`docs/method/`, lab stage stories H-053, H-063 and after): a `Arms:` line per layout naming the arms the page must show.
7. A story for arm R and the era check (the cheapest first deliverable, section 6), and a later one for arm F as the staircase factors exist.

## 6. First deliverable, cheap and useful at once

Arm R on today's roster: 36 ordered role pairs at 1:1, 2:1 and 1:2 is 108 fights of the arena runner, about 18 seconds each (stage 1 measure), under an hour serial and minutes parallel, one seed each (deterministic). Output: a 6 by 6 table of winners and margins, the triangle edges marked PASS or FLAG, and the L-0102 pair (Bastion against Vanguard at 1:2) among them. It needs only the existing runner plus a layout generator for pure role pairs; no new engine behaviour. If he agrees, it is story H-064, Ready, and the Dispatcher runs it beside stage 3.

## 7. Questions for Westley (player-level)

1. The triangle: are the three edges exactly Siege beats Line, Strike beats Siege, Line beats Strike, each holding at 2:1 for the weaker category (his L-0102 words give the first edge)? Is there a fourth rule, for example no role beats every other role (a dominant role)?
2. Does Strike against Line (the weak edge) also have a headcount at which it should still win, or may it simply lose at any ratio?
3. Factor list for arm F: positioning, formation, terrain, sight, height bands, orders. Anything missing, anything he would never test alone?
4. Should a failing pair block a configuration from the later batches (the plan's step order), or only flag it?
