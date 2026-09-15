# Probe K — red tests generated from rules

**Proves.** `agy`'s filled-in test bodies (arrange/act/assert from `gen_test_skeleton.py`'s stubs) are red for the right reason: a planted defect in one rule's expected value fails only that rule's test, and a correct toy implementation passes every other generated test.

**Fixture.** Toy epic with concrete numbers, one rule's expected value deliberately wrong in the epic text (planted defect). A correct toy C implementation of the epic's real (intended) behavior.

**Pass criterion.** Against the correct toy implementation: the test for the planted-defect rule fails (proving the test faithfully encodes the epic's stated — wrong — number, not the correct behavior); every other generated test passes. Tests are never hand-edited after generation for this probe to pass; a test that needed editing to get this result is the probe failing, not passing.

**Blocked today.** `gen_test_skeleton.py` emits fail-stub skeletons only (verified, `docs/northstar/spec_factory.md`); no `fill_tests.md` prompt exists yet to fill arrange/act/assert bodies from a rule's numbers, and no toy C implementation exists to run them against. Runs after the fill prompt lands and a toy implementation is written.
