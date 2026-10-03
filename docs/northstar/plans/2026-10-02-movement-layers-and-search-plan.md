# Movement and layers into the MVP engine, then the search for where the lines cross

## Context

The Mac design chat stopped on 2026-10-02 and handed the layer-dynamics work to Linux (`docs/northstar/research/layer_dynamics/LEAVE_OFF.md`). This plan picks it up. Read in full for this draft: LEAVE_OFF, README, the harness-check run, the port audit, the history, all three crosschecks, the parity requirements, the cascade brief, the harness spec and code, E-01, E-11, E-12, E-13, principle 4, the three research briefs, the register rows they cite. Read by mappers only: the Python and C source.

- **Goal (Westley):** "players with better understanding of the landscape, unit formation, layer awareness/intentionality, and the other players current position can defeat a much larger force". "The *lines* can cross in multiple locations".
- **Defined in the repo:** a line is the edge, in the space of settings, of where one condition holds; the crossing is a region where C0 to C9 all hold; several regions may exist (README 4). Measure: margin, break-even in whole units, units able to fire per side through the fight. Chart form: README 5.
- **Flag, not a stop:** the pass marks for C0 to C9 are drafts he has not confirmed; only the restatement (skill wins the firing count, the result follows it, 30 percent and 2x to 3x as rough sizes) is his. The search (Phase E) does not start until he sets them.
- **Problem:** the C engine lost the Python's movement (armies end as two flat rows), units fire at what nobody sees, and no layer action exists.

Order (Westley, 2026-10-02): the movement system as ruled, layers and all, into the MVP engine first; then simulations and chart pages. Engine only; client controls and pipe frames later. One builder chat runs builds (manager mode, tests first, scale asserted) and batches; I plan, rule, check each page against the method, and bring it to him.

## Decisions (Westley, this chat, 2026-10-02; recorded in W0)

| Item | Decision |
|---|---|
| Movement | "the same exact logic from the python"; P1 to P9 as ruled |
| Group speed | Slowest member (Q-095-01: a movement ability detaches the unit). Ruled difference from Python |
| 200 wu leash before damage | A switch; the lab runs both; he picks |
| Unit in solid terrain | Pushed out (R-097-09), not the Python stall |
| P4 map content | Held for his environment design. Terrain is hand-placed blocked rectangles |
| Whose sight gates fire | The side's shared sight (a spotter or a ping lets long-range units fire) |
| Siege needs eyes | Accepted: Bombards and Bastions (sensor 300) fire at range only when a friendly unit or a ping sees the target |
| Cover and fire | Fire follows the vision rule: a cover obstacle blocks only a line passing through it between two outside units (R-098-02). A unit standing inside one is seen and shot as normal |
| Cover height | Built now: each cover obstacle has a height in layers and blocks sight and fire only up to it (E-01 S-007) |
| Terrain block threshold | Above 0.7, as the bible and C |
| Lone unit on attack-move | Resumes its march after the fight; "the group ends" applies to groups of two or more |
| Units pushing apart | As the Python: "the way that it worked on the Python simulation was perfect" |
| Target choice | Nearest stays the game's rule. A lab-only setting for focus fire is added, and one batch measures how it changes the results |
| Guard stance | Decided after movement lands and a choke defence has been looked at; the landscape batch waits for it |
| Scope | Engine only |

## Phase A: port parity

