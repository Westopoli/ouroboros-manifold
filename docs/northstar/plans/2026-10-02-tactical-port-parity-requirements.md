# Requirements: bring the C tactical sim back to the Python's behaviour

Written 2026-10-02 by the design chat on the Mac (real-engine-tuning-lab) for a planning chat on the Linux machine. This file states what is required and where the evidence is. It is not a plan: the Linux chat writes the plan, the pieces, the tests and the order.

## 1. Why

The skill lab (`docs/northstar/research/layer_dynamics/README.md`) measures tactical fights on the real C sim. Its first run showed two armies collapsing into flat rows at weapon range whatever shape they started in (`docs/northstar/research/layer_dynamics/runs/2026-10-02_harness_check.md`). The cause is the port: the Python reference sim (`simulation/`) has movement and pursuit behaviour that the C sim (`csrc/`) lost. An audit then found 24 further differences: `docs/northstar/research/layer_dynamics/port_gap_audit_2026-10-02.md` (by a Sonnet sub-agent, file and line for both sides; spot-check before relying on a line number). The audit's own numbering (G01 to G24) is used below as "audit G##"; it is not the skill-lab brief's G0 to G8.

Westley on the movement, 2026-10-02: "make sure that we use the same exact logic from the python in the new C, that was tested and it worked perfectly and it's exactly how I want units to move in the C version."

Westley's ruling on the audit, 2026-10-02: "C engine should: #3 fire the tick the target enters range, have the python terrain/waypout/map-edge routing from #5, have python of all of #6, python of #8, python #9, python #10, python #11, and python #12. This is getting into deep implementation work, let's send this as a requirement to the Linux machine in a push."

## 2. Required (ruled by Westley)

In every item the Python is the reference. "Exactly" means the same decisions on the same inputs; where the C must differ for determinism or scale (fixed-point, id order, no unseeded `random`), keep the C mechanism and reproduce the Python's outcome, and list each such place in the plan.

| Req | What the C sim must do | Python reference | C today | Audit |
|---|---|---|---|---|
| P1 | **Pursuit through ordinary movement.** An attack-moving unit whose target is not in its range, with a visible enemy in sensor range, gets its move goal set to the nearest visible enemy and walks there through the normal movement step (steering around units). It holds only while its own target is within its attack range, and pursues again when the target leaves. Pursuit target chosen on the unit's cohort turn, gated by the unit's visible set; the chase persists after arrival. | `movement.py` 282-460; `damage.py` 190-290 | `unit.c` `om_tac_step_toward` writes a straight-line position; holds on any hostile in range | known gap; G10 |
| P2 | **First shot fires on the tick the target is first in range** (no full-interval wait after spawn). | `unit.py` 98; `damage.py` 21-24 | cooldown starts at 0 and must reach the interval | G09 |
| P3 | **Routing around terrain, waypoints, map-edge clamp.** A route on the 100 wu grid built from obstacle density, cached per shared destination, straightened by line of sight, followed by waypoints with their arrival radius; positions clamped to the map; collision pushes clamped to the map and slid along blocked cells. | `movement.py` 105-210, 360-370, 457-459, 621-651 | straight line; BFS path never used; no clamp; density cells never filled | G08, G14 |
| P4 | **Map content, all of it.** Obstacle, cover and interference gradients with linear, quadratic and constant falloff; spine nodes; vantage nodes; drifting nodes; the asteroid field; layer masks and layer accessibility; layouts from the generator. The live battle map carries them and the pipe sends them. | `tactical_map.py`; `map_generator.py`, `layout_library.py`, `layout_instantiator.py`, `gradient_placer.py`, `layer_masks.py` | `om_map_generate*` STUB; binary discs; one cover disc per mission; `obstacles: []` on the pipe | G07, G20 |
| P5 | **Attack-move as a group order.** Attack-move gets formation slots like move (offsets from the centroid, scatter fallback beyond 450, slot walkability). When every member has engaged, the group ends and its members do not resume the march. | `command.py` 50-61; `movement.py` 512-536, 667-732 | every unit sent to one shared point; always resumes | G11 |
| P6 | **Return fire also turns attack-moving units.** A unit with no target that is hit, idle or attack-moving (not plain-moving), turns on its attacker; out of range, it attack-moves to the attacker and its old destination is dropped. | `damage.py` 78-130 | idle units only | G12 |
| P7 | **Units face what they shoot.** A unit faces its engaged target (within 1.5 x range), else its move target, else its velocity. Stationary firing units turn. | `facing.py` 59-77 | stationary units never turn | G22 |
| P8 | **Steering sweep as the Python.** Straight probe 40 wu; if blocked try +30, -30, +60, -60, +90, -90 degrees in that order and take the first clear one; if none is clear, continue straight; hold a deflection for 60 wu of distance moved; only units on the same layer block; probe against start-of-tick positions. | `movement.py` 234-250, 311-325, 413-431, 463 | 13 angles at 15 degrees; waits when none clear; no layer filter; group mates exempt; live positions | G13 |
| P9 | **Capture census wired.** Each tick, per structure: units within 300 wu, capture after 10 s when exactly one non-owner faction is present and no owner. Keep the C's seeded RNG for spawn offsets. | `reinforcement.py` 23-81 | `tactical_support.c` waits for a caller that does not exist; capture never advances | G21 |

