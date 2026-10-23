# Leave-off: layer dynamics and the skill lab, 2026-10-02

**Picked up on the Linux machine, 2026-10-02.** The plan that continues this work, with Westley's decisions on the open parity points, is `docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md`; rulings are in `docs/northstar/plans/2026-10-01-architect-rulings-2.md` (Addendum 45 on). The rest of this file is the Mac's record as it left it.

The design chat on the Mac stopped here. Westley, 2026-10-02: "I'm going to hand this task off to the linux machine, coordinating modifications to the real sim between machines will be difficult. Our work is done for now." All of this work now continues on the Linux machine. Everything is on `origin/main`; nothing is left only on the Mac.

## Read in this order

1. `docs/northstar/research/layer_dynamics/README.md`: the goal, the principle, the five skills, the measure, the conditions, the layer rulings, the plan.
2. This file: where the work stopped and what is next.
3. `docs/northstar/plans/2026-10-02-tactical-port-parity-requirements.md`: the next piece of work (P1 to P9), with Westley's rulings quoted.
4. `docs/northstar/plans/2026-10-02-skill-lab-cascade.md`: the harness contract (section 3) and the engine steps for the layer system (section 5; G2 and G8 moved into the parity work).

## Where things stand

| Thing | State |
|---|---|
| Goal, principle, measure, five skills, conditions C0 to C9 | Written (README 1 to 4). Draft pass marks not yet confirmed by Westley. |
| Layer rulings | In E-01 and the register (README 6). Buildable: S-001 to S-004, S-162 to S-164, with provisional numbers (brief section 6). |
| Toy simulator `toys/layerlab/` | Frozen. Its findings are leads only (README 10). |
| Skill lab harness `scripts/skilllab/`, tests `tests/skilllab/` | Landed on `main` at `61a201e6`. 547 tests pass on the arm64 Mac. Not yet run on Linux. |
| Controls on today's engine | Measured: mirror 16 v 16 mean +0.003; 17 v 16 +0.285; identical 16 beat 15; +20 percent damage beat 17; +20 percent reach beat 14. No chart page was made for Westley. |
| Port audit, Python against C | `port_gap_audit_2026-10-02.md`: 24 differences. A Sonnet sub-agent's work, not re-verified line by line. |
| Port-parity requirements P1 to P9 | Written, ruled by Westley, not planned, not built. |
| Engine cascade for the layer system (G0, G1, G3 to G7) | Briefed, not started. Waits for the parity work: both edit `csrc/unit.c` and `csrc/tactical_move.c`. |
| Skill batches, the search | Not started. |

## Next, in order

1. On Linux: pull `main`; run `python3 -m pytest -q tests/skilllab` (about 3 minutes). `tests/skilllab/integration/test_cross_machine.py` compares against `tests/skilllab/golden_hashes.json`, written on the arm64 Mac. A mismatch is a determinism finding to bring to Westley, not to patch.
2. Plan and build the port parity (P1 to P9). The requirements file lists nine open points to bring to Westley first as register rows.
3. Regenerate the golden hashes (movement changes every fight), re-run the controls, and make the one-page controls chart for Westley: `python3 -m scripts.skilllab controls --out <dir>` writes the rows and the HTML page.
4. The engine cascade for the layer system: brief section 5, G0, G1, G3 to G7.
5. Small batches, one skill at a time, each read with Westley before the next (README 8). Then the search for every region of settings where the conditions hold.
6. When a working configuration is found and Westley has read it: carry the layer interactions into the MVP at once (his request, 2026-10-02).

## Findings to carry forward

- **Position decides what is measured.** Today's engine walks two armies into two flat rows at weapon range whatever shape they started in, so a starting formation does not survive the walk. Westley: "A real battle isn't going to be a line feeding into each other, it's going to be a blob if they're mediocre players, or a spread out line if they're skilled players." The plays now start sides at contact distance. After P1, P5 and P8 land this must be looked at again before any formation batch.
- **Concentration of fire.** With 1.2x reach every unit on both sides was firing, yet the long side lost: it halted strung out in depth, the enemy's fire fell on its front few units, its own fire was spread. Equal total health, 11 units alive against 15. The principle (units able to fire) does not cover this. Not yet discussed with Westley as a change to the principle.
- **One even fight swings about 0.17 in margin** on position shifts of up to 10 wu. Twenty fights per cell place a mean within about 0.04. Near a break-even more fights per cell are needed.
- **No first-spawner edge shows** once positions are shifted, although the C applies damage in unit-id order (audit G02).
- **One fight costs about 70 ms** through the harness (the engine alone is about 3 ms; sampling every 5 ticks through ctypes is the rest). A 120-fight scan takes about 7 s.
- **Charts.** Westley reads: a heading that states the finding in soldiers; a line of won and lost fights by enemy size with the break-even marked; labelled firing lines with the gap shaded; a table with a plain-words column. He found margin curves and scatter plots hard to read. Sample: https://claude.ai/artifact/WtQDNnNZTR8hqx6LpxBaJ2. The report page shades the gap between two firing lines as a bow-tie where they cross; cosmetic.