| Req | Change | Files |
|---|---|---|
| P8 | Sweep +30, -30, +60, -60, +90, -90; first clear; none clear continues straight; same-layer blockers; group mates block; probe against start-of-tick positions; detour counted by distance moved; fixed direction vectors, no trig | `csrc/tactical_move.c`; six-angle constants through `docs/bible/algorithms.md` and `scripts/specfactory/alg_constants.py` |
| P7 | Faces engaged target within 1.5 x range, else move target, else velocity; stationary firing units turn | `tactical_move.c` |
| P5 | Attack-move takes slots through `om_command_group_move`; a group of two or more ends when every member has engaged, no resume; a lone unit resumes. Slowest-member cap kept, and a movement ability detaches the unit (Q-095-01). Fixed tables from audit G23 (64 groups, 64 members, 1,024 queued orders, discovery ids to 255, route cache 256, cover and obstacles 256, fog zones 64, vantage 32, structures 64) are each sized for `OM_MAX_UNITS` and the largest canvas or shown not to bind, first, or the 10,000-unit test fails | `unit.c`, `tactical_move.c` |
| Collision | As the Python: same-layer pairs only; only units that moved start a pair check; two stationary units split the push when either moved this tick; arrival within the Python's radii without snapping; clamp and slide. One exception brought to Westley, not ported silently: the Python flings two units on the exact same spot apart by a thousand times the normal push (audit G14) | `tactical_move.c`; R-097-10, R-097-07, R-099-04 reworded |
| P1 | On the cohort turn, no target in range and a visible enemy in sensor range: move goal becomes that enemy, walked by the ordinary movement step; holds only while its own target is in range; chase persists after arrival; a kept out-of-range target survives between cohort turns | `csrc/unit.c` |
| P2 | First attack ready on the tick the target is first in range | `unit.c` |
| P6 | Return fire also turns attack-moving units; lowest-id same-layer attacker; out of range, attack-move to it and drop the old destination | `unit.c` |
| P3 | Canvas size known to movement, set at mission setup (`mission.c`); positions clamped; route on the 100 wu grid per layer (R-097-01; E-13's scale line says 60 wu cells, corrected to 100 in W0), blocked above 0.7, straightened by line of sight, waypoints, cached; dense grid replaces the 1,024-entry list; `om_map_block_rect` (brief G2); a blocked cell blocks sight and fire on its layers; `om_map_sample_layer_accessibility` reads the grid; a unit never enters a blocked cell (E-13 invariant) and one found inside is moved to the nearest open cell; obstacle repulsion works as R-097-09 says; terrain slow (R-097-06, ruled in Q-099-01) reads the same grid, so hand-placed terrain slows units and live maps are unaffected until P4 | header, `signatures.toml`, `mission.c`, `tactical_move.c`, `tactical_mapgen.c`, `fog.c` |
| P9 | Capture census computed each tick (300 wu, one non-owner faction, no owner, 10 s) | `csrc/tactical_support.c` |
| Cover | Endpoint exemption for fire, as vision has; a height in layers per obstacle, blocking sight and fire only up to it (R-007-01, R-007-02) | `tactical_move.c` (`om_combat_can_shoot`), `fog.c`, `tactical_mapgen.c`, header |
| Settings | `om_tactical_set_param` (brief G1) is built here, first, as the one contract piece of this phase, because Phase A needs it: `OM_TP_PURSUE_BY_STEERING`, `OM_TP_ROUTE_AROUND_TERRAIN` (both default 1, 0 gives the old behaviour for the hash baseline), the leash-before-damage switch, the target-choice setting (nearest by default, most damaged for the lab). The side Westley does not pick for the leash is deleted, not left behind | header, `signatures.toml`, `unit.c`, `tactical_move.c` |

One ABI bump for the whole plan: every header change of Phases A and C (settings, canvas size, block-rect, cover height, the layer calls) is drafted in W0 as one contract piece, documented before any implementation.

Left as the C has it (requirements section 4): audit G02, G05, G16 to G19, G24. Overridden by Westley's decisions above and so changed: G01 (side sight, in Phase C), G06 (cover), G14 (collision). Bugs against rules already ruled, fixed under their owners with a test first, not asked again: G04 (Intercept never expires, R-086-02); G15 (a second Warden must add 0.05, Q-084-01; the C gives 0.09). Recorded as not built and not in this plan: the flinch when an attacker is visible but unreachable (Q-088-01) and the cross-layer flee (G12). Every deliberate difference from the Python (fixed direction vectors in place of trig, id order, seeded random, the speed cap, the push-out, the fling) is listed in one document at the end of the phase (requirements section 6).

Verification, written first:
1. **Side-by-side with the Python** (`tests/csim/parity/`): the same small scene through `simulation/` (`TacticalEngine`) and the C; per-tick position, target, facing. The fixture resets the Python's module globals (`damage._targeting_tick`, `facing._prev_*`), uses hand-built maps, and no unseeded random. Scenes from `simulation/test_maps.py`, `test_obstacle_navigation._build_wall_map`, `test_attack_move_basic._run_scenario`: unit behind its own row; target walks out of range; three in file; attack-move group of 8; wall with a gap; return fire on the march. The unchanged C fails each. Tolerance measured first, proposed to Westley, then fixed.
2. **Rule tests** in `tests/csim/`, one per rewritten rule (R-084-01, R-087-04, R-087-05 and R-096-03 with the leash switch both ways, R-087-06, R-095-01 and R-095-06 for the cap and the detach, R-096-02 for the group and the lone unit, R-097-01/02/03/05/06/07/09, R-098-02, R-007-01/02, R-099-04, R-100-01, R-127-01/02, R-086-02, R-083-03), each with a positive control. R-095-01's "not built" tag is removed. Tests asserting old text become `test-defect` rows, listed up front: `test_E13_S097_around_not_through.py:66`; the R-127 tests that feed the census by setters; `test_E13_S096_four_commands.py:60`; a new attack-moving case in `test_E11_S087_*`.
3. **Live game:** a pipe test in `tests/transport/` (attack-move group: slots, pursuit, hold, damage dealt at the objective) and a new desktop case beside `tests/qa/desktop/test_tactical_play.py` using the detectors in `scripts/qa/rts_detectors.py`.
4. **Scale, every wave:** movement and collision 3 ms at 1,000 and 30 ms at 10,000; targeting and damage 2 ms and 25 ms; route queries 1,000 per second; pipe round trip under 100 ms at 5,000 (the 10,000 figures at the 10 ticks per second the sim runs above 1,000 live units, R-099-03); O0 against O2 identical; `reach_lint` shows each behaviour reached from `om_tactical_step`. With the two movement switches at 0 the recorded hashes are unchanged (the baseline); hashes that change on purpose at 1 are re-recorded once per wave with a ledger row.
5. **Every wave report says:** live maps still carry no terrain and the pipe still sends `obstacles: []` (P4 held), so routing, slow and cover height show only in tests and the lab.

## Phase B: first read with Westley

First of all, before any engine change: `python3 -m pytest -q tests/skilllab` on Linux; a mismatch with the Mac's hashes is a determinism finding for him, not patched. The harness pieces this phase needs (the position trace, the settings binding) are built in wave A1, not left to Phase S. After Phase A: positions printed through one mirror fight (does a formation now survive the walk; the plays' contact placement is revisited), `python3 -m scripts.skilllab controls`, the leash both ways, a choke defence looked at tick by tick for the guard decision, and the one-page chart. `golden_hashes.json` is regenerated on Linux, which is now the only machine; the cross-machine test is kept and noted as unverified on the Mac until someone runs it there. With the page I bring him, each with context and a small diagram, never a bare list: the draft pass marks; the win margin (0.05); whether concentration of fire joins the principle; the S2 roll-up counter (never confirmed); the guard stance; the Python's same-spot fling.