P1 and P8 together are what the skill-lab brief called G8, and P3 is its G2 (`docs/northstar/plans/2026-10-02-skill-lab-cascade.md` section 5). They move to this work; the Mac's cascade B keeps G0, G1 and G3 to G7 and starts after this lands, because both edit `csrc/unit.c` and `csrc/tactical_move.c`.

## 3. Bible

Rewritten on 2026-10-02 to carry the ruling (check them before writing tests): E-11 R-084-01 (P2), R-087-04 (P1), R-087-06 (P6); E-13 R-096-02 (P5), R-097-03 (P8). Already says the Python: E-13 R-100-01 (P7), R-097-01 (P3), E-15 R-127-01/02 (P9).

The Linux chat brings these to Westley as register rows before building; they are places where "exactly the Python" meets something else and nobody has ruled:

1. **Speed cap.** Python attack-move and move have no cap at the slowest member; the bible (R-095-01) and the C cap. The ruling on P5 named slots and the group ending, not the cap.
2. **Obstacle repulsion.** The Python's repulsion (`movement.py` 433-443) is a direction no-op, and at density 1.0 the steer vector is zero so the unit stalls (audit G08). R-097-09 describes a working repulsion. Port the stall, or fix it?
3. **Terrain slow.** The C has R-097-06's slow (1 - 0.5 d) built and unfed; the Python has none. P4 will feed it for the first time.
4. **Block threshold.** Python blocks a cell at density >= 0.7; C and R-097-01 at > 0.7.
5. **Asteroids.** Python line of sight uses 3D cylinders with height; C uses 2D discs of any height; `Q-098-01` is open on cover height and on units inside a cover disc.
6. **E-17.** Map generation is E-17's; the C comment says the gradient model is "held" for it. P4 needs E-17's open flags checked and its gate run.
7. **Leash before damage.** In the Python the 200 wu leash runs before damage, so an attack-moving unit with range over 200 never shoots a target more than 200 from its anchor (audit G03). This is tied to P1's code path but was not ruled. Do not port it silently.
8. **Collision details** beyond the clamp and slide in P3 (stationary pairs, snap to slot, exact-overlap direction; audit G14): R-097-10/07 and R-099-04 match the C.
9. **Fixed caps.** The C's 1,024 density cells against a Python navmesh of 57,600 cells for a 24,000 wu canvas (audit G23): P3 and P4 cannot fit in the present table.

## 4. Not ruled: leave as the C has it

Audit G01 (fire gated by the shooter's own sight; the Mac's G3 covers targeting by sight), G02 (simultaneous against sequential damage), G04 (Intercept never expires in C: a bug against R-086-02 on either reading, report it), G05 (ability auto-trigger), G06 (cover blocks fire), G15 (Warden aura), G16, G17, G18, G19, G24. Each is described in the audit. None is to change under this work; if one blocks a requirement, stop and ask.

## 5. Constraints

- Contracts first: any change to `csrc/ouroboros_sim.h`, `signatures.toml` or the pipe frames (P4 changes what the pipe sends) lands as its own documented contract piece before its consumers.
- Determinism holds: same seed and commands, byte-identical trace on both machines. The Python's module-global cohort counter and unseeded `random` are not ported.
- Tests first, in `tests/csim/`, each naming its rule; every detector with a positive control. For P1, P3, P5 and P8 include side-by-side fixtures: the same small scene run through the Python reference and the C, positions compared within a tolerance proposed to Westley.
- Wired: each behaviour reachable from the tick or a pipe handler.
- Register every file in `docs/northstar/plans/push/pieces.toml` before work starts. The Mac holds `scripts/skilllab/` and `tests/skilllab/` and will not touch `csrc/` until this lands.
- Scale: the engine's unit and canvas requirements (E-13 scale section) still hold; the Python's data structures are not the model for size.

## 6. What comes back

To the design chat, through the repo: the plan file path; the register rows from section 3; when it lands, the commit, and a note of every place the C deliberately differs from the Python. The Mac then regenerates the skill lab's control hashes, re-runs its controls, and starts cascade B.
