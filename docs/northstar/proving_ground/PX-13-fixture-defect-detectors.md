# PX-13 — Fixture-defect detectors (proving the factory)

Run 2026-09-19 (ouroboros `3c081a0`, `scripts/specfactory/fixture_defects.py`, 19 tests, specfactory suite 74/74). Claim (Factory section, Round 5 audit): three fixture-defect classes can be flagged before any model call: a control unsatisfiable by tick order, a control whose numbers never reach the branch it tests, and a two-agent fixture where the non-tested agent acts.

Result: **pass on the incidents, with stated limits**.

| Check | Incident | Hit | Clean counterpart | Silent |
|---|---|---|---|---|
| `tick_order_reachability` → `UNSATISFIABLE_BY_ORDER` | R7h `test_control_e05_agent_reads_live` (3d reads a same-tick 3f mutation from a SURPRISE injection) | yes | R7e fixed test, conquest-on-band control, S-034 tests | yes |
| `branch_coverage_of_control` → `VACUOUS_CONTROL` | R7l `test_control_e05_garrison_before_damage` (both orders give 31.3); suggests military 15.0 | yes | conquest-on-band control (no formula pair: declines, does not guess) | yes |
| `two_agent_confound` → `TWO_AGENT_CONFOUND` | R7e pre-fix `test_R_036_05` case 2 (defender budget 100, unfiltered `len(...) == 1`) | yes | R7e fixed version and every other sub-case | yes |

Sweep of all E-05 tests and controls: three flags, two the known incidents, one **new**: `test_E05_S040_empires_fracture.py::test_R_040_04_chain_still_completes_nothing_interrupts` reads a self-initiated SURPRISE `REINFORCE` injection through `read_reinforces` (3e) while the fixture's own comment says it resolves at 3f; `csrc/resolve.c` shows neither 3e nor 3f handles an injected `OM_ACT_REINFORCE` today. Question for Westley (design, not fixture): does a self-initiated surprise reinforce resolve in 3f like an attack, and is that meant to be built? The test already fails earlier on an unimplemented event-queue assertion, so it cannot be confirmed end to end yet.

Limits, stated plainly: all three checks are AST, regex and docstring-pattern matches over conventions this suite happens to follow (the `inject_intent(mode=SURPRISE)` shape; a per-bug-id formula table with one entry; lower faction id as the designed attacker). A same-tick surprise reached through `force_draws`, a new bug id without a formula entry, or a fixture that swaps the attacker convention would slip past.

Design consequences (DECISIONS.md): the conventions become explicit in the Stage 5 test template (a fixture marker naming attacker and defender; a machine-readable formula pair per "ways this could be wrong" item, generated with the control skeleton), so the detectors read declarations, not habits. The detectors run as part of card lint with WARN, and FAIL for the two classes that have never produced a false positive here.
