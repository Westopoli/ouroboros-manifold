# Audit: the skill lab against its plan and Westley's words (2026-10-04)

Auditor: Engineer (Sonnet 5.5), read-only except this file. Scope: the layer-lab plan of 2026-09-30/10-01, Westley's typed words in the two Mac transcripts, and what the Linux work has produced since. Westley's words below come from `docs/legacy/claude_exchange/transcripts/` (his own typed turns only, extracted by script). The Linux chats' transcripts are not in the repo, so every "Westley said" in the Linux documents dated after 2026-10-02 can be checked only against what those documents quote.

## 1. Largest drifts, in order

1. The search for regions of settings where the lines cross has not started and nothing is aimed at it. The two map forms built for it (`charts.py` `region_map_html`, `small_multiples_html`) are called by no batch; only their own tests use them.
2. Westley has been shown no chart from the real-engine lab. The only chart he ever saw is the 2026-10-01 toy-era sample (two drafts). Six real-engine pages exist as 0.07 to 1.2 MB HTML files in git; no link, artifact or screenshot of any is recorded.
3. Of seven batches defined in `batches.py`, two have been run (formation three times, focus fire twice). Matchup (S5), landscape (S1), enemy position (S4), layers (S3), combinations: defined, never run. Only S2 has ever been measured, and only with unconfirmed draft plays.
4. The last five days went to making the instrument and engine faithful (parity, leash, stand-off, shapes, stalls). The batches are "instrument checks", not results (A187, A197). Instrument work is real, but the plan's loop (small batch, read together, next step) has had zero turns with him.
5. Decisions the plan reserved for him were taken "provisionally overnight" under A165 (leash, guard stance, fling, pass marks, concentration of fire, roll-up counter, layer numbers, scale figures). He then said the pass-mark drafts would "dilute the strategic depth" (A209/A210); the others still stand unconfirmed (A211).
6. The newest batch (2026-10-04, branch `push/batches-1004`) reports break-evens of 10 to 12 for 16 units (15 to 16 on 10-03), 163 and 469 stalled fights in single cells, and pages with a margin of +0.56 labelled "lost". A lab rule ("mop-up order") nobody ruled on produced it. It is not yet a question about the instrument in its run file.
7. Page headings no longer state the finding in soldiers; the formation pages are headed "Skill lab formation batch". Only the 10-02 controls page headed itself "identical: 16 units beat 15".
8. Added scope: per-side target policy and a focus-fire batch (his request, but grown to 9,280 fights), mop-up order, guard order, approach control, a process pool, 7 batch definitions and a 32-combination profile before any one skill was settled.
9. The goal sentence is intact in every document; the pillar (units able to fire) is computed and charted per cell. Principle and measure have not drifted. Execution has.

## 2. Question by question

### Q1. Goal and "lines cross in multiple locations"

Asked: "players with better understanding of the landscape, unit formation, layer awareness/intentionality, and the other players current position can defeat a much larger force" (2026-10-01). And: "The *lines* can cross in multiple locations, there may be configurations where health/range/vision/ping distance is much higher/lower but the expected behavior is exhibited" (2026-10-02). Also: "My original intent was to shuffle *every* variable, vision, damange, range, literally everything" (2026-10-01).

Now: the goal and the multi-region sentence are carried correctly into the Linux plan (Goal, Phase E: "More than one region is a result, not a tie to break") and README 4. But no code path samples settings: batches vary the enemy's unit count and, in focus fire, one policy switch. `sample.py` and `scan.py` exist; Phase E "does not start until he sets them [pass marks]" and A209 then parks the marks until data exists. That is a circle: the search waits for marks, the marks wait for data, the data waits for batches that measure one skill on one map.

Drift: partial. The aim is stated; the work has narrowed to making the instrument and the engine correct. Correction: add one cell family now that varies a knob (reach against spacing, health against damage) over a grid on the formation map, and draw it with the existing `region_map_html`. Whole-fight break-even as the shaded variable needs no pass marks.

