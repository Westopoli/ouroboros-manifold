# Sidecar: client, presentation, multiplayer, eras, pipeline, hub (group 4)

Drafter: Engineer tier (Sonnet 5.5), 2026-10-02. Files written: `docs/bible/epics/E-09-chronicle.md`, `E-16-client-camera-hud-and-world-view.md`, `E-18-visual-style-and-combat-visuals.md`, `E-19-multiplayer.md`, `E-20-multi-era-and-monetization.md`, `E-21-offline-ai-pipeline.md`, `docs/bible/game_bible.md`. Story numbers used: S-230 to S-244 (S-245 unused).

## 1. Catalog rows for stories.md

| Story | Epic | Summary | Status and flags | File and anchor |
|---|---|---|---|---|
| S-230 | E-16 | "As the economy player of a pair, my screen shows resources, workers, the yield of a lot before I place, my schedule, technology and defenses, and no list of what the commander needs." | Design decided 2026-10-02, not scheduled; Q-230-01 to Q-230-03 | `epics/E-16-client-camera-hud-and-world-view.md` S-230 |
| S-231 | E-16 | "Alone, I have a dial, a doctrine switch, unit-mix switches and I ask by pointing, even from the map view." | Design decided 2026-10-02, not scheduled; Q-231-01 to Q-231-03 | `epics/E-16-client-camera-hud-and-world-view.md` S-231 |
| S-232 | E-16 | "I see my ping and my emitting forces, I am told when I am pinged and from which way, and told when a unit cannot reach a layer." | Spec'd, blocked on Q-232-01, Q-232-02 | `epics/E-16-client-camera-hud-and-world-view.md` S-232 |
| S-233 | E-16 | "I choose how the rules run my economy and whether the enemy's economy is clever." | Design decided 2026-10-02, not scheduled; Q-233-01 | `epics/E-16-client-camera-hud-and-world-view.md` S-233 |
| S-234 | E-16 | "I zoom from a single unit to the battlefield's map view in one smooth drawing, and the zoom stops there." | Spec'd, blocked on Q-234-01, Q-234-02 | `epics/E-16-client-camera-hud-and-world-view.md` S-234 |
| S-235 | E-16 | "The map shows where the economy is, weather moving across it, and the ticker tells me what happened to it." | Design decided 2026-10-02, not scheduled; Q-235-01 | `epics/E-16-client-camera-hud-and-world-view.md` S-235 |
| S-236 | E-18 | "The ground is drawn in deep detail up close and as the shape of the land far away, with no pop between." | Design decided 2026-10-02, not scheduled; land maps only; Q-236-01 (space: Q-166-02) | `epics/E-18-visual-style-and-combat-visuals.md` S-236 |
| S-237 | E-18 | "A base starts as ground under construction and rises stage by stage, spreading and thickening." | Design decided 2026-10-02, not scheduled; Q-237-01 | `epics/E-18-visual-style-and-combat-visuals.md` S-237 |
| S-238 | E-18 | "I see workers walk and gather, weather cross the map, and disguised buildings look like what they pretend to be." | Design decided 2026-10-02, not scheduled; Q-238-01, Q-238-02 | `epics/E-18-visual-style-and-combat-visuals.md` S-238 |
| S-239 | E-18 | "A ping, an emitting force and a ping alert read at a glance." | Spec'd, blocked on Q-239-01 | `epics/E-18-visual-style-and-combat-visuals.md` S-239 |
| S-240 | E-18 | "A screen of thousands of units, workers and buildings stays smooth." | Direction only; blocked on Q-240-01 (Westley's budgets) | `epics/E-18-visual-style-and-combat-visuals.md` S-240 |
| S-159 (retitled, shrunk) | E-19 | "A second player runs the economy behind my war, and we have to talk." | Design decided 2026-10-01 and 2026-10-02, not scheduled; the economy is E-22 | `epics/E-19-multiplayer.md` S-159 |
| S-241 | E-19 | "My pair is a sub-civilization in a team of 2, 4 or 6, and the map, resources and enemies grow with the team." | Design decided 2026-10-02, not scheduled; Q-241-01 to Q-241-03 | `epics/E-19-multiplayer.md` S-241 |
| S-242 | E-19 | "My building, scheduling and requests reach my partner as commands like any other." | Design decided 2026-10-02, not scheduled; Q-242-01 to Q-242-03 | `epics/E-19-multiplayer.md` S-242 |
| S-147 (retitled) | E-20 | "A space era and a land era to play, all one game." | Spec'd, blocked on Q-147-01, Q-147-02 | `epics/E-20-multi-era-and-monetization.md` S-147 |
| S-243 | E-20 | "The era pack checklist names what the economy and the landscape need." | Design decided 2026-10-02, not scheduled; Q-243-01, Q-159-08, Q-146-02, Q-146-03 | `epics/E-20-multi-era-and-monetization.md` S-243 |
| S-156 (retitled) | E-21 | "Headless fights on the real engine measure margin and break-even and flag broken rules automatically." | Spec'd, blocked on Q-156-02 (replaces Q-158-01) | `epics/E-21-offline-ai-pipeline.md` S-156 |
| S-244 | E-21 | "The names and teaching text for the economy come from the same pipeline as every other library." | Design decided 2026-10-02, not scheduled; Q-244-01, Q-244-02 | `epics/E-21-offline-ai-pipeline.md` S-244 |

Rows that need a status or pointer edit, not a new row: S-104 (add "ticker and structure panel direction changed, see S-230, S-235"), S-146 (status adds Q-146-02, Q-146-03, Q-243-01), S-149 (adds Q-149-03), S-144 (adds Q-144-03), S-161 (adds Q-234-01), S-077 and S-126, S-127 (known going in, other groups). The S-159 row's status text is now "Design decided, not scheduled", and the catalog header vocabulary question (Spec'd, Ready, Tested, Queued, Building, Built, Revised, Killed) is the architect's call.

