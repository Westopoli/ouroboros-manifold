# Control group depth: perception brief

## 1. Feature and status

E-16 S-105 "Selection and control groups", rules R-105-01 to R-105-06 (`docs/bible/epics/E-16-client-camera-hud-and-world-view.md:61-72`). The open design item is recorded in E-16 "Ways this could be wrong" (`:190`) and research item RL-Q75 (`docs/legacy/research_lane_queue.md:93`), never run. Flags Q-105-01 and Q-106-01 closed (`docs/northstar/ambiguity_register.md:101-102`). Related closed flags: Q-E03-01 group pace (`:17`), Q-101-01 arrival (`:98`), Q-003-01 layer modifier (`:24`). No story exists for sub-groups yet.

## 2. Player-facing goal as documented

"As a commander, I want to click, box-select, and bind groups, and never to have an all-army button, so that positional thinking is the whole game." (`E-16:61`)

"Control-group depth. Westley's target (2026-09-14): a talented player runs three armies with two or three layers inside each, so control groups need sub-groups per layer without violating exclusive membership (Principle 4). Open research item RL-Q75; no story yet. The risk is that R-105-02's flat digit groups make multi-layer armies unmanageable and players ask for the all-army button we refuse." (`E-16:190`)

Principle 6 (hub, `docs/bible/game_bible.md:78`): "Any feature that lets the player issue an order without thinking about where their units are is excluded, at every difficulty. There is no all-army command. Control-group exclusive membership is the canonical instance."

Litmus test (`docs/bible_history/bible_2_00_design_vision.md:65`): "does this feature let the player issue an order without thinking about where their units are? If yes, it violates this principle."

## 3. Westley's own words

Q-105-01 answer, 2026-09-14 (`ambiguity_register.md:101`): "(b), a drag box selects every layer; a player who wants one layer's units narrows the selection with the layer hotkeys. Westley also set a target: a talented player handles three armies with two or three layers each, so control groups need sub-groups per layer; research item RL-Q75."

Q-106-01 answer, 2026-09-12 (`ambiguity_register.md:102`): "No replacement needed. "Players should already have access to army hotkeys and easy ability usage (since all abilities are contained within the same command card, immortal style)." Hotkey affordance exists; don't remove it."

A-300, 2026-09-10 (`docs/legacy/agora_era/stage1_audit.md:472`): "Cross-check resolved (2026-09-10): Westley says remove the all-army hotkey now — it is not supposed to make it into the game."

Q-E03-01 answer, 2026-09-10 (`ambiguity_register.md:17`): "(c) — Halo Wars model. Keep both mechanics, but reverse the speed-matching clause: a selection moves together at its slowest unit's pace by default (not strung-out arrival), and formation-preserving destination assignment is exactly the mechanism that makes uniform-pace cohesion work. Players can deliberately split off their own sub-groups to move independently at a different pace if they want a faster element to detach."

Q-101-01 answer, 2026-09-16 (`ambiguity_register.md:98`): "Halo Wars group centroid model: arrival is defined when the average of all unit positions (the group center) reaches the destination target point, while units maintain their destination formation offsets."

## 4. Fixed constraints any option must honor

- R-105-01: click selects one; a drag box selects every friendly unit inside it on every layer (`E-16:64`).
- R-105-06: with a selection spanning layers, the layer hotkey N narrows the selection to layer N; strip focus unchanged (`:65`).
- R-105-02: Ctrl plus digit binds; exclusive membership (a unit leaves any other group); digit recalls; double-tap centers the camera (`:66`).
- R-105-03: Tab cycles layer-strip focus (`:67`). R-105-05: Shift-click adds or removes (`:69`).
- R-105-04: no select-all, select-all-army, or select-all-of-type command exists (`:68`).
- R-104-07: each bound group's tab shows its unit-type icon and count (`:51`).
- Key space: Alt plus 1 to 5 sets layer preference, Alt plus 0 clears (Q-003-01); the modifier remap is temporary and control groups keep 1 to 0 in normal play (`docs/bible_history/bible_2_00_combat.md:155`).
- A selection moves at its slowest unit's pace; the player may split off a sub-group to move faster (Q-E03-01).
- Layer focus is purely visual; it never filters selection or orders (Q-009-01, `ambiguity_register.md:31`).
- Always 5 layers. Each unit is on exactly one.
- Accessibility never comes from flattening space (Principle 6).

## 5. Prior art already named

StarCraft 2 subgroup tab-cycling, Halo Wars group handling, Supreme Commander hierarchical groups, Immortal: Gates of Pyre control scheme and command card (RL-Q75, `research_lane_queue.md:93`; Q-106-01). Halo Wars pace and centroid model (Q-E03-01, Q-101-01).

## 6. Contradictions, as questions for Westley

1. Q-106-01 says "Players should already have access to army hotkeys" and the register concludes "don't remove it", while A-300 and R-105-04 remove the all-army hotkey. Confirm "army hotkeys" means the control-group hotkeys (1 to 0), not a select-all.
2. "Sub-group" has two meanings on record: per-layer sub-groups inside a control group (Q-105-01, E-16:190), and an ad-hoc split-off so a faster element can detach (Q-E03-01). Are both wanted, and are they the same mechanism?
3. Sub-groups per layer inside a group and exclusive membership on flat digits cannot both be true as written. Is exclusive membership about the top-level group only (a unit belongs to one army), with layers as a second axis inside it?
4. Three armies with two or three layers each is up to nine addressable slices. Should every slice be reachable in one gesture, or is two gestures (army, then layer) acceptable?

## 7. Proposed option width

Three options, one wild. Each option includes a hotkey and gesture table (bind, recall, narrow to a layer, split, merge, center camera) and a description of what the HUD tabs show for a two-axis group.

## 8. Westley confirms

Batch 1, 2026-09-22, verbatim: "When a player selects a group, and right clicks, all units should stay on their layer. If a player wants to swap the layer of a specific group or set of units, we need to give them options to manually select them. We'll offer them a variety of keybinds to do various things. Control groups, no all army hotkey"

Folded into the brief:

- Question 1: confirmed. "Army hotkeys" are the control-group hotkeys. No all-army hotkey exists.
- A right-click move on a selection keeps every unit on its current layer. Changing the layer of a group or a set of units is a deliberate act on a manual selection, never a side effect of a move.
- Questions 2 to 4 (sub-group meanings, exclusive membership as a top-level rule, one gesture versus two): left to the options. Westley wants a variety of keybinds offered; each option proposes its vocabulary for selecting a group, a layer slice of it, or a set of units, and for moving that selection between layers.

## 9. Sub-agent brief

Follow the common template in `../README.md` ("Sub-agent template"). Sections 4 and 8 of this file are the constraints; where they disagree, section 8 wins.

- Options: 3, of which 1 wild.
- A hotkey and gesture table per option: bind, recall, narrow to a layer slice, select a set inside a group, move a selection to another layer, split, merge, center the camera.
- A right-click move keeps every unit on its layer; a layer change is a deliberate act on a manual selection.
- How exclusive membership reads when a group has layer slices inside it, and what the HUD tabs show for a group spread across layers.
- The target: three armies with two or three layers each, run by one skilled player, with no select-all of any kind.

## 10. Decision (2026-09-23)

Westley, verbatim: "For control group depth, I want to combine Recall and Narrow with The Comb, recall can be the default for control groups and multi-layer movement, and comb can be the way to move individual layers within a group."

Recorded as: Recall and Narrow as the default for groups and multi-layer movement, the Comb for moving individual layers within a group (Q-105-02).
