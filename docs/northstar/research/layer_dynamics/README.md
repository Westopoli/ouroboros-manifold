# Layer dynamics: the layer lab

## 1. Purpose and status

Opened 2026-09-30. Design phase for the research program in register `Q-008-02` and research queue `Q76`. It feeds `Q-008-03` (the cross-layer numbers), E-01 S-008, E-12 (fog and sensors) and E-14 S-125 (what hard-mode AI strives for). Nothing here is bible text. When the lab yields numbers they are folded into `algorithms.md` and the S-008 rules, and this document is then a record.

The question: how do units on different layers damage and see each other so that the engagement's conditions, not the raw numbers, decide who wins? The method: a fast standalone C simulator (the layer lab, `toys/layerlab/`) that carries the system's constraints, run in small engagements that vary everything an RTS varies, read after every run, tuned, and run again.

## 2. Westley's own words, verbatim

2026-09-30.

> "The player owns the layer, so nothing ever changes it automatically." Unless their units are forced because of terrain. If they move-command someplace that doesn't have access to the layer they're on, but does have access on another layer that they can transition to, then their units automatically transition (like units walking up a mountain). Record that decision.

> I'd like to start ( idea about layer simulation, simple prototype to tune numbers to produce strategy situations ) a specific method of figuring out how we'll do this. We will build a "toy" prototype. It will have the basic functions of the game, and be very fast, all C, bare minimum visuals maybe with python game library or something simple. It will contain the restraints of the system, layers, damage, vision, landscape. The prototype will run "simulations" of unit complex combinations: position, orientation, damage, health, anything that we can vary in an RTS. We'll use this simulator to document the relationships between all the variables and find the places that the "lines cross". We'll use this as a map for tuning units across different eras, and maintaining strategic depth. For example, we may notice that changing the vision variable only produces only strategic depth at a specific "value" given the values of all the other variables, however, if we change another one, the "lines cross" in more than one place, and induce strategic depth from two configurations of variables instead of one. This will require significant iterations and tuning, so the algorithms need to be fast. This is just an idea in my head currently, I want to explore it further and verify it works with a simple prototype before we commit to building the full thing.

> We'll need to clearly define what "strategic depth" looks like, but we can grab from other similar high skill games like Starcraft 2. For example, in starcraft 2 when units have a layer advantage, they can shoot without being shot back. When units have a surround, the units in the concave with the surround win. Organizing your units in specific patterns can lead to better engagements, depending on the unit, it's vulnerabilities and abilities, etc. For example: templar are very weak and slow and expensive, but when they use storm they're devestating to low-health units. A player that effectively protects them has a higher chance of winning. We will need to map all these dimensions out before we build anything.