### Q2. Principle and measure

| Item | Asked | Computed | Shown on pages | Status |
|---|---|---|---|---|
| Units able to fire, per side, through the fight | "the number that we really care about is number of units firing" (2026-10-01) | Yes (`firing.py`, per-tick) | Yes: "units able to fire through one fight" chart per cell; firing unit-seconds in run files | Kept |
| Consistent over whole fight, not opening | "it's not just opening firing advantage, it's consistent firing advantage" | Series per tick, unit-seconds | Series shown for one exemplar fight per cell | Kept, one fight only |
| Margin | plan Part 1 | Yes | Yes, in table | Kept |
| Break-even, whole units | "16 beat 17 and lose to 18" | Yes (`breakeven.py`) | Yes, "beats N, loses to N+1" | Kept |
| Firing advantage beside every result | brief of 2026-10-01 | Yes (`evidence.py`) | Run files give side-0/side-1 unit-seconds; no advantage column | Partial |
| Result follows the firing count (C2) | "compare the amount of time and number for both" | Coded, tested | No page plots break-even against firing advantage | Dropped from pages |
| Conditions C0 to C9 | README 4 | C0 to C6 and the profile are coded and tested; no batch reports them | None | Parked by A210 |
| Weighted by unit type | "not just unit values but their type" | Partial | Matchup page not run | Not shown |

Notable: the fraction "beats N" stays but the 2026-10-04 page shows margin +0.561 with "lost" at 12 enemies, so the page's won/lost and its margin disagree (likely cap or stall handling; not explained in the run file).

### Q3. Readable output

Asked (2026-10-01, 2026-10-02): "small batches of tests, that produce output that both of us can read (using the visual artifact style you produced and more if the type of data we're looking at changes)". On the first draft: "it doesn't read well, I had to stare at it to figure out what it meant". On the second: "looks much better, especially the top graphic that makes it very clear." Plan named form: heading states finding in soldiers; fights by enemy size with won/lost dots and break-even marked; firing lines through the fight; table with plain words; "lines crossing" as a two-knob map.

| Page (all HTML with inline SVG, openable in a browser) | Form present | Gaps |
|---|---|---|
| `runs/2026-10-02_phase_b/controls_page.html` (and a duplicate in `2026-10-03_phase_b/`) | Heading with finding ("identical: 16 units beat 15."), fights-by-size chart, firing chart, table with "In words" | Closest to the approved form |
| `runs/2026-10-03_formation/formation_page.html` (v1), `2026-10-03_formation_v2/` | Per-cell chart, firing chart, plain-words table, 48 SVGs | Generic heading; no finding summary; 25 tables, 0.7 MB |
| `runs/2026-10-03_focus_fire_v2/`, `..._v3/` | Per-cell chart and table; v3 has no title at all | No headline; v2 lists three skills as "not expressed" |
| `origin/push/batches-1004:.../2026-10-04_formation/` | Same as v2 | Not on main; 1.2 MB; won/lost vs margin disagree |

The "lines crossing" map and small multiples are built (`charts.py`) and tested but are used by no batch. The Linux plan promised "chart forms beyond the controls page"; they exist and are unused.

