# PX-06 — Under-test detection: shadow fixture and diff-scoped mutation (proving the factory)

Run 2026-09-19 (ouroboros `e00dd77`, `a0514e1`, `b2ece82`: `scripts/specfactory/undertest_check.py`, `tests/specfactory/test_undertest_check.py`). Claim (Factory section, "Gates the worker cannot move"): a candidate that hard-codes the fixture's answer fails a perturbed fixture; and mutating only the lines a candidate changed must kill at least one acceptance test, or the card is under-tested and must not merge.

Result: **mutation gate proven on the real incident; shadow fixture unproven; one tool defect found**.

## E1 — the R7g incident, caught

Mutants of card 204a1's own diff (`0d65f9e`, the merged `om_step_telegraphs` that got five formulas wrong) against its single acceptance test `test_R_036_03_it_resolves_in_step_3c`:

**40 mutants, 14 killed, 26 survived, verdict UNDER_TESTED, 1.27 s per mutant.**

The survivors name the exact lines R7g later found wrong by hand: the entrenchment ternary (line 127), the effective-attack product (136), the effective-defense product with its `0.55` and its reinforce term (137), the forced-draw branch (140). A gate reading this report would have blocked the merge and named the missing tests, four cycles and one human diagnosis before R7g did.

## E2 — after the fix, with the R-037 tests

Mutants of the fix diff (`a493cfd`) against `test_R_036_03` plus `R-037-01..05`: 40 mutants, 2 killed, 38 survived, 2.29 s per mutant.

That number is contaminated: **the tool mutates literals inside C comments**, and lines 143-146 of the fixed function are a comment block explaining the forced-draw scaling. Those mutants are no-ops and can never be killed. Excluding them, the real survivors are the entrenchment lines (128, 129: `held_since < 0`, `1.0 + fmin(1.0, (tick - held_since) / 100.0)`) and one RNG line. That residual is genuine and was predicted by R7g itself: every fixture in the suite sets `held_since = -1`, so no test constrains the aged-entrenchment formula at all.

## E3, E4 — shadow fixture: inconclusive

Both the genuine `om_faction_step_budget` at `d641ea2` and a hand-made hard-coded version returned `baseline_pass: False`: the acceptance test does not pass at that commit even before perturbation (its later `om_step_decisions` assertion is red for unrelated reasons), so the check could not distinguish them. The shadow-fixture claim is **not tested**; it needs a card whose acceptance is actually green at some commit.

## Design consequences

1. The diff-scoped mutation gate is adopted on this evidence, with three stated properties: it skips comments and string literals (this run's defect); it reports per-line survivors, because the actionable signal is which changed line no test constrains, not the bare verdict; and it runs in the CPU slot after a candidate passes and before merge, so the 50-95 s it costs per card never blocks the GPU slot.
2. A survivor set that is entirely one formula is a test-authoring task (`test-defect`, escalator-owned under C6), not a card failure.
3. The shadow fixture stays in the design but is unproven; re-run it against a card that is green at HEAD before trusting it.
4. Independent finding for the E-05 suite: aged entrenchment (`held_since` other than -1) is untested across the whole suite.
