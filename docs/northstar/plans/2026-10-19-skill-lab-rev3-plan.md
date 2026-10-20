# Skill lab rev 3: close the coverage gaps found after rev 2 (plan, 2026-10-19)

Plan for a Sonnet 5.5 overseer running in manager mode. Source: the Architect (session ouroboros-manifold-b0), relaying Westley 2026-10-19 after two Opus roster analyses and an Opus positioning audit (`docs/northstar/plans/drift_audits/2026-10-19-positioning-in-code.md`; the mix analyses are copied by the Architect's clerk to `docs/northstar/research/layer_dynamics/audits/mixes_2026-10-19/`). Everything below that the Architect did not state is marked DRAFT. This file is records only; the lab landing (`LAB-REV2`, spec `docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md`) comes first and the rev 3 pieces build on it.

## Purpose

Westley's verdict: "these are some major defects in the simulation lab, our testing method isn't as strong as it needs to be." The lab exists to find the rule settings that give strategic depth. Ten defects (D1 to D10) show that its experiment does not cover the game: it plays four of nine category cells, uses layers 0 to 2 only, sweeps knobs that cannot bite on the play they are swept on, and copies types in a way that drops engine rules. Rev 3 fixes the defects and adds the checks that would have caught them.

## Method (manager mode)

Westley: "tests written first, agent that wrote tests will not write implementation, manager-mode mentality."
- The overseer plans pieces and writes briefs. It never codes.
- Every requirement has a test that is RED today, with the failing line pasted, before any builder starts.
- A fresh auditor reads each test set. A different agent builds. A clerk lands.
- The red list (test id, failing line, which defect or requirement it proves) goes to the Architect before the first builder starts.
- Rule questions go to the Architect; numbers go to Westley through him.
- Each test cites the rule or the finding in its header, pastes its failing line on the current lab branch, and has a positive control.

## Defects (each is a FINDING row `FINDING-lab-d1` to `FINDING-lab-d10` in the push ledger and gets a red test)

- D1 Layers. The engine has five layers (`OM_LAYER_COUNT 5`); the lab uses layers 0 to 2, the enemy always on layer 0, no play ever below the enemy, no play on layers 3 and 4. The two-layer knob families (vision, range, damage at offset 2) were swept on plays where no unit is ever two layers from an enemy: measured byte-identical rows at 0.25 and at base.
- D2 Mixes. M0 to M4 and M3b reach 4 of the 9 category cells (Strike against Siege never, except one Raider in M3b); the Warden is in no mix; Bombard and Bastion never fight in batch one's sweep.
- D3 Copied types. `plays_space._types` and `fight._register_types` copy every type with a reach into a custom id; the engine keys the Warden aura (`unit.c:1129`, `:627`) and the Bastion damage cap (`unit.c:987`) on built-in ids, so the copies lose both (built-in Wardens beat copies 8 of 8; a copied Bastion dies in 720 ticks against 1,057). `om_roster_set_reach` works on built-in ids (verified on ids 5 and 1).
- D4 `naive_attacker` baseline fields 16 Vanguards whatever mix the play uses (`scenes.py:133-136`): C1 is not like for like.
- D5 `s3_dark_striker` is a no-op: it sets side 0 silent, the default; nobody emits; identical result under three settings (1669 ticks, 14:0).
- D6 The `OM_TP_CATMULT_*` settings are never read (`unit.c:2427-2438` uses compile-time constants): a category-matrix family cannot be swept until an engine piece; the lab must mark it unavailable, not sweep it.
- D7 One-way reach scenes stall once the units that can reply are dead (for example Interceptors two layers below a Vanguard force; Bombards two above without enemy Interceptors): the fight runs to the cap; pre-flight does not catch it; elimination-only has no end condition for "no side can reach the other".
- D8 The opening-window prediction misses the layer arrangement: on layout 192 three setups (Raiders one up; Raiders with reach removed; Raiders on the enemy's layer) gave the identical window reading 10.5 : 3.0 and ended win, stall, loss; the whole-fight totals told them apart (709:565, 290:565, 298:777).
- D9 Warden healing stacks per Warden and stalls fights above 4 per 16 (20 of 20 caps at 16 Wardens, 6 of 20 at 8, 0 at 4). The stall is a rule question for Westley; until he answers, the lab fields at most 4 Wardens per 16.
- D10 Method. No check that the experiment covers the game (category cells, reach pairings, layers) and no check that a swept knob can bite on the play it is swept on; the gap sat in a draft mix table and passed every test and both drift audits.

## Requirements (Westley, 2026-10-19)

- R1 Mixes (arbitrated, accepted by him). Keep M0 to M4 and M3b. Add M5 8 Raider + 8 Bombard; M6 8 Interceptor + 8 Bombard; M7 8 Raider + 8 Interceptor; M8 8 Bombard + 8 Bastion; M9 12 Vanguard + 4 Warden; all six types as one robustness mix in batch two. Same mix both sides (rev 2 ruling 2). A 30-fight naive mirror per new mix before it enters a batch; a mix that caps is rejected and reported. D3 and D4 are fixed first.
- R2 All five layers. Plays and baselines place sides on every layer pair the reach table allows; the enemy layer varies (0 to 4); plays that fire from below exist (Interceptors two below, Raiders one below); a layer-symmetry control shows a same-offset fight on (0,1) and on (3,4) gives the same result in a space era. Ground eras later.
- R3 Reach as a knob. Westley: "experiments should also vary unit types/roles abilities with regards to number of layers visible upward/downward, not just stick to one value for each role (the intent of the simulation engine is to find the configurations that induce strategic depth)." Per type, reach up and reach down are swept values (0, 1, 2 each, inside the rules) with the bible's reach table as the base point. The mix and play tables are data-driven by the reach configuration; the artifact reports crossings per reach configuration; vision up/down offsets likewise. R-164-03's intent is the target: a type that reaches further is weaker to something, so the advantage is temporary.
- R4 Paper prediction from the setup. A first-class prediction computed before anyone moves: per side, the units whose reach covers the enemy's layer, times the category weight, with a clear sightline through the Setup's blocks. Reported beside the opening window and the whole-fight totals; the artifact says which of the three called the winner. The window stays.
- R5 Coverage test (red until covered). Every category cell of ALG-60, every reach pairing a type can make, and every layer is exercised by at least one enabled play or mix.
- R6 Inert-knob probe. Before a family is swept on a play, one fight at the band's extreme must change the row hash against base; otherwise the batch refuses the family on that play and says so in the artifact.
- R7 No-reach end. A fight where no living unit of either side can reach any living enemy (reach table plus layers) ends as a finding row `no_reach_stall` at that tick and never runs to the cap; pre-flight refuses a scene that starts that way.
- R8 Fixes. D3: set reach on built-in type ids, no copies. D4: the naive attacker fields the play's mix. D5: the dark-striker play makes the enemy emit at the knob's values, or is deleted with its row. D6: marked unavailable with a FINDING row pointing at the engine piece.
- R9 Sight-engagement, for planning only. Westley approved the Starcraft rule set (`docs/northstar/plans/2026-10-19-sight-engagement-proposal.md`, section 3 answered). The engine piece comes after the lab landing and E7; L8 re-engage and mop-up retire after it. Batch one runs with re-engage as the stand-in and says so.

## Test cases (written first, red today; the writer never builds)

| Id | Proves | Statement |
|---|---|---|
| T1 | R5, D1, D2, D10 | Coverage test over the mix table, the play table and the reach table; fails naming each uncovered category cell, reach pairing and layer. Red today on D1 and D2. |
| T2 | R6, D1, D10 | The probe on `s3_layer_above` with the two-layer families says inert (identical hash). Positive control: the one-layer family changes the hash. |
| T3 | D3 | A fight with 8 built-in Wardens against 8 lab-registered Wardens is a mirror (same outcome distribution), red today. The Bastion cap: a lab Bastion takes at most 1.0x from a Strike attacker, red today. |
| T4 | D4 | The naive attacker's roster equals the play's mix for every play. |
| T5 | D5 | The dark-striker fight changes under the emitting knob. |
| T6 | R2, D1 | Plays exist on layers 3 and 4 and below the enemy; the layer-symmetry control. |
| T7 | R3 | The reach table is a swept input: a sweep with Raider reach up 2 produces a different break-even than reach up 1 on `s3_layer_above`. |
| T8 | R4, D8 | The paper prediction exists in the CSV and the artifact and names the winner on the three audited setups of D8 (layout 192). |
| T9 | R7, D7 | The Interceptors-two-below scene ends as `no_reach_stall` before the cap (today it runs to 12,000). |
| T10 | R8, D6 | The category family is listed unavailable with its finding. |
| T11 | D9 | A mix with more than 4 Wardens per 16 is refused by the mirror pre-check. |

## Pieces

Owner rows `LAB-REV3` (umbrella, this file), `LAB-REV3-A`, `LAB-REV3-B`, `LAB-REV3-C` are in `docs/northstar/plans/push/pieces.toml`, queued. Every rev 3 row depends on `LAB-REV2` and `LAB-REV2-FIX` (FIX owns `sweep.py`, `scenes.py`, `plays.py`, `scan.py`, `contract.py`, `fight.py`, `diagram.py`, `report.py` today; no file moves out of FIX; the dependency orders the lint). File lists below are DRAFT, derived from the defects; the test writer and the overseer correct them against the code before the rows are final. New file names are DRAFT.

| Piece | Tests | Files (DRAFT) | Builds |
|---|---|---|---|
| LAB-REV3-A (first) | T1, T2, T3, T4, T5, T10 | `scripts/skilllab/plays_space.py` (`_types`), `scripts/skilllab/fight.py` (`_register_types`), `scripts/skilllab/scenes.py` (lines 133-136), `scripts/skilllab/sweep.py` (the probe, the unavailable family), new `scripts/skilllab/coverage.py` and `scripts/skilllab/probe.py` | D3 (built-in ids with `om_roster_set_reach`, no copies), D4, D5 (emitting enemy, or the play deleted with its row), D6 mark-unavailable, the coverage test T1 (red until B lands the new rows: A ships it marked expected-red with the uncovered list as its output, DRAFT) and the inert-knob probe T2. |
| LAB-REV3-B | T6, T11 | `scripts/skilllab/plays_space.py` (the mixes data table: columns name, units, used_in, enabled; rows M5 to M9), `scripts/skilllab/plays.py`, `scripts/skilllab/scenes.py`, `scripts/skilllab/sweep.py` (the 30-fight naive mirror pre-check, the Warden cap) | R2 plays on all five layers and below the enemy plus the layer-symmetry control; R1 mixes M5 to M9 as rows of the mixes table, each behind the 30-fight naive mirror pre-check (a mix that caps is rejected and reported); D9 cap of 4 Wardens per 16 with the refusal in the mirror pre-check. T1 turns green here. |
| LAB-REV3-C | T7, T8, T9 | `scripts/skilllab/plays_space.py` and `scripts/skilllab/sweep.py` (reach and vision up/down as swept knobs), `scripts/skilllab/fight.py` and `scripts/skilllab/contract.py` (the `no_reach_stall` end), `scripts/skilllab/scenes.py` (pre-flight refusal), `scripts/skilllab/report.py` and `scripts/skilllab/diagram.py` (crossings per reach configuration, the three predictions), `scripts/skilllab/rows.py` or the CSV writer (the paper-prediction column; column name DRAFT) | R3, R4, R7, D7, D8. |
| LAB-REV3-L (landing order, not a row) | none | none | Order A, then B, then C. The Architect said "B and C by files"; B and C share `plays_space.py`, `scenes.py` and `sweep.py` in the DRAFT lists, so the rows order C after B (DRAFT; if the corrected lists are disjoint, B and C may land in either order). One landing per piece through a merge clerk; the merge gate and the playthrough run after each. |

`csrc/unit.c` is touched only by a named engine piece (D6 category-matrix settings read at run time; R9 sight-engagement), never by A, B or C.

Order and gating (Architect): the lab landing (`LAB-REV2`) first, then A, B, C. D3, D4, D5 and T1, T2 go first because they change what batch one measures. Batch one may run before the rest only if its header lists D1 to D10 as known gaps, and says re-engage is the stand-in for R9.

## Process per piece

1. Test writer (Sonnet, one file set) writes the piece's tests from this plan and the code, red on the built tree for the stated reason, failing line pasted, positive control green. It never builds.
2. The red list (test id, failing line, defect or requirement proved) goes to the Architect before the first builder starts.
3. A fresh auditor that has not seen the writer's reasoning reads the test set against this plan and the code and tries to refute it.
4. A different agent builds in a worktree under `~/Projects/om-push/wt/`, runs `scripts/specfactory/pre_gate.sh`, pushes its branch and stops.
5. A merge clerk lands it (merge gate, playthrough); one landing per piece.
6. STOP rules in every brief: a test defect is a ledger row classed by the ruler, never an edit by the builder; a threshold or tolerance is Westley's.

## Open for Westley (routed through the Architect)

- D9 rule question: Warden healing stacks per Warden and stalls fights above 4 per 16. Until he answers the lab fields at most 4 Wardens per 16.
- Roster analysis go: the two Opus roster analyses and the arbitrated mix table (R1 is accepted; a go to run batch one with the known-gaps header is still his).
- Layouts: which layer pairs and enemy layers (R2) the first batch fields (DRAFT: every pair the reach table allows).
- Arcs and cones: whether the E2 arc and cone families run in batch one (they land after the lab landing).
- Numbers, all DRAFT until he gives them: reach sweep values beyond 0, 1, 2; the 30-fight naive mirror count (30 is the Architect's); the paper-prediction category weights (taken from ALG-60, no new number); vision up/down offsets and bands.