## 2. Register rows for new flags

| Flag | Where | Question | Candidates | Status | Answer |
|---|---|---|---|---|---|
| Q-230-01 | E-16 / S-230 | Where do the economy seat's panels sit on the screen? Only what must be shown was decided. | (a) a bottom bar like the commander's with the economy panels beside it; (b) a screen of its own panels around a shared map view; (c) the layout is designed in a Design Lane pass first | open | |
| Q-230-02 | E-16 / S-230 | The commander's portrait place (R-104-08) shows the commander; what does the economy player's screen show there, since that player is not the commander? | (a) the same commander portrait; (b) the economy player's own identity; (c) nothing | open | |
| Q-230-03 | E-16 / S-104, S-230 | Where is the line between "no enemy composition readout anywhere" and the inference the economy invites (heavy gathering of one resource shows which role a side makes more of, E-22 S-171)? | (a) nothing is totalled; the player infers from the world only; (b) the seat's screen may show what it has seen of the enemy's gatherers and buildings, not totals by role; (c) other | open | |
| Q-231-01 | E-16 / S-231 | Where do the solo commander's dial, doctrine switch and unit-mix switches sit on the HUD, given the right sidebar is empty but for the layer strip (R-104-09)? | (a) the right sidebar; (b) a bar in the bottom-center beside the ability slots; (c) a panel opened by a key | open | |
| Q-231-02 | E-16 / S-231 | How does the commander override the mix the rules pick, and does the screen show that a request by pointing was taken, and what it shows when the rules cannot carry it out? | (a) a mix panel and a short acknowledgement on the ticker; (b) a marker on the map where the request stands; (c) no acknowledgement | open | |
| Q-231-03 | E-16 / S-231, hub principle 6 | Do the dial, the default-on unit-mix rules and the doctrine switch fit "positional thinking over command shortcuts"? Principle 6 is about orders to units; the dial is about spending. Auditor could not judge. | (a) they fit, since no order to a unit is issued without thinking about where units are; (b) they fit only as opt-in assistive toggles labeled as such; (c) principle 6 is amended to say so | open | |
| Q-232-01 | E-16 / S-232 | Keys and controls for the ping (a layer number and a click) and for switching a force between emitting and silent; also whether the ping and the layer-narrowing hotkey (R-105-06) share the number keys. | (a) decided with Q-103-04's camera keys; (b) ping on a held key plus 1 to 5, emit on a toggle key; (c) other | open | |
| Q-232-02 | E-16 / S-232 | Where and when do the ping alert with its 60-degree sector and the "cannot reach that layer" cue appear? The cascade brief leaves "the alert's display" out. | (a) alert at top-center with the banners, cue at the cursor on a pointed enemy; (b) alert drawn around the edge of the screen toward the ping, cue in the ability area; (c) other | open | |
| Q-233-01 | E-16 / S-233 | Where does the player choose the starting doctrine, the unit-mix behaviours and the enemy economy's foresight, and is the starting doctrine the player's pick? | (a) mission setup before each chapter; (b) Settings (R-110-02) and onboarding (E-08 S-063), changeable later; (c) at creation of the campaign or universe | open | |
| Q-234-01 | E-16 / S-161, S-234 | Is the Sand Table of S-161 the zoomed-out end of the one continuous drawing (E-17 R-166-05) or a separate drawing? | (a) the zoomed-out end of the same drawing; (b) a separate low-resolution model; (c) decided by the prototype (Q-103-05) | open | |
| Q-234-02 | E-16 / Scale | Do workers, buildings and settlement pieces count among the "1,000 units on screen" of the 60 fps budget, and what is the client budget for the long-term thousands? E-11, E-12 and E-13 budgets run to 10,000. Westley's numbers. | (a) they count; the 1,000 figure is unchanged; (b) units only; (c) Westley sets new figures (see Q-240-01) | open | |
| Q-235-01 | E-16 / S-235 | Which economy events does the ticker carry beyond base occupied, fall back to an expansion, expansion founded and weather arriving? A shipment that does not arrive must not be explained. | (a) only those four; (b) plus a forward base built or lost; (c) plus a strongpoint taken or lost | open | |
| Q-133-01 | E-18 / S-133, E-20 | How many building pieces does an era pack define for settlements, and are the 3 to 6 structures of R-133-05 and R-146-01 points of interest only? Westley's numbers. | (a) a fixed small set per era; (b) a count range like the polygon budgets; (c) set with the generator (E-17 S-166) | open | |
| Q-236-01 | E-18 / S-236, S-138 | How does a cliff or waterfall settlement read in the Settled Reach, where every unit flies, and what does the space landscape draw? | (a) not drawn in the space era until Q-166-02 is designed; (b) drawn as asteroid and open-section equivalents; (c) other | open | |
| Q-236-02 | E-18 / S-132 | Polygon budgets for workers and for the many pieces of a settlement (R-132-04 has none). Westley's numbers. | (a) as structures, 200 to 800; (b) a lower range per piece; (c) Westley sets them | open | |
| Q-237-01 | E-18 / S-237 | How many stages does a lot rise through, and what does each look like? E-17 R-166-03 fixes thresholds and "starting under construction", not the count. | (a) three, as the tiers; (b) a count per era pack; (c) set with the generator | open | |
| Q-238-01 | E-18 / S-238 | How is a disguised or hidden building drawn, to its owner and to the enemy? Follows Q-159-09. | (a) the enemy sees a decoy look, the owner sees the true building; (b) both see the true building with a cover mark for the owner; (c) decided with Q-159-09 | open | |
| Q-238-02 | E-18 / S-238 | R-159-11 says the side has no vision of its own shipment on the way. Can anyone see one (a side with vision on the lane), and how is an arrived shipment drawn? | (a) no one sees it, it simply arrives; (b) a side with vision of the lane sees it; (c) other | open | |
| Q-239-01 | E-18 / S-239 | The look of the ping burst, the emitting force and the alert sector in each era manifest. | (a) one abstract look per category in the manifest, as attacks; (b) designed per era; (c) set at the first reference pass | open | |
| Q-240-01 | E-18 / S-240, E-16 | Client budgets for thousands of units, workers and buildings on the minimum-spec machine; E-16 says 60 fps at 1,000 units, E-18 says a 30 fps floor at 1,000. Westley's numbers. | (a) Westley sets one budget for both epics; (b) keep both and add a separate one for thousands; (c) leave as a direction until the sim budgets (10,000) are reached | open | |
| Q-241-01 | E-19 / S-241 | How much more of each resource, and how many more enemies, does each added pair bring? Westley decided only the direction and the 64,000 wu canvas for 4 to 6 players. | (a) in proportion to players; (b) fixed steps at 2, 4 and 6; (c) set by the simulation's situation | open | |
| Q-241-02 | E-19 / S-241, hub | What is a sub-civilization in the rules (its own base, resources, population cap, ledger) and what is a sub-commander when the player runs the economy? Also the hub's description of who the economy player is. | (a) each pair has its own economy and the sub-commander title covers both seats; (b) pairs share one economy and the sub-civilization is a command grouping only; (c) other | open | |
| Q-241-03 | E-19 / S-241, Scale | Teams of 6 stand (DECISIONS H7) against the confirmed 4 peers. Does Westley confirm 6 peers, does 200 ms input delay hold at 6, and what is the total when opposing humans are possible (Q-141-01)? | (a) 6 peers confirmed, 200 ms unchanged; (b) 6 peers with a new latency figure; (c) per-team peers, versus counted separately | open | |
| Q-242-01 | E-19 / S-242 (R-142-04) | Does the economy player see what the commander sees? Shipments (E-22 S-176) and disguise (E-22 S-172) depend on it. | (a) one shared visible set per pair; (b) each seat sees its own units' view only; (c) shared vision with the economy seat seeing the base fully | open | |
| Q-242-02 | E-19 / S-242 | May the economy seat ever give a military order, or the commander seat a building order, in a pair? E-22 S-180 says a solo commander never places or queues. | (a) never, roles are strict; (b) the economy seat may order defenders at its base; (c) either seat may, by agreement | open | |
| Q-242-03 | E-19 / S-242, Scale | What does the economy cost per tick and per checkpoint checksum in a team of 6, and what does the tick rate halving above 1,000 live units (E-13 R-099-03) do to 3 ticks of input delay? | (a) an economy cost budget is added to the scale suite; (b) the economy is counted in the unit budget; (c) set after the first prototype | open | |
| Q-146-02 | E-20 / S-146, S-243 | Are resource names, doctrine names and environmental troubles "names" (may differ per era) or mechanics (identical per A-321 and R-146-02)? | (a) names and troubles differ, mechanics identical; (b) all identical for the two launch eras; (c) Westley decides per item | open | |
| Q-146-03 | E-20 / S-146 | What does the "elevation flag" (R-146-01, E-11: false for the Settled Reach) mean once every map has ground on all five layers (E-17 R-166-06)? | (a) retired; (b) kept for whether walking units exist; (c) other | open | |
| Q-149-03 | E-20 / S-149, hub | The base SKU was set at $10 to $15 for three eras; launch has two (space and land). Contents and price? Pricing is Westley's. | (a) two eras at a price Westley sets; (b) the same price with a third era designed; (c) other | open | |
| Q-150-02 | E-20 / S-150 | Which parts of map generation stay era-agnostic now that the land and space landscapes are sister systems with different objects? | (a) spine, edges and canvas stay shared, landscape is per era kind; (b) only the seed is shared; (c) decided with Q-166-02 | open | |
| Q-151-02 | E-20 / S-151 | The Climate of War's "reinforcement rate" is now the pace of production plus strongpoint reinforcement; which economy values may an era set? | (a) production pace only; (b) pace and resource yields; (c) none until the economy is built | open | |
| Q-243-01 | E-20 / S-243 | Are a doctrine's name, description and parameters pack content or engine config? | (a) name and description in the pack, parameters in engine config; (b) all in the pack; (c) all engine config, names only in the pack | open | |
| Q-153-02 | E-21 / S-153 | Does a mission archetype's base kind and resource slant (E-22 S-177) live in its library entry or in config (Q-153-01 says archetype prose is in code or config)? | (a) in the library entry; (b) in config; (c) decided with Q-153-01 | open | |
| Q-154-01 | E-21 / S-154 | Are workers named, and what do the "200 units" of R-154-05 count? | (a) workers are not named; (b) workers are named from the same pool; (c) workers have a separate small pool | open | |
| Q-155-02 | E-21 / S-155 | Where do the building pieces and the worker fall in the production order of R-155-02, and does an era still cost weeks, not years? | (a) after structures, before environment; (b) with structures; (c) estimated after the first pack | open | |
| Q-156-02 | E-21 / S-156 | Pass marks for the skill lab's conditions (layer_dynamics README section 4: mirror break-even tolerance, skill beating the mirror's noise, rank agreement, stacking, dominance and dead-skill shares, counters). The draft marks are unconfirmed. | (a) the draft marks as written; (b) Westley sets each; (c) report only until the marks are confirmed | open | |
| Q-244-01 | E-21 / S-244 | Are the names of resources, doctrines and building kinds generated library content or authored by hand? | (a) generated by the builder per era; (b) authored by hand in the pack; (c) a seed set by hand, varied by the builder | open | |
| Q-244-02 | E-21 / S-244 | Where does the player meet the teaching text for the economy seat and the solo commander's controls? | (a) onboarding (E-08 S-063); (b) at the paired queue; (c) in a first-use panel | open | |
| Q-068-03 | E-09 / S-068 | Do in-mission events (base occupied, retaken, fall back, expansion made) reach the time-jump log, and so the consequence slots and `chain_expansion`? Depends on Q-159-07. | (a) no, only the outcome reaches the log; (b) yes, as consequence slot content; (c) decided with Q-159-07 | open | |
| Q-070-02 | E-09 / S-070 | Who is the economy player in the chronicle, and who are the other players of a team of up to 6? R-070-03 frames lineage members as military only. | (a) the economy player is not in the lineage; (b) a lineage member in a support role, framed as military; (c) other | open | |

