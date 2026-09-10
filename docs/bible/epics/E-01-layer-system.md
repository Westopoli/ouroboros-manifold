# E-01 — Layer System

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Yes, 11 stories, 34 rules. Rules that depend on an open flag cite it inline. |
| Every input listed with range and rejection behavior | Yes, see Inputs. Two rejection behaviors are open (Q-002-02, Q-003-01). |
| Every output listed with where it is observable | Yes, see Outputs. On-screen elevation is open (Q-E01-01). |
| Implied-but-unstated behavior turned into flags | 14 new flags raised, Q-001-01 through Q-009-01. |
| Every visible-surface story has a reference | **No.** `references/E-01/notes.md` is a stub awaiting Westley's screenshots. Blocks S-009, S-010, S-006. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on 15 open flags (Q-E01-01 plus 14 new) and on references. Stories are Spec'd, not Ready.

## Purpose

The layer system is the game's strategic defining characteristic. The battlefield is not a flat plane. It is a stack of three to five vertical layers, and a unit is always on exactly one of them. Terrain blocks layers at specific places, so a force can go over an obstacle on a high layer or around it on a low one. Vision across layers is worse than vision on your own layer, so a force on a layer you cannot see is a threat you do not know about. Changing layers costs time and leaves the unit briefly vulnerable.

The promise this keeps for the player (vision_v2 Q6): a smaller force that understands surrounds, high ground, and layers beats a larger force that does not. Every rule below exists to make that promise testable.

Era-agnostic: the engine knows "layers 1 and 2 are blocked here." The era pack decides whether that is an asteroid, a mountain, or a reef. Launch ships the Settled Reach with no per-unit-type layer restrictions.

## Obviously working in 60 seconds

Spawn a Raider and a Bastion on layer 3 next to a tall obstacle. Order both to layer 5. The Raider rises visibly within a second, the Bastion takes several seconds, and each unit's ring changes color when its layer changes. Place an enemy on layer 1 under the obstacle: neither unit sees it. Move an enemy onto layer 4 within half the Raider's sensor range: the Raider sees it, the Bastion does not until it is closer. Fire a pulse: the layer-1 enemy appears for two seconds, then vanishes. Order the Raider to layer 1 through the obstacle: it does not change layer until it moves clear of the blocked zone, then drops.

## Stories

### S-001 — The map decides where each layer is open
As a commander, I want terrain to block specific layers at specific places, so that going over, going around, and hiding in the blocked layers are real choices.

Rules
- R-001-01  Given a map position where layers 1 and 2 are blocked and layers 3 to 5 are open, When any unit on layer 1 or 2 is ordered to move through that position, Then its path avoids the blocked area on its current layer and the unit never occupies the blocked position on layers 1 or 2.
- R-001-02  Given the same position, When a unit on layer 3 moves through it, Then the unit passes straight through with no detour.
- R-001-03  Given a position where every layer is open, When any unit moves through it, Then no layer restriction applies.
- R-001-04  Given any map generated for any era pack, When the map is queried for layer accessibility at every sampled position and layer, Then the answer is a binary open or blocked per layer, and the count of layers is the same for every position on that map.

Inputs: map layer accessibility mask (binary per layer per position); unit position; unit current layer.
Outputs: unit path; unit position over time; layer accessibility query result.
Open flags: Q-001-01 (layer count per map), Q-001-02 (which end is layer 1), Q-001-03 (no route on current layer).

### S-002 — Hard layer transfer
As a commander, I want to order selected units to a specific layer, so that I can commit a force to a height when timing matters.