## Phase C: the layer system in the engine (brief section 5)

The contract landed in W0 and G1 in Phase A. G0 (`.gdignore` files, and the Makefile guard so the Mac can build again when it returns; small, kept for that reason); the rest of G1's parameters; G3 targeting, pursuit and fire by the side's visible set (P1's "visible" is the unit's own set in Phase A, as the Python, and becomes the side's here; the page of Phase B says so); G4 layer change orders with the cross-over at halfway and routing across layers by travel time; G5 reach by type, applied to area attacks and return fire too, with range, damage and area multipliers per signed layer offset and the vision factor per signed offset as settings (the Q-008-03 families, which the three lever tables need); G6 going dark; G7 the targeted ping with its alert and 60-degree sector. A seer type at very high cost is a lab unit type (Q-005-04), not an engine change. Tests as the brief lists, plus the rules it leaves out: R-002-02 to R-002-07 (pending, replace, move keeps it, same-layer no-op, out of range rejected, mixed selection), R-004-04, R-008-03, R-008-04.

- Switches `OM_TP_TARGET_BY_SIGHT` and `OM_TP_ROUTE_ACROSS_LAYERS` default to the bible's rule (1). The hash invariant is asserted with them at 0 against the end-of-Phase-A hashes; the controls are re-hashed at 1 and the difference reported.
- Scale figures for E-01 (visibility, accessibility queries) are marked "proposed" in the epic; they are used as targets and brought to Westley for confirmation with the first Phase C report.
- Engine defaults keep reach 0 and silent; the brief's section 6 numbers are the design chat's proposals, applied by the lab as settings, not confirmed by Westley.
- Scale: visibility 2 ms at 1,000 and 20 ms at 10,000 by spatial hashing; 10,000 accessibility queries under 1 ms; targeting and damage 25 ms at 10,000 with sight and reach on.
- Not built: layer preference (S-003), era masks (S-011), slopes and walking units, scouts, the pulse, client display. Land maps are therefore not measured; said on every report.

## Phase S: the harness grows (alongside C; `scripts/skilllab/`, tests first)

Today it has four symmetric single-type plays, an unweighted same-layer firing count, orders only at tick 0, and no condition checker. Needed before batches:
- per-tick trace of position, target, facing; terrain, layer orders, reach, emission, ping and per-fight settings in `Setup`; a unit-type-weighted firing count that uses side sight and reach;
- asymmetric plays: skilled, naive blob, naive line abreast, counter; mixed unit types; two force sizes per cell;
- an order timeline (orders at a tick, on arrival, when an enemy is seen), which the bait, ambush and fall-back plays need; a guard stance is the engine's anchor and leash ("Yes a guard stance is fine");
- break-even by scan that flags a curve that flips more than once and runs the side-swap control; more fights per cell near a break-even;
- the condition checker for C0 to C9 with thresholds as inputs (Westley's), the 32-combination skill profile, guard cells (all siege, camp the top layer, a max-range blob);
- chart forms beyond the controls page: the two-settings map shaded where all conditions hold, the decision-tree summary, a matchup grid for S5, small multiples; a new form is allowed when the data changes;
- the speed gate re-measured, since fights get slower; a process-pool runner (plain data to workers, entry point guarded, README 9), which the search needs;
- a situation sampler: space maps built from hand-placed blocked rectangles, cover with height and layers (open, block, wall, lane, cover field), sampled and asymmetric, with the naive-against-naive break-even of each map reported beside every result ("the landscape will be autogenerated and not symmetrical"); C8's share of maps is counted over these;
- every result row carries how far it transfers: rule geometry that holds as is, or magnitudes that will retune;
- chart rules from the research: counts not ratios, position on a common scale, no log scales, no dual axes, small multiples not animation.

## Phase D: small batches, one skill at a time

Order (README 8): formation, matchup, landscape, enemy position, layers, the knobs, combinations and counters. Each batch: look at what the play does before measuring; one map, one size, then widen; one run file in `layer_dynamics/runs/`; one chart page; the builder stops; I check it and bring it to Westley; the next starts on his word. Carried from the record:
- formation on short-range Raiders (at range 350 every unit fires in any formation); reach against body size swept;
- free controls from combat theory: the choke as a switch from square to linear law, packets keeping sqrt(1 - 1/k); his order, choke then defeat in detail (the ramp waits for slopes);
- the three lever tables he asked to see side by side: vision only, vision and reach, vision, reach and damage;
- **the focus-fire batch (Westley's request):** the controls and each skill's headline cells run twice, nearest and most-damaged, with one page on what changes: break-evens, firing counts, fight length, which skills gain or lose. Nearest remains the game's rule;
- the formation batch includes a concave that curves around the point where the enemy arrives, since the toy's scripted arc "is not yet the concave Westley means";
- the landscape batch waits for the guard decision; tall cover with height and its counter (a layer above it) are in it;
- the seer at very high cost is measured against the ping;
- firing arcs are not built or measured (the toy's E6); land maps are not measured;
- a surprising result is first a question about the instrument.

## Phase E: the search

After Westley sets the pass marks. Every region where the conditions hold, two ways side by side: all settings at once, unit numbers included ("literally everything"), and two variables first then adding. Compared on: whether each reaches a passing rule set, fights used, how it holds on situations neither saw, how well each step can be explained. More than one region is a result, not a tie to break ("strategic depth from two configurations of variables instead of one"); the regions are the map for tuning other eras. Then his read; the layer actions go into the MVP client at once, as he asked (LEAVE_OFF step 6), under a plan I write as soon as he has read a working configuration; numbers fold into `algorithms.md` and S-008, closing Q-008-02 and Q-008-03.

## How it is run

- **W0, me, on approval:** rulings addendum with the decisions above. Bible rewritten in the same commit: side sight in E-12 (Purpose, S-093's title and R-093-02, the invariant "visibility never changes combat resolution", the wrong-ways line) and E-01 (R-008-04, R-004-02's "its sight"); E-11's Bombard example gains a spotter; R-098-02 and S-007 for the cover exemption and height; R-096-02 for the lone unit; R-097-10, R-097-07, R-099-04 for the Python's collision; E-13's 60 wu scale line; R-095-01's tag. Test defects listed for the builder: the Bombard mirror at 1,000 in the R-085-04 test, and the cover test. Register: the two rows sharing id Q-098-01 and the two sharing Q-101-01 are given distinct ids; the cover-height row closes as built; rows opened for the guard stance, the fling, concentration of fire, how refusing a fight is checked, and the S5 reading of C1 and C2. Definition of Ready: the E-01, E-11, E-12 and E-13 gates are re-run against the stories this plan builds, and a story with an open flag is not handed to the builder. `pieces.toml` rows for `tests/csim/parity/**`, the one contract piece, `tactical_move.c`, `unit.c`, `tactical_support.c`, `fog.c`, `tactical_mapgen.c`, `mission.c` (canvas size only), the constants, `scripts/skilllab/**`, `tests/skilllab/**`; the coordinator's speed round 2 answered (its two exact units land first, then it stays off those files; the target search is rewritten by P1); this plan to main as `docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md`; LEAVE_OFF points at it; then the paste for the builder chat.
- **Builder chat:** manager-mode-lite: all Sonnet 5.5; test writer, separate auditor, then implementer; implementers never edit tests; units about one file and 100 lines; sub-agents never spawn; branches `push/pp-*`, `push/ls-*`, `push/sl-*`, landed through `scripts/specfactory/merge_gate.sh`. Waves: A1 parity harness, failing tests, the settings call, the table sizes; A2 `tactical_move.c` (P8, P7, clamp, collision, cover) with P9 and the two bug fixes beside it; A3 `unit.c` (P2, P1, P6) then P5; A4 routing, terrain, cover height; B; C by the brief's waves with S beside it; D batch by batch; E. One report per wave; it stops for a ruling when a rule is unclear or a budget is missed. Nothing is loosened.

## Still Westley's, asked when reached

Each is brought with context and a small diagram. After Phase A: the parity tolerance; the guard stance; the same-spot fling; the leash, from the chart. With the first chart: pass marks C0 to C9 and the win margin; concentration of fire; the roll-up counter; how refusing a fight is checked; whether unit-type matchup is judged by the weighted firing count. Before Phase C: emission per unit or per group; the provisional layer numbers; the E-01 scale figures. Later: whether abilities join the bar; whether E-13 bounds the worst step (from the worker chat's speed work); the fight-length flags Q-085-01 and Q-085-02. Held with P4: asteroid height, the E-17 gate and Q-119-02.

## Risks

- `unit.c` is in use by the coordinator; A3 waits for its two units. A1 and A2 do not.
- Exact parity through collisions may not hold (Python iterates a set, C goes by id); tolerance is measured before it is promised.
- Side-sight targeting and routing at 10,000 units are the likely budget misses; gated every wave.
- The harness work is as large as the engine work; batches cannot start on plays the harness cannot express.
- Without a guard stance the choke and concave plays may read weak, as in the toy; that is why the decision sits right after Phase A.
- Fixed direction vectors in place of the Python's trig move positions slightly; the parity tolerance has to absorb it.

## Appendix: the contract piece (`PP-contract`), documented before implementation

One piece, one ABI bump, landed first by the builder (header, `signatures.toml`, generated bindings by `sig_table --emit`). Names follow the header's style and may be adjusted to `signatures.toml` conventions; behaviour may not. Calls marked (brief) are specified in `2026-10-02-skill-lab-cascade.md` section 5 and are not repeated here.

| Call | Purpose | Phase |
|---|---|---|
| `om_tactical_get_param`, `om_tactical_set_param`, enum `om_tac_param` (brief G1) | Rule numbers and switches at run time. Out of range is refused and changes nothing. Includes `OM_TP_PURSUE_BY_STEERING`, `OM_TP_ROUTE_AROUND_TERRAIN`, `OM_TP_TARGET_BY_SIGHT`, `OM_TP_ROUTE_ACROSS_LAYERS` (default 1), `OM_TP_LEASH_BEFORE_DAMAGE` (default 0, today's order), `OM_TP_TARGET_POLICY` (0 nearest, the default and the game's rule; 1 most damaged, lab only), the leash, the cross-layer vision, range, damage and area factors by signed offset, the emission and ping numbers | A, C |
| `int om_map_set_canvas(om_world *w, double width, double height)` | The map size movement clamps to; called by mission setup. 0 ok; -1 on a non-positive size | A |
| `int om_map_block_rect(om_world *w, double x0, double y0, double x1, double y1, uint32_t layer_lo, uint32_t layer_hi)` (brief G2) | Blocks the route-grid cells a rectangle covers on a range of layers | A |
| `uint32_t om_map_add_cover(om_world *w, double x, double y, double radius, double height)` (existing call, signature unchanged) | `height` is read as a whole count of layers from the bottom: the obstacle blocks sight and fire on bible layers 1 to `height` (engine layers 0 to `height` - 1). 5.0, which every live caller passes, is all five layers. A fractional, negative or above-five value is refused (A132) | A |
| `om_command_set_layer`, `om_unit_transition_progress`, `om_unit_get_target_layer` (brief G4) | Layer change orders | C |
| `om_roster_set_reach`, `om_unit_profile_reach` (brief G5) | Reach by unit type | C |
| `om_command_set_emission`, `om_unit_get_emission` (brief G6) | Going dark | C |
| `om_command_ping`, `om_ping_alert_count`, `om_ping_alert_get` (brief G7) | The targeted ping and its alert | C |

The builder reports any call here that already exists under another name instead of adding a second one. No pipe frame changes in this plan.