## How Westley wants this worked

- Small batches, read together, then the next step. Not thousands of runs analysed afterwards.
- Look at what a setup actually does (print positions through a fight) before measuring it. A surprising result is first a question about the instrument.
- Check anything written against his own words; quote him, do not paraphrase a ruling into something stronger.
- Explain choices with context and a small diagram; terse option lists have confused him.
- He owns every threshold and tolerance. Tests are changed only as `test-defect` with a ledger row (`docs/northstar/plans/push_ledger_2026-09-22.md`, rows `TD-SKILLLAB-*`).
- Sonnet 5.5 sub-agents build; the main chat designs, documents and checks. Sub-agents report once.

## Open with Westley

- The nine points in the parity requirements, section 3 (speed cap, the repulsion stall, leash before damage, and the rest).
- Whether concentration of fire joins the principle or is treated as a property to tune out.
- Draft pass marks for C0 to C9; how refusing a fight is checked; the roll-up counter; the provisional numbers (brief section 6).
- Register: `Q-008-02`, `Q-008-03`, `Q-009-02`, `Q-165-01` open; `Q-001-05`, `Q-005-04` provisional.
- On the Mac only: 34 old agent worktrees under `.claude/worktrees/`, and an uncommitted `project.godot` change he chose to discard (`git restore project.godot`).

## File map

| What | Where |
|---|---|
| Start-here record | `docs/northstar/research/layer_dynamics/README.md` |
| This leave-off | `docs/northstar/research/layer_dynamics/LEAVE_OFF.md` |
| Runs, one file each | `docs/northstar/research/layer_dynamics/runs/` (`2026-10-02_harness_check.md`) |
| Port audit | `docs/northstar/research/layer_dynamics/port_gap_audit_2026-10-02.md` |
| History and every toy run | `docs/northstar/research/layer_dynamics/history_2026-09-30_to_10-01.md` |
| Audits of the record against Westley's words | `docs/northstar/research/layer_dynamics/crosscheck_2026-09-30.md`, `crosscheck_2026-10-01.md`, `crosscheck_2026-10-02.md` |
| Parity requirements (next work) | `docs/northstar/plans/2026-10-02-tactical-port-parity-requirements.md` |
| Harness contract and engine brief | `docs/northstar/plans/2026-10-02-skill-lab-cascade.md` |
| Harness spec as built | `docs/northstar/plans/skilllab-harness-spec.md` |
| Harness code | `scripts/skilllab/` (`contract.py`, `engine.py`, `fight.py`, `firing.py`, `formations.py`, `plays.py`, `scan.py`, `sample.py`, `rows.py`, `report.py`, `__main__.py`) |
| Harness tests | `tests/skilllab/`, real-engine controls in `tests/skilllab/integration/`, `golden_hashes.json` |
| Test-change ledger | `docs/northstar/plans/push_ledger_2026-09-22.md` (`TD-SKILLLAB-*`) |
| Layer rules | `docs/bible/epics/E-01-layer-system.md` |
| Unit, fog, movement rules | `docs/bible/epics/E-11-units-and-combat.md`, `E-12-fog-and-sensors.md`, `E-13-movement-and-command.md` |
| Strategic-depth principle | `docs/bible/game_bible.md`, principle 4 |
| Register | `docs/northstar/ambiguity_register.md` |
| Research briefs | `docs/legacy/topics/lanchester_and_combat_theory.md`, `active_layer_vision_mechanics.md`, `charts_for_combat_simulation_data.md` |
| Python reference sim | `simulation/` (`movement.py`, `damage.py`, `facing.py`, `tactical_map.py`, `reinforcement.py`) |
| C sim | `csrc/` (`unit.c`, `tactical_move.c`, `fog.c`, `tactical_mapgen.c`, `tactical_support.c`) |
| Frozen toy | `toys/layerlab/` |
