# Requirement audit, 2026-11-17

First run of the weekly audit (`docs/method/requirement_audit.md`), started on Westley's word, at origin/main `2845f88f7`. Three fresh Sonnet auditors, read-only. Rows per rule are in `2026-11-17-requirement-audit/slice-1.md` (stage 4 rules of E-11 and E-12), `slice-2.md` (stage 4 rules of E-13, E-01 and E-17) and `slice-3.md` (the rotating epic, E-01 whole). The check of documents and tests against the rulings of 2026-11-17 is `2026-11-17-targeting-rulings-check.md`.

Scope: every rule the lab's stage 4 depends on (39), every rule changed since the backfill of 2026-11-11, and E-01 whole (87 rules, 7 Invariants). The beta stage was left out (Westley, 2026-11-11: the beta is not far enough along). One test was run (the single named proof in scope); every other statement about a test is a reading of its source.

## Result

| | Stage 4 rules (39) | E-01 whole (94) |
|---|---|---|
| Proven | 0 | 0 |
| Weak (a named proof that fails a qualification) | 0 | 1 |
| Missing (code, no qualifying test) | 37 | 73 |
| Unbuilt | 2 | 20 |
| Stale pointers or citations | 3 | 4 |
| Places the bible disagrees with itself | 16 | 24 rows, 13 not already numbered |

No rule that stage 4 depends on is proven. By the card, that blocks the stage's sign-off.

## What is closest

Seven stage 4 rules have a test that is one or two changes from qualifying. Each is a whole-run or scenario test in the lab's configuration; the usual failure is qualification 1 (the test does not quote the rule's current text) or 5 (no recorded break).

| Rule | What it says, short | Candidate | Fails |
|---|---|---|---|
| R-093-02 | a unit acquires and fires only at what its side sees | `tests/skilllab/arena/test_invariants_round2_wiring.py::test_R_093_02_no_shot_and_no_held_target_is_outside_the_sides_visible_set` | 1 |
| R-008-04 | reach across layers | the same test | 1, 5 |
| R-084-04 | no moving in the pause after a shot | `tests/skilllab/arena/test_engine_rules_f2_move_or_fire.py::test_R_084_04_no_unit_moves_in_the_pause_after_its_shot` | 1, part of 3 |
| R-083-03 | Warden healing does not stack | `tests/skilllab/arena/test_engine_rules_f4_wardens.py::test_R_083_03_no_unit_heals_more_than_one_wardens_0_075_in_a_tick` | 1, 2 |
| R-097-10 | idle own units step aside | `tests/skilllab/arena/test_engine_rules_r4_idle_yield.py` (L-0028, sight on) | 2 |
| R-007-01 | cover blocks its own layer | `tests/csim/test_PP_move_cover.py::test_R_007_01_02_06_...` | 1, 3 |
| R-096-08 | a guard never passes its radius | the per-tick guard leash test | 1, 2, 5 |

## What the rulings of 2026-11-17 left behind

Expected, since the rulings were records only; this is the work list of the engine piece.

- Engine: acquisition radius and the lock block in `om_tac_unit_ai` (`csrc/unit.c`), the end of the move away, `om_move_collide_pair` (`csrc/tactical_move.c`), and the steering probe's layer filter.
- Tests: 16 read as red or likely red under the new rules, 2 more may shift; 20 recorded hashes and pinned fight lengths will move. Red tests that cite none of the rewritten rules: `test_PP_C_g3_pursuit_by_sight.py`, `test_PP_unit_pursuit.py`, one case of the guard test.
- Lab checker: the lock check would report a drop for leaving the notice distance as a swap; the acquire check has no notice distance; nothing judges R-087-01 or collision across a slope's midline.
- Equations: ALG-62 (acquire within attack range, then sensor radius; the move away with no hold) and ALG-68 (same-layer pairs; "leash 200 wu") change with the engine, in the same commit.
- Layouts: all 84 catalogue layouts carry an order that brings the sides together, so none stalls at the start. A stand-off late in a fight cannot be read from the orders; L-0054, L-0046, L-0045 and L-0084 are the likeliest.

## Corrected in the same commit as this report

- R-096-02 said a unit acquires at attack range on its own layer and resumes when the target leaves range; it now cites the notice distance and the lock. Its sentence that a group never resumes described the engine before 2026-10-14 and is gone.
- R-087-05 and R-096-03 gave the leash as the sensor radius; the decision of 2026-11-01 and the engine use the larger of sensor radius and attack range. Both rules now say so, and today's decision row no longer contradicts the older one.
- R-087-01 and R-087-03 mark the two readings that are the Architect's and not Westley's words.
- R-087-06 said the engine overwrites the ordered point; that was fixed in the lab's E1 piece. Removed.
- R-097-05 said "layer line", a term with no source; it says midline. The E-13 collision Invariant names the slope case. E-14 R-120-02 no longer cites a 200 wu leash.
- The one named proof in E-01 (the Invariant that no unit stands in blocked ground) is `MISSING`: the test runs green, but it quotes E-13's rule, covers twelve units of one type on one layer, and has no terrain or sight.

## Open, by owner

Westley's:
- Q-096-02, new: whether a guard still engages by sight now that no other unit does.
- In E-01, not stage 4: a three-layer enemy is "never visible" in R-005-05 and visible at 0.20 from a vantage in R-005-06; the same factor is 0.40 in ALG-65 and 0.20 in the engine; the catalog row of S-162 says a pinged enemy learns roughly where the pinger is and R-162-03 says it is told nothing; the 5 percent of R-010-03 has no source. `Q-` rows for these are raised with the E-01 clean-up, not in this run.

The Architect's, text that is simply out of date (not done in this run):
- R-097-05 says 3 collision iterations, R-097-10 and ALG-68 say up to 10; R-097-01 blocks a cell above 0.7 and R-097-06 at 0.7 and above; ALG-68 says an idle unit takes no push; R-208-01 and R-096-08 describe the guard's return differently; R-096-08 still calls its radius "the attack-move leash".
- E-01's header (82 rules and 12 open flags against 87 and 8), eight flags listed open that the register closes, R-004-07's slope time against the two rules that cite it, Invariant 5 against the ground model, R-006-01 written as live though the pulse is not built.
- The checker's continuity predicate cites R-004-08 for a thing that rule does not say.
- Readings of today's text that an auditor could take two ways, to be settled in the engine piece's spec: whether the reach table's multipliers scale the margin; whether a unit holding after a move away acquires other enemies meanwhile; whether the steering probe follows the slope case of the collision rule.

Not confirmed by this run: that any candidate test is green, or that its control turns it red. The auditors read; they did not run.
