# Spec-authoring investigation, 2026-10-11 (Westley's ask after drift item 5)

Westley rejected the two interim balance liberties from drift check e (placement refuses instead of clearing; the starting force is the whole force with free strongpoint production on top) and asked for the deeper question: this is the third build in a week that contradicted what he asked for (the settlement grown as a block at the map centre, the galaxy view unlike the approved prototype, and now these two). Two fresh Sonnet 5.5 engineers ran read-only on origin/main (f79f91c1): one traced both liberties from his words to the code, one classed every behaviour-defining sentence of the spec by its authority. Their reports are reproduced unedited in sections 2 and 3, as guard 7 requires. Section 1 is the Architect's diagnosis and the proposed fix, which waits on Westley.

## 1. Diagnosis and proposed fix (Architect, Fable)

**The mechanism that failed.** The chain is the same in all three cases. Westley's recorded answer is directional ("free placement, limits only from terrain"; "drop the split, the situation decides"; "the look is approved"). The Architect's spec turned it into a concrete behaviour, labelled "liberty", "Architect default" or "as the builder drafted", with the same standing in the text as his own words. The test writer wrote tests to that spec sentence, the builder built to those tests, and the gate certified the spec sentence, not his rule. In two of the three cases a builder's draft was then written back into the spec as the ruling. The bible was edited afterwards to match the code. No step compared the spec sentence to his words before the build; the only audit that did (drift check e) ran after landing.

**How wide it is.** Of 78 behaviour-defining decisions in spec rev 10, 39 trace to Westley, the bible or an approved prototype; 31 are Architect decisions, 4 are builder drafts, 4 have no source. All four builder drafts sit in lane E1 and two of the three failures come from them. The galaxy failure is the other shape: the spec said "look approved" and listed no geometry numbers, so the copy drifted with nothing to check it against. The placement contradiction was readable in the spec itself (two lines of the same spec disagree) and nobody was asked to look for that.

**Why the method rev 2 audits did not catch it.** The pre-launch audits checked internal consistency, code facts and interfaces. Only round 1 (2026-10-07) compared anything to the bible. The rev 10 audits are cited in commit messages and were not landed as reports. The audit brief never had a provenance column.

**Proposed fix (method rev 3, four rules, one lint, one test of the fix). Waits on Westley.**

1. *Every behaviour sentence in a spec carries a provenance tag, and only four kinds exist:* `[W Q-id]` (his words, the closed register row quoted), `[B R-id]` (the rule text quoted beside it), `[P path:line, approved <date>]` (a prototype or mockup, with the numbers copied by line), `[DRAFT-name]` (an open register row he sees before launch). The words "liberty", "Architect default" and "as the builder drafted" are banned from specs. An Architect decision is a DRAFT with a register row, nothing else; a builder's draft never enters the spec, it goes back to a Q row.
2. *A spec lint runs in every pre-flight:* `scripts/specfactory/spec_provenance.py` fails on a behaviour sentence (a number, a when/then, a visible element) without a tag, on a `[P]` tag without numbers by line, and on two sentences in one spec that cite the same piece with different behaviour. The test of the fix: run it on spec rev 10 and it must flag the 39 untraced rows, the two placement lines that disagree, and the "look approved 2026-10-07" line with no numbers; run it on rev 11 after the tags are added and it passes.
3. *The audit brief gains a provenance column* (W/B/P/DRAFT per sentence, with the quoted source checked against the register, the epic or the mockup file) and a "contradiction inside the spec" check; the audit report lands on main beside the spec, every round.
4. *The test writer's brief quotes the bible rule, not the spec's paraphrase,* as the "done when" of a rule piece; the auditor checks one positive test per rule clause (a rule that says "cleared and refilled" gets a clearing test; placement had none, which is why the gate was blind). A "copy the prototype" piece lists each constant with the prototype's value by line and ships a parity test over the two files.