Rules
- R-002-01  Given a selected unit on layer 3 at a position where layer 5 is open, When the player issues a hard transfer to layer 5, Then the unit begins its transition on the same tick and finishes on layer 5 after its transition duration (S-004).
- R-002-02  Given a selected unit at a position where layer 5 is blocked, When the player issues a hard transfer to layer 5, Then the unit keeps executing its current orders on its current layer, and begins the transition on the first tick it occupies a position where layer 5 is open.
- R-002-03  Given a unit with a pending hard transfer, When the player issues a second hard transfer to a different layer, Then the first transfer is discarded and only the second is pending.
- R-002-04  Given a unit with a pending hard transfer, When the player issues a move order, Then the transfer stays pending; a move order never clears a transfer.
- R-002-05  Given a hard transfer to the unit's current layer, When it is issued, Then it is accepted and completes immediately with no transition and no vulnerability window.
- R-002-06  Given a hard transfer to a layer outside the map's layer range, When it is issued, Then it is rejected and the unit's state does not change.
- R-002-07  Given a hard transfer order for a mixed selection, When it is issued, Then every unit in the selection gets its own pending transfer and each resolves independently by its own position and duration.

Inputs: layer command (target layer, integer in map range); selection (1 to N units); unit position; accessibility mask.
Outputs: per-unit pending transfer; per-unit layer field in the tick delta; transition start and end events.
Open flags: Q-002-01 (non-adjacent target passes through intermediates or not), Q-002-02 (pending transfer never expires, or expires on arrival at the move destination).

### S-003 — Layer preference
As a commander, I want to give units a standing preference for a layer, so that a scouting group stays high and a siege group stays low without me re-ordering them at every obstacle.

Rules
- R-003-01  Given a selected unit with no preference, When the player sets preference to layer 2, Then the unit's preference is 2 and it begins a transition to layer 2 on the first tick it is at a position where layer 2 is open and it is not already on layer 2.
- R-003-02  Given a unit with preference 2 currently on layer 4 because layer 2 is blocked here, When the unit moves to a position where layer 2 is open, Then it begins its transition to layer 2 on that tick without a new order.
- R-003-03  Given a unit with preference 2 at a position where layer 2 is blocked, When any number of ticks pass, Then the unit continues its current orders on its current layer and never stalls or stops to wait.
- R-003-04  Given a unit with preference 2, When the player issues a hard transfer to layer 4, Then the preference is cleared and the hard transfer proceeds.
- R-003-05  Given a unit with preference 2, When the player issues the clear-preference action, Then the preference is cleared and the unit stays on its current layer.
- R-003-06  Given a unit with preference 2, When the player sets preference 3, Then the preference is 3 and any pending transition toward 2 is replaced.
- R-003-07  Given the modifier key held, When the player presses 1 through 5, Then that is a preference assignment, not a control-group recall; and Given the modifier key released, When the player presses 1 through 5, Then that is the standard control-group recall.
- R-003-08  Given a saved mission, When it is loaded, Then every unit's preference is restored exactly.

Inputs: preference command (layer integer or clear); modifier key state; selection.
Outputs: per-unit preferred layer in the tick delta; preference indicator on screen (S-009); save file.
Open flags: Q-003-01 (modifier key default and clear-preference input).

### S-004 — Changing layers takes time and leaves you exposed
As a commander, I want a layer change to cost time that depends on the unit type, so that hopping layers is a commitment and not a free dodge.

Rules
- R-004-01  Given a Raider ordered from layer 3 to layer 4 at an open position, When the transition starts, Then the unit is on layer 4 exactly one transition duration later, with the duration taken from the unit type's transition time [Q-004-01 for the confirmed numbers; current config: Raider 1.0 s, Interceptor 1.2 s, Vanguard 2.5 s, Warden 2.0 s, Bombard 4.0 s, Bastion 5.0 s].
- R-004-02  Given a unit mid-transition, When any unit on its old layer would otherwise attack it, Then the attack does not target it, and the transitioning unit itself cannot attack.
- R-004-03  Given two units of different types ordered to the same layer at the same tick, When the faster type completes, Then the slower type is still mid-transition, and completion order always matches transition-time order.
- R-004-04  Given a unit mid-transition, When a new hard transfer to another layer is issued, Then the unit completes the current transition first and the new transfer becomes pending.
- R-004-05  Given the same seed and the same command stream, When the mission runs twice, Then every transition starts and ends on the same tick both times.

