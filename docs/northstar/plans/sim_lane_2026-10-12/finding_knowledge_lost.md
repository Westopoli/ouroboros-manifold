# Finding 1: two red tests on the Mac (R-045-09 Knowledge Lost, R-085-04 fight order)

Diagnosis only; nothing was changed. Probes ran from /tmp/probe (a conftest wrapper), no repo file touched.

## A. R-045-09 Knowledge Lost rate

| rule says | sim did | seed/tick | classification | proposed piece |
|---|---|---|---|---|
| Mean 1.0 to 2.0 Knowledge Lost events per 50-tick window, 50 factions, 5,000 ticks | Mean 4.41 (test, seed 12345). Seeds 1, 2, 3: 3.84, 4.64, 4.63 | seed 12345, ticks 0-5000, 100 windows | Threshold target stands (closed Q-045-02 keeps 1.0 to 2.0); code matches ALG-27b verbatim; constants are a "first tuning" never fitted. Not a regression, not a fixture defect, not Mac. It is the open tuning item A90/A95 held by Westley | KL-RETUNE (Westley picks lever: constants, revolt economy effect, or per-world target) |

Evidence
- Rule: `docs/bible/epics/E-06-diplomacy-and-technology.md:88` (R-045-09); line 92: "constants ... are a first tuning; R-045-09 is the target Westley set and the number to retune against".
- ALG row: `docs/bible/algorithms.md:134` ALG-27b: eligible if `avg_e < 20.0` or `avg_p(now) <= avg_p(tick-50) - 10.0`, and cooldown >= 100; one draw, fire if `< 0.03`; `tech = max(0, tech - 5.0)`; "retune the constants, never the rule's shape".
- Code: `csrc/diplomacy.c:629-641` implements exactly that (ring of 50, old slot read before overwrite, `eligible && tick - last_kl >= 100`, one `om_rng_draw`, `< OM_KNOWLEDGE_LOST_P`, `fmax(0.0, tech - DELTA)`). Constants `csrc/om_constants.h:221-226` = 100, 5.0, 20.0, 0.03, 10.0, 50. All match ALG. Draw is taken only when eligible and off cooldown, as ALG says.
- Test: `tests/csim/test_E06_S045_a_faction_s_technology_is_one_number.py:198-237`. Fixture: `world_factory(n_regions=0, seed=12345)`, 50 factions, 100-150 regions, `generate`, EVENTS feature on, launch events loaded, 100 windows x 50 `om_world_step`, count records named "Knowledge Lost" from `read_events`. The fixture is the scenario the rule names. Fixed earlier as dead-filter defects (e6f39a3c, aee6ce4c). The event queues one tick after firing but every tick is read, so the count is faithful.
- Seeds: the test hardcodes 12345; I ran seeds 1, 2, 3 in a probe. Spread 3.84 to 4.64: stable, always 2 to 3 times the cap, so not seed luck.
- History: `git log -S OM_KNOWLEDGE_LOST_P` -> constants generated in 29d3cf37 (F3); pop-drop ring fixed in edc701c8 (B5c-1); diplomacy.c last touched for this in 3f293bf8 (SAVE-1, format only). No code change since to explain a drift.
- Linux status: `docs/northstar/plans/2026-10-14-skill-lab-rev2-baseline.md:28` lists it among failures "pre-existing on main". `docs/northstar/plans/2026-10-01-architect-rulings-2.md` A90 (:516) and A95 (:536): red and held by Westley "until the layer and environment systems are designed; he intends a fresh balance simulation". Q-045-02 (register :244, closed 2026-09-26) built the pop-drop leg and kept 1.0 to 2.0; the rate then went from 0.0 (leg missing) to about 4.4 (leg present). No sha with a green run on Linux exists in the ledgers; it was red from the first time it could fire.
- Mac float: ruled out. The path is `fmax`, double add and compare, and the project RNG; Makefile:33-38 uses `-fno-fast-math -ffp-contract=off`, SSE2 doubles. No libm transcendental on the path.
- Not established: which eligibility leg (economy < 20 or pop drop) supplies most events. That needs instrumentation I was told not to add. KL-RETUNE should start by counting each leg.

## B. R-085-04 Strike before Line before Siege

| rule says | sim did | seed/tick | classification | proposed piece |
|---|---|---|---|---|
| Strike-vs-Strike resolves before Line-vs-Line before Siege-vs-Siege | Strike 2170, Line 4226, Siege 1800 ticks. Strike < Line holds; Line < Siege fails (`assert 4226 < 1800`) | single deterministic fight each, no seed in the test | Threshold/measurement never had a bible source: Q-085-01 (algorithms register :246) and Q-085-02 (:247), both open, say the engagement layout and composition are inventions. Not a Mac float issue, not a drift from an ALG row | TACT-ORDER-RULING (Westley answers Q-085-01/02 and the engagement the order is measured on) |

Evidence
- Rule: `docs/bible/epics/E-11-units-and-combat.md:110` (R-085-04); line 115 "launch pacing targets (A-340)". The rule gives no counts, distance or orders.
- ALG: the tactical section `docs/bible/algorithms.md:254-` holds unit stats and damage; no ALG row states a fight duration or a per-category ordering. R-085-04 therefore rests on no ALG row, only on the Westley pacing target.
- Test: `tests/csim/test_E11_S085_long_enough_to_think.py:69-96`. Three separate one-region worlds, 10 v 10 mirrors: Raider at x 0 v 200 spacing 30; Vanguard 0 v 300 spacing 30; Bombard 0 v 1000 spacing 40; `om_tactical_run_until_eliminated`. The starting distance differs per category (200, 300, 1000), so the fixture is not like-for-like. A116 (rulings-2 :604) says Engineer variants kept the same result "Strike before Line holds in every variant, Line before Siege fails in every variant", so the fixture is not the cause. Note the unused first `w = world_factory(...)` at line 71, harmless.
- Code: `csrc/unit.c` and `csrc/tactical_move.c` use `sqrt` (IEEE exact) and a private `om_atan2` (`tactical_move.c:458`); Makefile:33-38 deterministic flags. No platform transcendental on this path, so Mac float is ruled out. A99's tactical hash reds are a separate matter and were not diagnosed here.
- History: the test last changed in ff922942 (2026-10-03) and ee8ca739 (R-085-02 bounds only); R-085-04 body unchanged since 28c1415e (2026-09-16). Code `unit.c` changed since A110 (2026-10-01: Line 124 s = about 2480 ticks, Siege 30 s = 600): K0/K-e2/terrain2 pieces on 2026-10-06 to 10-10 moved Line to 4226 and Siege to 1800 (fixture values have drifted, order still wrong in both). Baseline `2026-10-14-skill-lab-rev2-baseline.md:29` lists it "pre-existing on main"; rulings A110, A116, A129 keep it red as Westley's.
- Register hygiene: Q-085-01 and Q-085-02 appear twice with different text (rows at :125-126, closed-looking old pair, and :246-247). The `Q-` id collision should be fixed by the clerk, not here.
- Interpretation candidates already in the register: (a) tune roster stats; (b) retarget to measured values; (c) restrict the ordering to mixed fights (Q-085-02 c). Nothing chosen.

## Summary
Both reds are balance findings Westley already holds (A90/A95, A110/A116/A129), not regressions in the C. Neither is a Mac float difference. Code matches ALG-27b verbatim; R-085-04 has no ALG row.