**The two corrections (fix pieces, specs to follow once he picks the interim for B).**
- A, placement: `csrc/economy_place.c` clears the self-built lots whose cells fall inside the 5x5 footprint and lets growth refill the 2-cell ring (R-193-03, R-168-01); refusal only on an unwalkable or water cell (Q-168-01 (c), his words). The overlap-refusal tests in `tests/csim/test_VG_E_e1e.py:132` retire under a TD row citing the rules; new clearing tests with a positive control. E1q-lots' `footprint_blocked` test goes the same way.
- B, starting force: his answer was "drop the split, the situation (S-211) decides". S-211 is not built, so an interim is his to pick: (a) the whole force at start and strongpoint production charged to the holder's economy now (pulls the E2 charge forward); (b) the whole force at start and no strongpoint production until S-211 (every holder fields exactly F, R-126-04 holds); (c) production as today but the starting force reduced by what strongpoints will produce. Architect's recommendation: (b), the smallest change that honours R-126-04 and his answer; (a) is the eventual shape and costs an economy piece now.

## 2. Scout report A: provenance of the two liberties (Sonnet 5.5 engineer, read-only, unedited)

I could not remove the worktree. Both attempts at `git worktree remove --force` were denied by the permission system. It is still at `~/Projects/om-push/wt/scout-liberties`, detached at `origin/main`. Nothing was committed or pushed. The scout was read-only, so I did not write a `.wt-done` marker.

# Liberty A: placement refusal near any lot

- **bible_rule:**
  - R-193-03 (`E-17-map-generation.md:317`): "Given a building the player places, When it claims its footprint, Then the self-built pieces under it are cleared and the pieces around it are refilled."
  - R-168-01 (`E-22-economy-and-bases.md:55`): "it claims its footprint and the self-built pieces around it are cleared and refilled."
  - Both epic files last changed in `1a8bbe19` (2026-10-10, drift check d record). The 10-10 commit changed neither rule's text. The rules date from the 10-02 bible rewrite and the 10-07 batches.
- **first_spec_sentence:**
  - Spec rev 8, `b63f066a`, 2026-10-10, author line Co-Authored-By Claude Fable 5.1. Subject: "K-e2 amendment: spec rev 8, ...". Spec line 149: "E1e placement: as the builder drafted (... refused on an unwalkable cell or a cell inside an existing lot's footprint; edge-adjacent footprints accepted; the 2-cell ring is a ring only)."
  - Earlier spec revs (`3bbbc5f8` rev 1, `cf9a979b` rev 6) only name "E1e placement + footprint clearing (R-193-03, R-168-01)". They contain no refusal sentence.
  - The words "refused on unwalkable or occupied cells" first appear in a workflow brief, `6ec712dc` (2026-10-07), "wave scripts 5 (lane E1) ... written". That is Fable-authored (not checked).
- **westley_line:** none asking for the refusal. The nearest line is Q-168-01 (`ambiguity_register.md:372`), where Westley chose (c), "free placement with limits only from terrain", and said "#2 C" on 2026-10-06. That is the opposite of an obstruction rule. No Westley line mentions clearing, refilling or a 4-cell distance.
- **first_code_commit:**
  - `5554e23b`, 2026-10-10 02:57, subject "E1e: om_economy_place footprint, refusals, rubble refound". The author line is Co-Authored-By Claude Sonnet 5.5.
  - The first file commit for `economy_place.c` (`1c265472`) was the stub. The `E1E_OVERLAP` name arrived in `ae086faa` (2026-10-10 04:41, "name place return codes and overlap span so the constants lint passes"), which only renamed literals.
  - The code header says "liberty 2026-10-10 ... the 2-cell ring is ring only and not checked". The commit messages cite no spec line, TD row or brief.
  - The code refuses when any lot (natural lots included) is within `E1E_SPAN` = 4 cells (`economy_place.c:46`). Nothing is cleared.
- **tests:**
  - `tests/csim/test_VG_E_e1e.py:132` (`test_overlapping_footprint_is_refused`, docstring "centres 4 apart share a column") and `:141` (`test_adjacent_footprint_is_accepted`). Added in `2221ce52`, 2026-10-09 23:50, "VG E1e tests: free placement on terrain, footprint refusals (R-168-01, R-193-03)".
  - That is before the code (10-10 02:57). It is on a different branch: tests on `push/vg-e1e-tests`, code on `push/vg-e1e-2`. Both are Sonnet 5.5.
  - The test header says refusal is for a cell "already claimed by an earlier placement". It asserts no clearing and no refill. No test anywhere checks that placing clears lots.