## 3. Flags to close, with the decision that closes each

- Q-158-01 (E-21 S-156, target band 40 to 60 percent): superseded by `docs/northstar/research/layer_dynamics/README.md` sections 4 and 11 (margin and break-even replace win rate). Replaced by Q-156-02. The epic text already says closed; the register needs the row closed.
- Q-141-01 (match shape and player count): the count part is answered by DECISIONS H7 (teams of 2, 4 and 6). The co-op or versus part stays open; the epic keeps Q-141-01 for that part only. Candidate for narrowing, not closing.
- Q-147-01 (launch eras unnamed): partly answered by DECISIONS H2 (one era in space, the Settled Reach, and one on land). The land era's name and brief remain open.
- Q-144-02 and Q-104-01 are already closed in the register; the stale mentions in the epics' open-flag lists were removed. R-104-03's bracket still names Q-104-01 (see section 4).
- Q-159-07 to Q-159-10 are no longer listed in E-19; E-22 holds them.

## 4. Needs a ledger row

Tested rules whose text is untouched, with a "Direction changed 2026-10-02, rewrite pending" line under the story heading (citations found by grep over tests/, csrc/ and scripts/):

- R-104-01 (E-16 S-104): cited by `tests/test_tactical_hud.gd`, `tests/csim/test_E15_S127_taking_a_garrison.py`, `csrc/tactical_support.c`. The ticker will also carry economy events (E-16 S-235).
- R-104-06 (E-16 S-104): cited by `tests/csim/test_E15_S126_most_of_my_force_is_out_there.py`. The structure panel's production timers move to the economy seat's schedule (S-230, E-22 S-170) and the structures become strongpoints (E-15).
- R-139-03 (E-19 S-139): cited by `tests/qa/t1/desync.py` and `tests/qa/t1/test_desync_detector.py`. The checksum must also cover the economy's state (new R-139-06, which is not yet tested).
- R-146-01 (E-20 S-146): cited by `scripts/specfactory/pack_validate.py`. A pack also carries the economy and landscape entries of S-243; the "3 to 6 tiered structures" and the "reinforcement constants" change meaning.
- R-146-02 (E-20 S-146): cited by `tests/specfactory/test_pack_validate.py` and `scripts/specfactory/pack_validate.py`. Says "three launch eras"; the launch has two (S-147). Names versus mechanics is Q-146-02.