> Develop a plan to document the idea in the bible (with a pass after it's documented cross-referencing my original prompt with what was actually written for missed information or hallucinations), map out the dimensions, build a toy prototype of it, and find out if the hypothetical "lines crossing" is evident in the data (configurations that produce victory from the expected player given the conditions of the engagement). We don't need to do a large batch of thousands of "runs" and then analyze the data, I think it'd be much faster to iteratively try small things, check the output, and tune repetatively.

Also in scope from 2026-09-23 (`Q-008-02`): a surround theory taken into three dimensions, drawing on high-altitude aerial battle research.

## 3. Fixed constraints

These come from the bible and the register; the lab does not vary them unless a run says so.

- Five layers, always; layer 1 is the bottom (Q-001-01, Q-001-02). A unit is on exactly one layer at every tick.
- Terrain blocks layers at places (E-01 S-001). A unit never occupies a blocked position and layer.
- Terrain-forced auto-transition: a move order to a place blocked on the unit's layer but open on another auto-transitions it (E-01 R-001-05). The lab has an off switch for it only because a control needs an off state; the ruling itself is settled. The edges the ruling leaves open are `Q-001-04`; the lab takes the recommended reading there and can vary it.
- A transition is one transition of one duration regardless of distance (Q-002-01), by unit type (Q-004-01: Raider 1.0 s, Interceptor 1.2 s, Vanguard 2.5 s, Warden 2.0 s, Bombard 4.0 s, Bastion 5.0 s). The old layer may attack the unit until the halfway point, the new layer from the halfway point on; visibility follows the normal cross-layer sensor rules (Q-004-02). E-01 R-004-02 still says the old layer cannot attack a transitioning unit; that is an existing conflict between the epic and the register, not settled here, and the lab runs the register's halfway rule.
- Vision across layers shrinks with distance: production uses factor 0.50 one layer away, 0.20 two layers away, none beyond, by absolute offset in either direction (`csrc/fog.c:585`); E-01 R-005-05 says two layers below is never visible, which disagrees (`Q-005-02`), so the lab takes vision by signed offset and can test both; vantage nodes and interference zones modify it; cover blocks sight by height and never changes damage or movement (E-01 S-007).
- Production combat is same-layer only (Q-008-01). Every cross-layer rule in the lab is a hypothesis under test, not a fact about the game.
- Layer damage is weighted much more heavily than abilities and passives (Q-083-02, hub principle 4): an ability never outranks position in the lab either.
- Determinism: same seed and command stream give a byte-identical trace.

## 4. Strategic depth: the definition and four test cases

The hub definition (principle 4): the engagement's conditions, not its numbers, decide who wins. Westley's examples are from StarCraft 2; the four patterns below are their abstract form, and each is a named test case. "Expected winner" is what a knowledgeable player would predict from the conditions alone.

| Pattern | Source | Expected winner | What proves it (observables) |
|---|---|---|---|
| P1 High-ground asymmetry | "when units have a layer advantage, they can shoot without being shot back" | The force with the layer advantage | Unanswered-fire ticks per side; first-shot side; HP-remaining ratio; ticks until the disadvantaged side fires |
| P2 The concave in a surround | "when units have a surround, the units in the concave with the surround win" | The side in the concave | Winner and HP-remaining ratio across formation and count; cost lost per side |
| P3 The screened glass cannon | templar are "very weak and slow and expensive, but when they use storm they're devestating to low-health units. A player that effectively protects them has a higher chance of winning" | The player who protects the fragile unit has the higher chance of winning | Win rate across seeds as screen radius varies against enemy speed; cost lost; burst damage landed |
| P4 The smaller force wins by position | "Organizing your units in specific patterns can lead to better engagements" and the promise in E-01 | The smaller force, in the configuration where position outweighs numbers | Winner with unequal counts; the smallest count ratio at which the smaller side still wins |

Depth holds for a cross-layer rule set when each pattern is true under at least one reachable configuration (one the game can produce) and none is true under every configuration. A pattern true everywhere is a dominant strategy; a pattern true nowhere is a dead mechanic.

## 5. The dimension map

Drafted as the last step of the design phase; Westley confirms it before the toy build starts.

## 6. The "lines cross" hypothesis, stated testably

Take a variable v (for example the range multiplier for fire from above) and hold every other variable fixed. The expected side's win probability is a function of v. It crosses 0.5 at some value v*. Depth exists on that axis when v* is reachable in play, meaning v* lies inside the range of values the game can produce. Now move a second variable w. Depth grows when w moves v* to another reachable value, or when w creates a second crossing, so two configurations of variables induce depth instead of one. That is Westley's "lines cross".

Pass criterion for the lab, proposed here for Westley to confirm or change (he owns it): at least one crossing on a layer-rule axis, and at least one two-variable interaction that adds a crossing.

Negative control: with the cross-layer rules off (multipliers zero, no cross-layer fire), no crossing on that axis. A detector that finds crossings with the mechanism off is measuring the harness, not the game. Positive control: the count ratio between two equal forces on flat ground, swept from 1:2 to 2:1, must show its crossing near 1:1; a detector that misses that is not reading.

## 7. The lab

`toys/layerlab/` (created when the build starts): standalone C simulation, Python driver (scenarios, sweeps, plots, replay). It reuses csrc's numbers as starting values and none of its code. Spec: `toys/layerlab/SPEC.md`, written before the build. It is built in four rungs, R0 to R3: flat combat and determinism; terrain, vision, transitions and every cross-layer knob; facing, formations and the storm-shaped ability; sweeps, replay and the run log. Every run is small: a handful of seeds and a few values, read at once, then tuned.

Every logged result carries a transfer class. T1: rule geometry that ports to the game as is. T2: magnitudes whose direction transfers while the numbers retune (no economy, no brace, fortify or cohort targeting, symmetric fog). T3: lab-only (steering, coarse pathing, formation drift, pulse trigger heuristic, stalemate window).

A run is logged in §8 with its date, the configuration difference from the previous run, the table, a link to the plot, and what changes next.

## 8. Run log

No runs yet.

## 9. Verdict and fold

Filled when the pass criterion in §6 is met or shown unreachable. If met: numbers go to `algorithms.md` as ALG rows, S-008 gains rules with values, `Q-008-02` and `Q-008-03` close, and the E-01 gate is re-run. If not met: record what the lab could not show and why, and revise the method; the cross-layer numbers stay open, and Westley decides whether the strategic-depth definition in the hub stands.