- **brief_sentence:**
  - `vg-resume-laneE1a.js:22` (also `vg-wave5-laneE1.js:21`): "a footprint of 5x5 cells cleared with a 2-cell refill ring (R-193-03, the mockup's rule), refused on unwalkable or occupied cells".
  - The a2 builder brief (`vg-wave5-laneE1a2.js:38`) says only: "Fill om_economy_place per the E1e ruling (footprint, refusals, the rubble-strongpoint refound...). Done when tests/csim/test_VG_E_e1e.py is green."
  - The brief mentions clearing, but "Done when" is the test file, which has no clearing assertion.
- **chain:** Westley wrote the rules in the bible. The Architect's wave-5 brief (10-07) compressed them to "cleared ... refused on occupied cells". A Sonnet test writer (10-09) defined "occupied" as a shared footprint cell and wrote no clearing test. A Sonnet builder (10-10) implemented against those tests, with "liberty 2026-10-10" in a code comment. The Architect then recorded the result in spec rev 8 as "as the builder drafted", with no Westley line behind it.

# Liberty B: starting force is F, reinforcement capacity 0

- **bible_rule:**
  - R-126-04 (`E-15-...md:37`): "a player who holds every structure the whole mission fields at least F, and one who holds none fields 0.20 · F".
  - R-218-06 (`E-15:128`) now reads: "the split of R-126-04 ... is dropped and the situation (E-10 S-211) decides; until S-211 the starting force is the whole force and the reinforcement capacity is 0 (Westley, 2026-10-06; liberty, Architect 2026-10-10)".
  - The "until S-211 ... whole force ... 0" clause was added to the bible by `1a8bbe19`, drift check d, 2026-10-10, after the code existed.
  - R-218-06 text originates in `829f2444` (2026-10-06, "Record Westley's batch 12"): "the split of R-126-04 ... is dropped and the situation (E-10 S-211) decides (Westley, 2026-10-06)".
  - R-126-04's 0.20 / 0.80 split comes from Q-127-01, "set now the other way: starting force 20 percent ... Westley, 2026-09-15" (`ambiguity_register.md:158`).
- **first_spec_sentence:** `b63f066a`, 2026-10-10, Co-Authored-By Claude Fable 5.1, spec line 143: "`om_mission_compute_starting_force(F)` returns F (the whole force at the start; liberty 2026-10-10 until E-10 S-211 is built: the situation then decides) and `om_mission_compute_reinforcement_capacity` returns 0 (strongpoint production is paid by the holder's economy, R-218-03, not pre-allocated)." It also deletes the R-126-04 test under TD-VG-E-2, citing "R-218-06, Westley 2026-10-06".
- **westley_line:**
  - Q-218-04 (`ambiguity_register.md:462`): "(b), the split is dropped and the situation (S-211) decides. Westley, 2026-10-06, verbatim: '4: b'."
  - That asks for dropping the split, with the situation (S-211) deciding. It does not ask for "starting force = F" or "capacity 0".
  - Q-211-02 (`:440`) is still open. Westley says there that he "wants to explore (a) ... with more context". The register notes Q-218-04 needed the code owner to know it was answered, and Q-218-04 itself says nothing about the interim value.
  - Every line giving the interim value (F, 0) is Architect or builder.
- **first_code_commit:** `1c265472`, 2026-10-10 01:22, "K-e2 + E1i: economy entries, six calls, R-218-01/05/06 edits". The author line is Co-Authored-By Claude Sonnet 5.5. The code comment reads "R-218-06, liberty 2026-10-10 until E-10 S-211". The message cites no spec line, TD row or brief. The spec paragraph (E1i, and the K-e2 amendment) is the source.
- **tests:**
  - `tests/csim/test_VG_E_ke2.py:110` (`== F`) and `:117` (capacity `== 0.0`). Added in `a060cac2`, 2026-10-10 01:04, "K-e2 tests: entry points, R-218-01/05/06 (red on main)". That is before the code (01:22).
  - A different branch: tests on `push/vg-ke2-tests`, code on the K-e2 branch. Both are Sonnet 5.5.
  - `test_VG_E_e1h.py:305` asserts only that the result is not 0.20 F.
  - The old R-126-04 test was deleted under TD-VG-E-2.