Inputs: unit type transition time (per type, config); transition start tick.
Outputs: unit layer field; transitioning flag in the tick delta; attack eligibility.
Open flags: Q-004-01 (confirm durations), Q-004-02 (movement and new-layer targeting during the window).

### S-005 — Seeing across layers is worse than seeing on your own
As a commander, I want cross-layer vision to shrink with layer distance, so that a force on a layer I am not watching is a real threat.

Rules
- R-005-01  Given an observer with sensor radius 1,000 on layer 3 and an enemy on layer 3 at distance 900, When one tick passes, Then the enemy is in the observer's visible set.
- R-005-02  Given the same observer and an enemy on layer 4 at distance 400, When one tick passes, Then the enemy is visible (adjacent layer factor 0.50, effective radius 500).
- R-005-03  Given the same observer and an enemy on layer 4 at distance 600, When one tick passes, Then the enemy is not visible.
- R-005-04  Given the same observer and an enemy on layer 5 at distance 150, When one tick passes, Then the enemy is visible (two-layer factor 0.20, effective radius 200); at distance 250 it is not.
- R-005-05  Given the same observer and an enemy on layer 1 (two layers below) or any layer three or more away, When one tick passes, Then the enemy is never visible by passive detection at any distance.
- R-005-06  Given an observer standing at a vantage node, When the same enemies are placed, Then the adjacent factor is 1.00, the two-layer factor is 0.40, and a three-layer enemy is visible at factor 0.20.
- R-005-07  Given an observer inside a sensor interference zone of intensity 0.5, When an enemy is on an adjacent layer, Then the effective cross-layer radius is sensor radius × 0.50 × 0.50.
- R-005-08  Given fog on, When an enemy on another layer is outside the effective cross-layer radius, Then it is hidden from the player exactly as a same-layer enemy outside sensor radius is hidden: no silhouette, no marker, no special treatment.

Inputs: observer layer, position, sensor radius; target layer, position; vantage membership; interference intensity at observer position.
Outputs: per-unit visible set in the tick delta; player-visible unit list; fog reveal on screen.
Open flags: Q-005-01 (what counts as standing at a vantage node).

### S-006 — Sensor pulse
As a commander, I want to spend a pulse to see every layer around a unit for a moment, so that scouting before a commitment is a decision with a cost.

Rules
- R-006-01  Given a pulse-capable unit with its pulse ready, When the player triggers the pulse, Then every enemy on every layer within the pulse radius is in the player's visible set for the next 2.0 seconds of sim time (40 ticks at 20 ticks per second).
- R-006-02  Given a pulse that started 2.0 seconds ago, When the next tick runs, Then enemies revealed only by the pulse leave the visible set.
- R-006-03  Given a pulse fired on tick T, When the player tries again before tick T plus 20.0 seconds (400 ticks), Then the command is rejected and the cooldown is unchanged.
- R-006-04  Given the pulse-capable unit is inside an interference zone of intensity 0.5, When it pulses, Then the pulse radius is halved.
- R-006-05  Given a pulse reveals an enemy on layer 1 while the observer is on layer 5, When the pulse expires and no passive detection applies, Then the enemy is hidden again.