Tested rules left alone with no note line (the text still holds, and nothing in the decisions contradicts it): R-103-02 (`tests/test_tactical_camera.gd` and others), R-104-04 (`tests/test_tactical_hud.gd`), R-110-02 (settings tests), R-070-03, R-065-02, R-068-03, R-067-04, R-069-01 (E-09 tests). R-104-03 (pause or menu button) is cited by `tests/test_tactical_hud.gd` and its text still carries the closed Q-104-01 bracket; it was left untouched under the policy, and its Open flags line says the flag is closed. Single-player pause allowed, multiplayer never: a ledger row could rewrite it when the HUD tests are revised.

No test or code cites a lockstep peer limit, so the "4 peers" Scale requirement of E-19 was rewritten (6 peers, Q-241-03), not noted.

## 5. Findings resolved

### E-16
- Purpose, bottom-bar HUD with economy chrome removed: done (Purpose rewritten, S-230).
- Purpose, "a minimap": done (Purpose now says the map view in place of a minimap).
- No story for the economy seat's screen: done (S-230); layout flagged Q-230-01.
- Solo commander's dial, doctrine, asking by pointing: done (S-231; pointer in R-104-09); layout flagged Q-231-01, Q-231-02.
- R-161-02 contradicts pointing from the map: done (rewritten).
- R-104-01 ticker contradicts economy events: done as direction note under S-104 (rule is tested) plus S-235 R-235-03; flagged Q-235-01.
- Ping alert and 60-degree sector: done (S-232 R-232-04); placement flagged Q-232-02.
- Emit mark in R-104-10: done (added to R-104-10, S-232 R-232-03).
- Ping and emit controls and cooldown: done (S-232 R-232-01, R-232-02); keys flagged Q-232-01.
- R-105-06 against R-162-01 (number keys): flagged (Q-232-01, pointer in S-105 Open flags).
- Reach cue by unit type: done (S-232 R-232-05); flagged Q-232-02.
- Map view contents (R-104-05): done (rewritten with pointer, S-235 R-235-01, R-235-02).
- R-104-06 structure panel: done as direction note (tested), S-230, S-235.
- R-104-10 and the no-readout invariant: flagged (Q-230-03), pointer added in R-104-10 and Invariants.
- R-104-08 commander portrait: done (rewritten with flag Q-230-02).
- Settings and onboarding choices (R-110-02, S-109): done as new story S-233; R-110-02 left (tested); flagged Q-233-01.
- Zoom limits and S-108 pull-back: done (S-234, pointer in R-108-01); R-103-02 left (tested), restated as R-234-04.
- Sand Table as the zoomed-out drawing: flagged (Q-234-01), pointer in R-161-05.
- Scale requirements at 1,000 units: flagged (Q-234-02, Q-240-01); numbers not changed.
- R-104-03 pause (noticed): left (tested); Open flags line says Q-104-01 is closed; hub fixed.
- Inputs and P4: done (Inputs row for live map content).
- Depends on E-19 and E-22 and E-17: done.