- **brief_sentence:**
  - `vg-wave5-laneE1a2.js:24` (test writer): "om_mission_compute_starting_force(1000.0) == 1000.0 and om_mission_compute_reinf..." (cut off by my column slice).
  - The builder was told to apply "the six calls and the three rule edits exactly as the spec's 'E1i' paragraph says, nothing more".
  - The lane E1 original brief (`vg-resume-laneE1a.js:25`, E1h) said only "R-218-06 no fixed force split".
- **chain:** Westley chose "4: b" (drop the split; S-211 decides) on 2026-10-06. The Architect (Fable) wrote the interim "F and 0" into spec rev 8 and called it a liberty. Sonnet wrote the test, then Sonnet wrote the code. The bible gained the matching wording four days later in a drift-check record.

# Common pattern

Each time, Westley's recorded answer is directional (free placement with terrain-only limits; drop the split and let the situation decide). The Architect's spec turned it into a concrete interim behaviour labelled "liberty". Tests were written to the spec before the code, so they certify the liberty, not Westley's rule. Neither liberty appears in a Westley line. In both cases the bible text was later edited or left standing without the interim value being put to him.

Placement also has no test for the clearing the rules require, so the mismatch was invisible to the gate.

## 3. Scout report B: authority of every behaviour sentence in spec rev 10 (Sonnet 5.5 engineer, read-only, unedited)

The audit is done and the scout-provenance worktree is removed. About half of the 78 behaviour-defining decisions in the spec (rev 10 on origin/main) trace to Westley, the bible or an approved prototype. The other half were decided by the Architect, a builder draft, or nobody.

## Table

Spec line numbers are as of rev 10. The table lists the rows that matter most; the full 78 are in the totals.