Charts Westley has been shown: one design in two drafts, both on the Mac on 2026-10-01 to 10-02, made from toy data (https://claude.ai/artifact/WtQDNnNZTR8hqx6LpxBaJ2). Real-engine pages shown to him: none on record. `LEAVE_OFF.md`: "No chart page was made for Westley." Since then six pages were made; the rulings record none being opened, published or screenshotted. A207 even notes the space-kit passes "none has been opened by Westley". The pattern repeats.

Drift: lost. Correction: publish one page (the 10-03 formation v2 or a fresh controls page) as a private artifact with a finding headline, and record the link.

### Q4. Small batches, read together

Asked: "We don't need to do a large batch of thousands of 'runs' and then analyze the data, I think it'd be much faster to iteratively try small things, check the output, and tune repetatively" (relayed 2026-10-02, his instruction). Plan Part 5b: "Each batch ... read with Westley before the next."

Run so far: Phase B material (10-02), formation v1, formation v2, focus_fire v2, focus_fire v3, the four-stall trace, formation 10-04: seven run files, about 480 to 9,280 fights each (formation 28 minutes per run; the 10-04 CSV has 15,041 rows). Read with Westley: zero. Each was read by the Architect chat (A166, A187, A196, A197, A200). Westley wrote about the work on the record only through A199 (formation holds to shooting, "this is something we might change when it comes to play testing"), A209/A210 and W1 to W5.

Decisions taken for him that the plan reserved ("Still Westley's, asked when reached"):

| Ruling | Plan said | What happened |
|---|---|---|
| A168 leash stays at 0 | "he picks from the chart" | Architect, overnight; A188 then changed the leash rule (the pursuer, not the target), provisional |
| A170 guard stance built | "decided after movement lands ... Yes a guard stance is fine" (his, 10-02) | Built as an order on his phrase; the rule detail is the Architect's |
| A173 fling not ported | "One exception brought to Westley" | Architect, overnight |
| A174 pass marks, 0.05 margin | "Westley sets the pass marks" | Adopted as drafts; his reply in A209 objects |
| A174 concentration of fire out of the principle | "whether concentration of fire joins the principle" | Ruled out; v3 later gave it a number (under half a unit) |
| A174 roll-up counter, per-unit going dark, layer numbers, scale figures | each "brought to Westley" | All provisional, unconfirmed (A211) |
| A196/A198 per-side policy, walk-then-attack (a) | Lab-only choices | Architect; A198 flagged the rule meaning, he answered in A199 |

Drift: lost, and acknowledged in part by A209. Correction: bring one page, then ask only what the page shows.

### Q5. Five skills

| Skill | Plan play | In the lab today | Measured | Why not |
|---|---|---|---|---|
| S1 landscape | hold a choke, hold a slope top, cover | landscape batch defined; terrain and cover in engine; guard order built (A170) | No batch run. A choke scan on the 10-02 Phase B runs (`choke_scan.md`) only | ROADMAP: "waits on the guard stance" (M6), yet A170 built it; no one released it |
| S2 formation | concave, spread line, screen | line, blob, concave (120 degrees), column counter | Yes: three runs | Concave aims at the middle of the enemy front, not the arrival point (A145 and the plan asked for arrival); "spread line" equals "line"; the screen play absent |
| S3 layers | ping, dark, reach by type | engine G4 to G7 landed; layers batch defined | Not run | Waits |
| S4 enemy position | ping, bait, ambush | enemy-position batch defined; bait and fall-back are "not a single group order" | Not run | Needs timeline orders; hold-fire not an engine call (A145) |
| S5 matchup | rocks on scissors | matchup grid defined | Not run | Waits for the next batch |

A145 says no skilled play is written for S1, S3, S4, S5 "until its batch in Phase D, where the play is looked at before it is measured". The batches were never reached. The reach control (+20 percent reach beat 14) and the focus-fire cell stand in for S3/S5 as reference cells only.

### Q6. Lessons about method

| Lesson | Followed | Broken |
|---|---|---|
| Check text against his words | `crosscheck_2026-09-30/10-01/10-02`; A199 and A209 quote him | Group speed ruled "slowest member", recorded in the plan as his decision, while his 10-02 words were "make sure that we use the same exact logic from the python"; A125 gives no quote for it |
| Look at what a play does before measuring | Formation v2 section 1 prints shapes at contact; the stall trace; A187 and A198 | The v1 formation batch ran (480 fights) before the shapes were looked at; the plan said look first |
| One skill, one map, one size, then widen | Formation was the one skill first | The first formation run was 24 cells: three sizes, two unit types, four plays; the 10-04 CSV is 15,041 rows. The plan asked for 8 and 16 |
| A surprising result is a question about the instrument | A187, A197, A201 treat stalls and shapes as instrument faults | The 10-04 run (break-even 10 to 12; margin +0.56 "lost"; 469 stalls) is filed as results with no instrument question |

### Q7. Scope added; scope not started

Added, not in the original plan: the full tactical port parity (P1 to P9, 24 audit differences); per-side target policy; mop-up order (a lab rule; no ruling in `rulings-2`, only a ledger row `TD-SL-mopup-field-order`); approach control; process pool and `--workers`; a 32-combination skill profile; conditions C0 to C9 coded as functions; guard order; seven batch definitions at once; the worktree prune and playthrough gate (ROADMAP W1 to W5, not this lab).

Asked, not started: matchup, landscape, enemy position, layers and combinations batches; the knob batches (reach against spacing, health against damage, speed, vision, ping distance); the three lever tables side by side; the seer against the ping; the search (Phase E); the two-knob map; the decision-tree summary; folding results into `algorithms.md` and S-008; closing Q-008-02 and Q-008-03; the MVP client carry-over of the layer actions ("as soon as we've found the *lines crossing* data and we know it works", 2026-10-02).

### Q8. Recorded as Westley's decision, not found in his words

Checkable against the Mac transcripts (to 2026-10-02 16:42) only. Unverifiable here, because the Linux chat is not in the repo: the A125 list (slowest-member speed, unit in terrain pushed out, side's shared sight, siege needs a spotter, terrain blocks above 0.7, lone unit resumes, repulsion "perfect", focus-fire switch with the quote "I had imagined that units would only... just fire at the closest unit"). The quotes carry his voice; the paraphrases do not. Specifics:

- "Group speed: slowest member ... a ruled difference from the Python" listed as his decision. His only found words say the opposite ("the same exact logic from the python"). Needs his confirmation.
- "Whose sight gates fire: the side's shared sight" and "Siege needs eyes: Accepted": no matching words in the Mac transcripts. His words there concern the engine unit finding "the shortest path forward to a unit in its vision" (2026-10-02).
- "Lab runs both [leash]; he picks": no source found.
- "Guard stance": his words are "Yes a guard stance is fine"; A170 builds a full order with a rule (R-096-05).
- "Pass marks C0 to C9": the README says drafts are unconfirmed; his only restatement is "30 percent ... 3x as rough sizes" (Mac chat); the plan's "30 percent and 2x to 3x" is the README's wording, not his typed one found here.
- Q-005-04 and Q-001-05 "closed as provisional" by "AskUserQuestion, 2026-10-01": the answers were given in a tool dialog, not in typed text; unverifiable.

## 3. What to do this week

1. Publish one real-engine page (formation v2 or a fresh controls page) as a private artifact with a headline in soldiers, and put its link in `runs/README.md`. Count it as the first chart he has been shown.
2. Hold all new batches. Read the 10-04 formation run with the instrument first: why margin +0.56 shows "lost", what the 163 and 469 stalled fights are, and whether the mop-up rule is wanted. Ask him once about mop-up.
3. Run one small matchup (S5) cell at 16 and 8 units, one map, and publish its page. This is the cheapest next skill; the batch is already defined.
4. Release or restate the landscape hold: A170 built the guard stance; ROADMAP M6 still says the batch waits. Run one choke cell at one size.
5. Put one two-knob map on a page (reach against spacing, formation map, 16 units), drawn with `region_map_html`, shaded by break-even, with no pass marks. Show it to him.
6. Add a headline sentence (break-even in soldiers, firing counts) to the top of every batch page and cap batch size at the plan's 8 and 16 until he has read one.
7. Send him the list of "provisional overnight" rulings with context and a small diagram, only after item 1, and ask him to confirm or strike A125's items I could not source (section Q8).
8. Make the list of the skilled plays per skill from README 4.1a an explicit checklist in `runs/README.md`, with "built / measured / shown" per row, so a compact cannot lose it.