Inputs: pulse command; pulse-capable unit; pulse radius (config); cooldown state.
Outputs: pulse active flag and remaining cooldown in the tick delta; revealed set; cooldown ring on the HUD; visible pulse effect on screen.
Open flags: Q-006-01 (which units pulse, radius, and whether the pulse is the unit's one ability), Q-006-02 (last-seen markers after expiry).

### S-007 — Cover blocks sight by height
As a commander, I want a tall obstacle to hide units on more layers than a short one, so that where I put a force relative to terrain changes what the enemy can see.

Rules
- R-007-01  Given an obstacle whose height reaches layer 2 between an observer and a target both on layer 1, When one tick passes, Then the target is not visible.
- R-007-02  Given the same obstacle and both units on layer 3, When one tick passes, Then the target is visible (the obstacle does not reach layer 3).
- R-007-03  Given a target hidden behind cover, When it attacks an observer that cannot see it, Then the attack lands and the target stays hidden; firing never reveals.
- R-007-04  Given a target visible despite nearby cover, When it takes damage, Then damage is unmodified; cover is never a damage reduction.
- R-007-05  Given cover in a unit's path, When it moves, Then movement is unaffected; cover never blocks movement.

Inputs: obstacle position, radius, height; observer and target positions and layers.
Outputs: visible set; damage applied; unit path.
Open flags: none beyond Q-001-01 (obstacle height thresholds depend on the layer count and spacing).

### S-008 — Combat across layers
As a commander, I want to know whether a unit can shoot at an enemy one layer above it, so that layer position is a positional decision and not a guess.

Rules
- R-008-01  Given an attacker on layer 3 and a visible enemy on layer 3 in range, When the attacker is idle or attack-moving, Then it engages.
- R-008-02  Given an attacker on layer 3 and a visible enemy on layer 4 in range, When the attacker is idle or attack-moving, Then [Q-008-01 decides: it does not engage (current code), or it engages with a stated range or damage modifier].
- R-008-03  Given a Bombard's area attack centered on layer 3, When enemies stand on layers 2 and 4 inside the radius, Then [Q-008-01 decides whether they take damage].

Inputs: attacker layer, target layer, range, visibility.
Outputs: attack events; HP changes in the tick delta.
Open flags: Q-008-01 (blocking; this story cannot be tested until answered).

### S-009 — I can see what layer every unit is on
As a commander, I want to see at a glance which layer each unit is on and which layer I am focused on, so that I never have to guess who can see whom.

Rules
- R-009-01  Given any unit on screen, When the player looks at it, Then a ring under the unit shows one color per layer, and the color changes on the tick the unit's layer changes.
- R-009-02  Given a unit with a layer preference, When the player looks at it, Then a second, smaller indicator shows the preferred layer's color, distinct from the current-layer ring [A-299: exact visual pending Track R research; a stand-in indicator is acceptable until then].
- R-009-03  Given the layer strip on the HUD, When the player clicks a layer or presses Tab, Then the focused layer changes and the strip highlights the new one.
- R-009-04  Given the same selection and camera, When a T2 screenshot is taken, Then the ring colors match the sim's per-unit layer field for every unit in view.

Inputs: unit layer, preferred layer; focus click or Tab.
Outputs: ring color per unit; preference indicator; focused layer on the strip.
Open flags: Q-009-01 (what focus does mechanically). Reference required: `references/E-01/notes.md`, missing.

### S-010 — Layers read as height on screen
As a commander, I want a unit on a higher layer to sit visibly higher than one on a lower layer, so that the layer stack reads as a stack and not as a color code.

Rules
- R-010-01  Given a unit on layer L at position (x, y), When it is drawn, Then its world-space height is the layer's elevation from the map's layer mapping [Q-E01-01 decides where the mapping lives; current code: three z-bands 0 to 30, 30 to 100, 100 to 300 for a five-layer count, which is itself a defect].
- R-010-02  Given a unit transitioning from layer 3 to 4, When frames render during the transition, Then its drawn height moves from layer 3's elevation to layer 4's over the transition duration, not as a snap.
- R-010-03  Given a fixed camera and a unit ordered up one layer, When a T2 screenshot is taken before and after, Then the unit's screen position differs vertically by more than 5 percent of the viewport height.

Inputs: layer to elevation mapping; camera.
Outputs: unit world position on screen.
Open flags: Q-E01-01. Reference required: `references/E-01/notes.md`, missing.

### S-011 — Era packs may restrict unit types to layers
As an era designer, I want an era pack to say which layers a unit type may occupy, so that a submarine era or a ground-only era works on the same engine without code changes.

Rules
- R-011-01  Given the Settled Reach era pack (no restriction mask), When any unit type is ordered to any open layer, Then it is accepted.
- R-011-02  Given an era pack whose mask permits type X on layers 4 and 5 only, When a type-X unit is ordered to layer 2, Then the order is rejected and the unit stays on its layer.
- R-011-03  Given the same pack, When a type-X unit spawns, Then it spawns on a permitted layer.
- R-011-04  Given the same pack, When a type-X unit has preference 2, Then the preference is rejected at assignment time.

Inputs: era pack restriction mask (per unit type, set of layers; absent means unrestricted).
Outputs: command acceptance; spawn layer.
Open flags: none. Launch scope: capability present, mask absent (A-294, A-321).

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Layer accessibility mask | Map generator | Binary per layer per sampled position | Not player-issued |
| Layer count | Map or engine | 3 to 5 [Q-001-01] | Map generation fails outside range |
| Hard transfer | Player | Target layer in map range, selection 1 to N | Out of range: rejected, no state change. Era mask forbids: rejected |
| Preference set | Player | Layer in map range or clear | Same as hard transfer |
| Modifier key | Player | Held or released | None |
| Pulse | Player | Pulse-capable selected unit, cooldown ready | On cooldown or not capable: rejected |
| Unit type transition time | Config | 1.0 to 5.0 s [Q-004-01] | Not player-issued |
| Sensor radius, vantage membership, interference intensity | Sim | Per unit, per position | Not player-issued |
| Era restriction mask | Era pack | Per unit type, subset of layers, or absent | Malformed pack fails to load |

## Outputs

| Output | Observable where |
|---|---|
| Unit layer | Tick delta unit entry; ring color on screen; save file |
| Preferred layer | Tick delta unit entry; preference indicator; save file |
| Transitioning flag and remaining time | Tick delta unit entry; drawn height mid-tween |
| Visible set per unit; player-visible list | Tick delta; fog reveal on screen |
| Pulse active, cooldown remaining | Tick delta; HUD cooldown ring; pulse effect on screen |
| Command rejections | Command acknowledgement in the tick delta with a reason code |
| Focused layer | HUD strip highlight |

## Invariants

- A unit is on exactly one layer at every tick, including mid-transition (it is on its old layer until the transition completes).
- No unit ever occupies a position and layer the mask marks blocked.
- Visible set is symmetric in rule, not in outcome: A sees B does not imply B sees A.
- Same seed and command stream produce identical layer, visibility, and transition traces.
- Cover never changes damage or movement.

## Scale requirements

Numbers to be confirmed by Westley in Stage 3. Proposed: 1,000 units computing cross-layer visibility against 1,000 units in under 2 ms per tick; 10,000 units in under 20 ms per tick; accessibility queries at 10,000 per tick in under 1 ms.

## Look and behavior references

`references/E-01/notes.md`. Stub; needs 2 to 5 screenshots or clips with one sentence each on what is wanted and what is not, for: how a layer stack reads on screen, how a unit changing height looks, how the layer ring and strip look, how a pulse looks.

## Ways this could be wrong

- Layer changes are instant in code today; a build that keeps the snap and ignores transition time passes a naive "layer changed" test.
- Visibility set changes but the fog render does not, or the render changes and the set does not.
- Cross-layer factors applied to the wrong axis (target's layer vs observer's).
- Vantage doubling applied to same-layer radius instead of cross-layer only.
- Pulse reveal persists after expiry, or cooldown resets on save and load.
- Preference and hard transfer both set but the wrong one wins.
- Blocked-layer path routes around on the wrong layer, or the unit auto-changes layer without an order.
- Ring colors read from the render's last-known layer instead of the delta.
- Cover blocks movement, or reduces damage, because a physics layer was reused.
- Layer count 5 in config with only 3 elevation bands, so layers 4 and 5 draw at layer 3's height.

## Open ambiguity flags

Q-E01-01, Q-001-01, Q-001-02, Q-001-03, Q-002-01, Q-002-02, Q-003-01, Q-004-01, Q-004-02, Q-005-01, Q-006-01, Q-006-02, Q-008-01, Q-009-01. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-11 Units (unit types, sensor radius, transition time per type).
- E-12 Fog and sensors (sensor radius, interference zones, elevation sensor bonus).
- E-13 Movement and pathing (routing around blocked layers).
- E-17 Map generation (accessibility mask, vantage nodes, cover placement).
- E-16 Camera and HUD (layer strip, rings, elevation on screen).