### E-18
- Self-built settlements and construction stages: done (S-237); flagged Q-237-01.
- World, terrain and landform at continuous detail: done (S-236), land maps only; space flagged Q-236-01 (Q-166-02).
- LOD only for attacks and wrecks: done (S-240 R-240-01).
- Scale requirements, 30 fps against E-16's 60 fps: flagged (Q-240-01); numbers not changed.
- R-132-04 polygon budgets: done (R-132-06 added; budget flagged Q-236-02).
- R-133-05 pack structure count: done (rewritten; building pieces counted separately, flagged Q-133-01). The auditor could not tell whether "3 to 6 point-of-interest structures" meant objectives only; the rule now says they are points of interest and the settlement pieces are not counted among them.
- R-138-03 frontier look and cliff reading: flagged (Q-236-01).
- Layer action visuals: done (S-239); looks flagged Q-239-01.
- Workers, shipments, weather, disguise: done (S-238); flagged Q-238-01, Q-238-02. Note: R-159-11 says the side itself has no vision of its shipment; the audit read it as "unseen by the enemy". The rule follows the decision text.
- Depends on: done.

### E-19
- Gate table counts and verdict: done.
- Open flag lists (Q-144-02): done.
- R-159-01 against S-141 and 4 peers: done (R-141-01 rewritten with teams of 2, 4, 6; Scale rewritten to 6 peers; Q-241-03).
- R-141-01, R-141-02 and co-op or versus: done (pointers added; Q-141-01 stays for shape).
- R-139-03 checksum scope: done as direction note (tested) plus new R-139-06.
- Command set on the wire: done (S-242 R-242-01 to R-242-03, Inputs row); flagged Q-242-02.
- Scale requirements: done (Scale rewritten, Q-241-03, Q-242-03).
- Fog and the pair: flagged (R-142-04, Q-242-01).
- R-140-04 drop-out: done (rewritten per seat; commander and other peers stay on Q-140-02).
- R-144-03 universe lock for the switches: done.
- R-144-02 lobby roles: done.
- R-143-03 and R-144-03: done (pointer in R-143-03).
- S-159 placement and home: done (S-159 shrunk to the paired mode, E-22 holds the economy; the flag on the home is resolved).
- R-159-13 and flags: done (Q-159-07 to Q-159-10 now E-22's; E-09 row below).
- Hub decisions with no home: team sizes, sub-commanders, sub-civilizations, 64,000 wu: done (S-241).

### E-20
- R-146-01 structures, resource names, doctrines, landforms, troubles, workers, movement kind, elevation flag, reinforcement constants: done as direction note (tested) plus S-243; flagged Q-243-01, Q-159-08, Q-146-03, Q-151-02, Q-133-01.
- R-150-03 workers: done (rewritten).
- R-146-02 and the Invariants: flagged (Q-146-02); invariant rewritten for two eras and "essentially the same".
- R-146-04: done (rewritten to add resources and building kinds).
- R-150-04: done (rewritten).
- R-150-01 and Depends on layouts: done (flagged Q-150-02).
- R-147-03: done (rewritten, landscape differs).
- Three-era launch text (Purpose, S-147, R-149-01, Invariants, hub Monetization): done, conflict flagged Q-149-03; pricing not settled.
- S-151 reinforcement rate: done (R-151-01, Q-151-02).

### E-21
- R-156-01, R-156-02, Q-158-01 (win-rate matrix): done (margin and break-even with units firing; marks flagged Q-156-02).
- R-153-01 archetype entries and base kind: done (rewritten), flagged Q-153-02.
- Behavior scripts and layout hints pointer: done (Open flags of S-153).
- Doctrine, resource and building names, economy-seat tutorial text: done (S-244), flagged Q-244-01, Q-244-02.
- R-154-05 pools (workers named): flagged (Q-154-01).
- Asset pipeline for building pieces and workers: done (R-155-05), flagged Q-155-02.

### E-09
- Economy seat's character in the chronicle: flagged (Q-070-02, S-070 Open flags).
- In-mission economy events and slots: flagged (Q-068-03).
- R-065-02 partial failure: done (pointer in S-065 Open flags; nothing to change).
- R-069-01 "map view": done (pointer in S-069 Open flags).
- Set L: checked, none.

### Hub
- Toolkit, fifth-of-force paragraph: done (rewritten; the missing full stop is fixed).
- Toolkit, dated callout and the solo commander's hand: done (dates and "not yet scheduled" removed; dial, doctrine, pointing, unit mix override, enemy economy choice, strongpoints added).
- Game Shape at a Glance: done (tactical bullet, orders paragraph, pause sentence).
- Vision, line 49 "two zoom levels": done.
- Vision, lines 22, 48, 123 and the economy seat's identity: done for line 48 only; line 22 and the litmus line left as they stand; the economy seat's identity flagged Q-241-02.
- Sacred principle 4: done (one sentence on the seat's skill and the economy).
- Sacred principle 6: flagged (Q-231-03); hub text unchanged.
- Onboarding: done (pointer, Q-233-01).
- Monetization: done (flag Q-149-03; production pace in place of reinforcement).
- Reference Hardware: done (pointer, Q-240-01).
- The Systems: done (E-22 added; S-159 and S-166 pointers).
- Pause (noticed): done.
- What's Unique: done (item 8).

### Catalog rows
Not edited (not my file); the rows are listed in section 1. The findings on S-006, S-126, S-127, S-077, S-112, S-116, S-120, S-121, S-125, S-128 belong to other groups.

## 6. Could not do

- R-104-03 (pause) and the other tested rules in section 4 keep old text, as the brief requires.
- No layout, key, number or look was invented; each is a flag above.
- Hub principle 6 and the hub's "commander, not king" lines are not edited; Q-231-03 and Q-241-02 stand for the architect.
- `docs/bible/stories.md`, the register and E-22 were not touched, so every "E-22 S-###" citation assumes the E-22 numbering in the brief's table.
- I could not find where E-15 holds weather and strongpoints in final form (another group's file); citations to "E-15" are by epic only.