| Line | Sentence (trimmed) | Class | Evidence |
|---|---|---|---|
| 62 | S-009 blocked: no occlusion mark, vision tube instead | W | Q-009-02 closed, verbatim |
| 62 | S-132 silhouettes parked | W | Q-132-02 open, but his "skip, post-beta" words are in the row |
| 67 | A1 HP bar above, layer ring beneath, selection ring | B | R-104-10 matches |
| 70 | A3 inactive dimming 0.4 | U | none |
| 75 | A7 groups 1-0, Ctrl+digit, double-press centres | B | R-104-07, R-105-02 |
| 75 | A7 double-click same type | U | none |
| 77 | A8 four beats | B | R-104-01 |
| 77 | A8 threshold crossing 25/50/75/100; banner 4 s | A, U | The bible says "threshold crossed" with no numbers; the spec's own liberty list (l.280) carries 25/50/75/100; the 4 s banner has no source |
| 78 | A9 per-type shot categories | B? | R-134-05 covers Settled Reach only |
| 79 | A10 0.5 s, 30 s, cap 150 | B | R-136-01, R-136-03 |
| 80 | A11 edge scroll 60 px | U | none |
| 86 | Lane B "look approved 2026-10-07" | P | `scenes/mockups/galaxy/` exists; the spec does not say who approved it (the programme file says Westley) |
| 91 | B22 R_BALL 71 (the prototype's 100, rescaled) | A | "liberty" in the spec |
| 91-93 | MIN_SPACING 22, INFLUENCE_RADIUS 28, POINT_RADIUS 1.4, camera min/max/focus | P | the prototype branch, cited by line |
| 94 | Camera default distance 50; "density parity chosen over ratio parity" | A | R-106-03 only gives the 40 to 65 band |
| 94 | TD-VG-B-12 "a fifth of the systems in the viewport" | A | none |
| 101 | Flyer altitude layer floor + 150 wu | A | liberty list l.280 |
| 105 | D8 spawn pockets, "Westley 2026-10-09" | A | no register row or quote found |
| 115 | Placing is a player command | A | contradicts R-168-01 ("paired economy player") and Q-159-03/Q-242-02 (a solo commander never places) |
| 117 | E1e "footprint clearing (R-193-03, R-168-01)" | B | matches the rules |
| 142-143 | R-218-05 and R-218-06 edits | B / B? | rule text has Westley 2026-10-06 plus an Architect 2026-10-10 amendment |
| 146 | E1b "a ring grows when tick % 60 == 0", slope within 50 wu | D | builder draft; contradicts R-193-01 "never form rings"; retired in rev 10 |
| 147 | E1c base `push/vg-e1c` (the 10x10 block) | D | spec l.210 admits it was a builder draft |
| 149 | E1e "as the builder drafted... refused on a cell inside an existing lot's footprint" | D | contradicts R-193-03 |
| 150 | E1h best slope = longest; midpoint; no drift | A / B? | R-218-01, R-218-07 |
| 151 | E1g doctrine unset default deferred | W | Q-233-01 closed ("unset until the player sets it"), but the default shipped contradicts it (Q-E1-02 open) |
| 187 | E1k mockup proportions, cliff 0.22 / stage 3, 20-frame ease | P | the settlement mockup |
| 187 | E1k street ribbons within 3 cells | A | liberty |
| 189-193 | E1l box 2x3, E1o ghost and 1 s flash, E1p panel position | A | liberties |
| 210 | Westley "far too circular"; the lot block and ring field were "a builder draft written into spec rev 8 by the Architect; no Westley decision asked for either" | D | the spec says so itself |
| 212, 216-220 | E1q growth constants, 60-tick step, 8-neighbour order, lane gap, shore margin | P | cited to the mockup by line (mockup "approved 2026-10-06") |
| 216 | econ term | W | Q-222-01 closed (a) |
| 216 | core = mission objective | A | Q-193-07 is open; the interim ruling is dated 2026-10-11 |
| 220 | Five stages | W | Q-193-02 |
| 220 | Thresholds 0.10/0.22/0.38/0.58 | P | mockup; the spec (l.280) and ROADMAP say "his numbers", still awaiting his approval |
| 220-226 | LOT_RISE_TICKS 20, OM_LOT_CAP 2048, 2 ms budget, symmetry 4 ulps, "lot count above 36" | A | named drafts |
| 220 | "Placement keeps its overlap refusal; R-193-03 clearing stays E2" | A | defers a bible rule |
| 228 | Solo commander's "production placement (Westley 2026-10-10)" lands in E2 | A | no register row or verbatim quote found |
| 288 | Go line waives the Definition of Ready and open-flag rule | W | Q-PROG-01 closed, verbatim |

## Totals

| Class | Count |
|---|---|
| W (Westley) | 8 |
| B (bible) | 14 |
| B? (loose match) | 5 |
| P (prototype/mockup) | 12 |
| A (Architect) | 31 |
| D (builder draft) | 4 |
| U (no source) | 4 |
| Total | 78 |

- **Traced to Westley, bible or prototype:** W + B + B? + P is 39 of 78, which is 50%.
- **A, D or U:** 39 of 78. Half of those (17 A and all 4 D) sit in lane E1.
- **P rows:** several rest on "approved 2026-10-06" for a mockup whose numbers ROADMAP still calls "his" and not yet approved.

| Lane | W | B | B? | P | A | D | U | Total |
|---|---|---|---|---|---|---|---|---|
| A | 3 | 9 | 1 | 0 | 3 | 0 | 4 | 20 |
| K | 0 | 1 | 0 | 0 | 3 | 0 | 0 | 4 |
| B | 0 | 1 | 0 | 5 | 4 | 0 | 0 | 10 |
| C | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 3 |
| D | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 2 |
| E1 | 3 | 3 | 4 | 7 | 17 | 4 | 0 | 38 |
| F | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| program-level (go line) | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |

Lane F has no behaviour sentences, only plumbing.

## Three failures

**1. Settlement grown as a block at the centre**
- **Spec sentence:** l.146 "a ring grows when `tick % 60 == 0` ... Steepness per cell is 1 when a slope segment passes within 50 wu; this replaces the mockup's per-cell scalar." l.147 "`push/vg-e1c` (007370dc) is the base."
- **Contradicted line:** R-193-01 "districts follow rivers, coasts and contour lines and never form rings"; the approved settlement mockup.
- **Visible from the spec alone:**
  - The ring is visible in l.146, and l.146 states that it replaces the mockup's field.
  - The 10x10 block at the canvas centre is not visible. The spec names a branch sha for it and nothing more, and a later grep confirms l.210 is the only place the block is described.
- **Flagged as a gap:** no. It was written as a ruling. The first admission is l.210, after Westley rejected the shot.

**2. Galaxy unlike the approved prototype**
- **Spec sentence:** before rev 10d, lane B (l.86-88) said only "look approved 2026-10-07". B0 measured shader equivalence (FIELD-EQ) on the 80-region fixture, not layout.
- **Contradicted line:** the prototype is a uniform ball of radius 100 with spacing 22 (`galaxy_gen.gd:8-11, 44-61` on the branch). Main packed a flat disc of radius 40 with spacing 3 (`galaxy_gen.gd:8-11`).
- **Visible from the spec alone:** no. Disc, radius and CIV_SCALE first appear in l.90-94, written after Westley rejected S-106, S-107 and S-108. The spec asserted approval of the look and never listed the geometry numbers.
- **Flagged as a gap:** no. The 80-region fixture was mentioned, but the density mismatch was not.
- **Bible side:** the shell shader and bands already matched the prototype, and R-106-03's bands are those same numbers.

**3. Placement refuses instead of clearing**
- **Spec sentence:** l.149 "E1e placement: as the builder drafted ... refused on an unwalkable cell or a cell inside an existing lot's footprint". l.117 lists the same piece as "placement + footprint clearing (R-193-03, R-168-01)".
- **Contradicted line:** R-193-03 "the self-built pieces under it are cleared and the pieces around it are refilled"; R-168-01 says the same.
- **Visible from the spec alone:** yes. Two lines of the same spec disagree, and l.149 carries the label "as the builder drafted".
- **Flagged as a gap:** not at ruling time. It was flagged afterwards, by drift check e on 2026-10-10 (finding 1) and then in l.220 and l.228 ("clearing stays E2"; "placement near a grown town is mostly refused"). R-168-01 is also scoped to a "paired economy player", while l.115 makes place a command for everyone. That contradiction is still in the spec.

## Audits

- **Spec audits on main:** `plans/archive/audits/audits_2026-10-07/` holds round1-opus (rev 1), round1-parallelism, round2-opus (rev 2), round3-opus (rev 3) and lab-drift. All are dated 2026-10-07.
- **What they checked:**
  - Round 1 did check the bible. It caught A4's remembered positions against R-089-04, "builders get choices the bible already fixes", and the Q-166-02 and Q-219-02 guesses.
  - Rounds 2 and 3 checked internal consistency, code facts, existing getters, owners and mechanisms. None has a provenance column.
- **Rev 10 and B22 audits:** the rev 10b to 10e and B22 commit messages cite three to four "fresh audits", but I found no report for them on main. The findings the commit titles list (save order, pins, ABI, compile safety, load checks) are interface and mechanism items. The titles give no sign of a bible or Westley check.
- **Drift checks:** `plans/archive/audits/drift_checks/` has five reports (2026-10-09, 09-b, 09-c, 10-10, 10-10-e). Drift check e is the only one that checked rulings against rules and Westley's words. It ran after E1e had landed, and it caught failure 3, the solo-placement contradiction, the doctrine default and the building roles.
- **Not caught:** no audit caught the centre block, the galaxy geometry or the settlement ring field. Drift check e item 14 noted the density port was partial but did not call it a ring.
- **Who approved:** the CLAUDE.md "Audit" bullet says Westley approves after the audit. The go line (Q-PROG-01) covers the rev 4 launch. I found no recorded Westley approval of rev 5 to rev 10 rulings.

## Summary

- 50% of the 78 behaviour decisions trace to Westley, the bible or an approved prototype. The other 39 are Architect decisions (31), builder drafts (4) and unsourced numbers (4).
- All four D rows are in lane E1, and two of Westley's three failures come from them. The third (galaxy) came from missing geometry numbers, not from a wrong ruling.
- In all three failures the divergence was knowable only after Westley saw the result. The spec flagged it itself in none of them before building. Failure 3's contradiction was visible in the text and unmarked.
- Pre-launch audits (rounds 1 to 3) checked consistency and code facts, with one partial bible pass in round 1. The only audit that compared rulings to Westley's words ran after landing.
- Two Westley dates in the spec ("D8, Westley 2026-10-09" and "solo production placement, Westley 2026-10-10") have no register row or verbatim quote I could find.
