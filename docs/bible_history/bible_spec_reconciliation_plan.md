# Bible–Spec Reconciliation Plan

> **Purpose:** This document is a task plan for Claude Code. Each phase is a self-contained unit of work with mandatory checkpoints. Phases are ordered by dependency — later phases depend on earlier ones. Do NOT skip phases or reorder them.
>
> **Working philosophy:** Isolate and confirm root cause before prescribing fixes. Baby-step checkpoints with mandatory stop-and-show-output discipline. Every fix must be tested against both its own correctness AND regression against all previously passing invariants.
>
> **Bible references are authoritative.** When this plan references a bible section, read the actual bible file — don't rely on summaries here.

---

## Dependency Map

```
Phase 1: Entrenchment verification (standalone — may already be implemented)
Phase 2: Typed adjacency graph (foundational — touches region model, all propagation queries)
Phase 3: Nemesis detection (depends on coherence ledger, event log — both exist)
Phase 4: Lineage selection algorithm (depends on Phase 3 for nemesis pool)
Phase 5: Commander death lineage decision (depends on Phase 4)
Phase 6: Cross-faction lineage rotation (depends on Phase 4)
Phase 7: Mission-adjacent features (refusal, inheritance, complications, time limits) — depends on Phase 4 for lineage queries
Phase 8: Bible documentation updates (recon phase → Stage 8, onboarding → Stage 8, edge type propagation note)
```

---

## Phase 1 — Entrenchment Verification

**What:** The bible defines an entrenchment system at `bible_simulation.md` line 381: regions gain a defense multiplier based on tenure, ramping from base to capped max, resetting on conquest. The attack resolution formula (`effective_defense = defender_military * resistance_factor * tech_defense_mult * entrenchment`) uses it. No stage spec mentions entrenchment. Determine whether it's implemented, and if so, whether correctly.

**Bible references:**
- `bible_simulation.md`: "Entrenchment — tenure-based defense bonus" (line 381)
- `bible_simulation.md`: Attack event resolution formula (line 344–345)

### Step 1A — Audit

Search the codebase for any entrenchment implementation:
- Search for `entrench` in all `.py` files
- Check `config.py` for entrenchment config values (base value, max value, ramp ticks)
- Check the attack resolution code path for the entrenchment multiplier
- Check region data model for a `ticks_held` or equivalent field

**Print:** Whether entrenchment exists in code, where it lives, and whether it matches the bible spec (ramps from base to max over configurable ticks, resets on conquest/colonization).

**🛑 CHECKPOINT 1A — Stop. Show findings. If entrenchment is missing, proceed to 1B. If it exists and is correct, skip to Phase 2. If it exists but is wrong, show the discrepancy and wait for direction.**

### Step 1B — Implement (only if missing)

Add entrenchment to the simulation:
- Add `faction_since_tick` field to region data (or equivalent — the tick when the current faction took ownership). Set on conquest, colonization, and world generation.
- Add entrenchment config values: `ENTRENCHMENT_BASE` (e.g., 1.0), `ENTRENCHMENT_MAX` (e.g., 1.5), `ENTRENCHMENT_RAMP_TICKS` (e.g., 200).
- Compute entrenchment multiplier: `entrenchment = min(ENTRENCHMENT_MAX, ENTRENCHMENT_BASE + (ENTRENCHMENT_MAX - ENTRENCHMENT_BASE) * min(1.0, ticks_held / ENTRENCHMENT_RAMP_TICKS))`
- Wire into attack resolution formula.
- Reset `faction_since_tick` on conquest and colonization events.

**Test:**
- Run scenario `07_lifecycle_4faction` for 500 ticks. Print 5 sample attack resolutions showing the entrenchment multiplier value for the defending region. Verify: newly conquered regions have base entrenchment, long-held home regions have max entrenchment.
- Run all existing invariants (A through current). Confirm no regressions.

**🛑 CHECKPOINT 1B — Stop. Show attack resolution samples and invariant results.**

---

## Phase 2 — Typed Adjacency Graph

**What:** The bible specifies three edge types (border, trade_route, both) on the inter-region adjacency graph. Different game systems propagate through different edge types. Currently all edges are untyped ("both"). This phase adds edge types and wires existing systems to query by type.

**This is foundational.** It touches the region graph, all adjacency queries, border friction, faction agent targeting, adjacency bonus, and potentially event propagation. Extreme care required.

**Bible references:**
- `bible_world.md`: "Inter-Region Topology — Typed Adjacency Graph" (full section)

### Step 2A — Audit Current Adjacency Usage

Before changing anything, catalog every place in the codebase that queries adjacency:
- Border friction calculation
- Faction agent targeting (attack candidates, colonization candidates)
- Adjacency bonus (economy drift)
- Event propagation (chain spawns to adjacent regions)
- Attractiveness scoring (strategic position — neighbors)
- Coherence ledger queries ("nearby region" for character selector)
- Any other `get_neighbors()` or `adjacent_regions` calls

**Print:** A complete list of every adjacency query call site, what it's used for, and which edge type it should use per the bible (border = military propagation, trade_route = economic propagation, both = full propagation).

**🛑 CHECKPOINT 2A — Stop. Show the adjacency audit. Wait for Westley to confirm the edge type assignments before proceeding.**

### Step 2B — Add Edge Types to Graph Model (Data Structure Only)

- Modify the region adjacency data structure to support typed edges. Each edge carries a `type` field: `"border"`, `"trade"`, or `"both"`.
- Default all existing edges to `"both"` — this is a zero-change-in-behavior migration. Nothing should behave differently after this step. Templates will be updated to use real types in Step 2D.
- Add helper query methods: `get_neighbors(region_id, edge_type=None)` where `None` returns all neighbors (backward compatible), `"border"` returns border+both neighbors, `"trade"` returns trade+both neighbors.

**Test:**
- Run all existing invariants. Every single one must pass identically — this step changes data structure, not behavior.
- Print: the adjacency graph for the `isolated_start` template showing edge types (all "both" at this point).

**🛑 CHECKPOINT 2B — Stop. Show invariant results. Confirm zero regressions. The critical property: behavior is IDENTICAL to before this change.**

### Step 2C — Wire Systems to Query by Edge Type

Using the audit from 2A and the confirmed type assignments, update each adjacency query call site to pass the appropriate edge type:
- Border friction → `edge_type="border"`
- Military-related faction agent queries (attack candidates, reinforcement) → `edge_type="border"`
- Economy adjacency bonus → `edge_type="trade"`
- Colonization candidates → `edge_type="border"` (you colonize through military access)
- Event propagation → depends on event type (military events through border, economic events through trade, most through both)
- Character selector "nearby region" → `edge_type=None` (any connection counts for narrative proximity)

**CRITICAL: Because all edges are currently "both", the edge_type filter should return the same results as no filter.** This step should again produce zero behavior change.

**Test:**
- Run all existing invariants. Every single one must pass identically.
- Add a targeted test: temporarily create a test world with one mixed-type edge (a trade-only route between two regions). Verify that border friction does NOT propagate across it, but economy adjacency bonus DOES. Then remove the test world.

**🛑 CHECKPOINT 2C — Stop. Show invariant results AND the mixed-edge test. Confirm the type filtering works correctly.**

### Step 2D — Update Templates: All Edges Default to "border"

**Design decision (confirmed by Westley):** All inter-region edges in world generation templates start as `"border"` only. Regions can see each other militarily (border friction, attacks, military adjacency) but do NOT share economic benefits (no adjacency bonus, no trade) by default. Trade routes are established through diplomatic cooperation (Step 2E), not baked into the starting map.

**What this means mechanically:**
- At game start, factions do not get economy adjacency bonus from *any* neighbor — including their own frontier regions. Trade is earned through peace, not granted by proximity.
- Border friction still applies at cross-faction borders (border edges carry military effects).
- Colonization still works (military access through border edges).
- The economy adjacency bonus becomes a meaningful diplomatic reward rather than a passive geographic advantage.

**WARNING — This is a significant behavioral change.** Economy growth in early game will be slower because the adjacency bonus doesn't fire until cooperative relationships form. This may require retuning economy drift rates, budget growth, or the adjacency bonus magnitude to compensate. Expect some invariants to shift.

**Implementation:**
- Update all world generation templates: every edge becomes `"border"`.
- Same-faction edges between a faction's own starting regions (e.g., home ↔ frontier within the player's starting territory) also start as `"border"` — trade within your own territory is established through the cooperative trade mechanic in 2E, or we add an exception here. **Proposal:** edges between regions owned by the SAME faction at world generation start as `"both"` (you trade within your own territory from day one). Only cross-faction and uninhabited-region edges start as `"border"`. **Print this proposal and wait for confirmation before applying.**

**Test:**
- Run all existing invariants. Print which invariants shift or break. For each regression, diagnose whether it's an expected consequence of the adjacency bonus being gated behind diplomacy, or a genuine bug.
- Print: economy growth comparison — run 200 ticks with old "both" edges vs. new "border" edges. Show the delta in average faction economy.

**🛑 CHECKPOINT 2D — Stop. Show the same-faction edge proposal, invariant results, and economy comparison. Wait for Westley to confirm the proposal and evaluate whether retuning is needed before proceeding.**

### Step 2E — Cooperative Trade Route Formation

The bible says cooperative diplomatic relationships include "adjacency bonus sharing" and "border friction removal." With typed edges, cooperative peace upgrades shared border edges to "both" (adding trade), and betrayal/war downgrades them back to "border" (removing trade).

**Implementation:**
- When two factions enter cooperative state: all shared border-type edges between the two factions upgrade to `"both"`
- When cooperative state breaks (betrayal, war declaration): shared edges between those factions downgrade to `"border"`
- When a faction colonizes an uninhabited region: the new edge between the colony and any same-faction neighbor is created as `"both"` (you trade with your own territory immediately)
- When a region is conquered: the edge between the conquered region and the conquering faction's existing territory becomes `"both"` (the conqueror integrates the region economically). Edges between the conquered region and the *former* owner's territory downgrade to `"border"` (trade severed by conquest).

**Test:**
- Run a scenario where two factions form cooperative peace. Verify: shared edges become "both", economy adjacency bonus flows across the border. Then trigger a betrayal. Verify: edges downgrade to "border", economy bonus stops.
- Run a colonization scenario. Verify: new colony-to-parent edge is "both".
- Run a conquest scenario. Verify: conquered region trades with new owner, not old owner.
- Run all invariants. Check specifically that diplomacy invariants still pass. Economy growth should now be closer to pre-Phase-2D levels because cooperative factions regain the adjacency bonus.

**🛑 CHECKPOINT 2E — Stop. Show diplomacy, colonization, and conquest edge tests, plus full invariant suite.**

---

## Phase 3 — Nemesis Detection

**What:** The bible defines nemesis detection as a query-time scan of the event log for named characters on opposing sides of combat events. This feeds the character selector's Priority 2 pool. Currently unimplemented.

**Bible references:**
- `bible_simulation.md`: "Nemesis detection" under Coherence Ledger (line 559)
- `game_bible.md`: Character Selector Algorithm, Step 2, Priority 2 (~20% pool)

### Step 3A — Implement Nemesis Detection Query

Add to `coherence_ledger.py`:
- New query: `get_nemesis_candidates(lineage_id) → list[character_id]`
- Logic: Scan the event log for combat-related events (attacks, conquests, defense events) where a character from the given lineage AND a character from a different faction both appear as attached characters. Characters who appear on opposing sides of 2+ such events are nemesis candidates. The threshold (minimum shared combat events) is a config value.
- Return: list of nemesis character IDs, sorted by number of opposing combat events (strongest rivalry first)

**Also add:** `get_nemesis_descendants_in_region(nemesis_ids, region_id, hop_range) → list[character_id]` — given a list of nemesis characters, find their descendants (via parent_character_id links in ledger) who are alive and within `hop_range` adjacency hops of `region_id`.

**Test:**
- Set up a mock scenario: create two lineages, attach characters from each to opposing sides of 3 combat events in the event log. Run `get_nemesis_candidates()`. Verify the opposing character is returned.
- Create descendants for the nemesis character in a specific region. Run `get_nemesis_descendants_in_region()`. Verify the descendants are found.
- Run all existing invariants. Confirm no regressions (this is a new query, shouldn't affect existing behavior).

**🛑 CHECKPOINT 3A — Stop. Show nemesis detection test output and invariant results.**

---

## Phase 4 — Lineage Selection Algorithm

**What:** The character selector's Step 2 (lineage selection on rotation) is defined in the bible but not implemented in any spec. Stage 4's `generational.py` has the rotation *decision* (stay/rotate) but uses placeholder character IDs. Stage 5 wires real names. No spec implements the three-pool weighted draw or within-pool scoring.

**Bible references:**
- `game_bible.md`: "Character Selector Algorithm" — Step 2: Lineage selection (full section, lines 138–146)
- `game_bible.md`: Step 3: Lineage member generation during time jumps (line 148)

### Step 4A — Audit Current Implementation

Read `generational.py` to understand what currently exists:
- Does it have pool selection logic (70/20/10 weights)?
- Does it have within-pool scoring (recency penalty, descendant count, chapter gap)?
- Does it just pick a random character ID?
- What does it do when rotation fires?

**Print:** Current rotation handler code, annotated with what matches the bible and what doesn't.

**🛑 CHECKPOINT 4A — Stop. Show audit results.**

### Step 4B — Implement Three-Pool Selection

Add to `generational.py` (or a new `character_selector.py` if cleaner):

**Pool selection:**
- Config weights: `LINEAGE_POOL_WEIGHTS = {"previous_descendant": 0.70, "nemesis_descendant": 0.20, "unrelated": 0.10}`
- Roll against weights to select a pool
- If selected pool has no valid candidates, fall through to next pool in priority order (previous → nemesis → unrelated)

**Priority 1 — Previous lineage descendant (selected pool):**
- Query coherence ledger for all previous lineages the player has played
- For each, check if living descendants exist in or near the mission region (use `hop_range` config, default 2)
- Score qualifying candidates by: recency penalty (don't immediately return to a lineage just left — penalize lineages played in the last 2 chapters), number of living descendants in the region, and how many chapters ago the player last played them (moderate gap preferred)
- Weighted random draw from scored candidates

**Priority 2 — Nemesis descendant (selected pool):**
- Call `get_nemesis_candidates()` from Phase 3
- For each nemesis, call `get_nemesis_descendants_in_region()` near the mission region
- If any exist, select from this pool (random or scored by rivalry strength)

**Priority 3 — Unrelated person:**
- Generate a new character in the mission region via the coherence ledger
- This signals the world has changed dramatically

**Integration:** Wire this into the existing rotation flow in `generational.py`. The mission generator has already selected the mission region — the character selector receives that region as input.

**Test:**
- Set up a mock game state with 3 previous lineages, each with descendants in various regions. Set up one nemesis relationship. Run the selector 100 times from the same state with different seeds.
- Print: pool selection distribution (should approximate 70/20/10), within-pool candidate scores, final selections.
- Verify: previous lineage descendants are selected ~70% of the time, nemesis descendants ~20%, unrelated ~10%. If the nemesis pool is empty, those rolls fall through to previous descendants (should see ~90/0/10 in that case).
- Run all existing invariants.

**🛑 CHECKPOINT 4B — Stop. Show selection distribution, candidate scores, and invariant results.**

---

## Phase 5 — Commander Death Lineage Decision

**What:** The bible says commander death "forces an early lineage decision." Currently, `outcome_resolver.py` logs the death but no spec defines what happens to the lineage rotation. The implementation must also respect the bible's minimum lineage chapter target (soft target 2–4, config `LINEAGE_MIN_CHAPTERS`).

**Design decision (confirmed by Westley):** A lineage is guaranteed a minimum of 3–4 missions before rotation can occur for any reason, including commander death. If a commander dies and the lineage is below the minimum chapter count, the system MUST find a successor within the same lineage — expanding search to the entire world if necessary. Rotation on death only happens if the bloodline is literally extinct (zero living members anywhere).

**Bible references:**
- `game_bible.md`: "The Cycle" step 4 — "Death forces an early lineage decision: the character selector either continues through another family member or rotates to a new lineage."
- `game_bible.md`: "The Generational Structure" — lineage persistence for 2–4 chapters (soft target)

### Step 5A — Implement Commander Death Handling

When `MissionResult.commander_survived == False`, the outcome resolver already marks the commander dead in the ledger. After that, the generational controller runs the following decision:

**Case 1: Lineage chapter count < `LINEAGE_MIN_CHAPTERS` (set to 3 or 4).**
- The lineage is below the guaranteed minimum. A successor MUST be found.
- Search order: (a) living lineage members in the mission region, (b) living lineage members in adjacent regions (any edge type), (c) living lineage members ANYWHERE in the world.
- If any living lineage member exists at any search radius, promote them to commander. The lineage continues. Log the succession as a special event in the event log ("Command passed to [name], [relation] of the fallen [dead commander name]").
- If the bloodline is completely extinct (zero living members anywhere): forced rotation. Run the Phase 4 lineage selection algorithm. This is the only way rotation happens below the minimum.

**Case 2: Lineage chapter count >= `LINEAGE_MIN_CHAPTERS`.**
- The lineage has served its minimum. The system has more flexibility.
- First, check if living lineage members exist in or near the mission region (same search as Case 1, steps a and b only — do NOT search the entire world).
- If a nearby successor exists: continue the lineage with that successor. The story isn't done if family is still local.
- If no nearby successor: force rotation. Run the Phase 4 lineage selection algorithm. The family is too dispersed to continue commanding here — the world has moved on.

**Config values:**
- `LINEAGE_MIN_CHAPTERS = 3` (update from current value of 2 — Westley wants 3–4 guaranteed missions per lineage)
- The existing `LINEAGE_HARD_CAP = 6` is unchanged.

**Integration:** Wire this into the generational controller's post-mission flow, after the outcome resolver runs but before the next time jump.

**Test:**
- Mock scenario 1: Commander dies on chapter 1 of a lineage. Lineage has a living descendant in a distant region (not adjacent to mission region). Verify: descendant is promoted (global search used because below minimum). Lineage continues. Chapter counter increments.
- Mock scenario 2: Commander dies on chapter 1. Lineage has ZERO living members. Verify: forced rotation fires, Phase 4 pool selection runs.
- Mock scenario 3: Commander dies on chapter 4 (above minimum). No lineage members nearby, but one exists far away. Verify: rotation fires (above minimum, no nearby heir = rotate). The distant family member is NOT promoted.
- Mock scenario 4: Commander dies on chapter 4. Lineage member exists in adjacent region. Verify: successor promoted (above minimum, but nearby heir = continue).
- Mock scenario 5: Commander survives. Verify: no change to existing behavior.
- Run all existing invariants. Specifically verify that J14 (player faction collapse triggers reassignment) still passes — commander death is a different path than faction collapse.

**🛑 CHECKPOINT 5A — Stop. Show all five scenario results and full invariant suite.**

---

## Phase 6 — Cross-Faction Lineage Rotation

**What:** After the hard cap (~6 chapters), the character selector should consider candidates across ALL factions, not just the player's current one. Stage 4 lists this as a bullet point but doesn't define the scoring. The faction is NOT chosen directly — it falls out of mission selection.

**The exact sequence (do not deviate):**
1. The lineage chapter counter hits the hard cap. Rotation is forced.
2. The **mission generator** expands its candidate pool: instead of scanning only player-faction regions and adjacent contested regions, it scans ALL factions' regions against all 10 archetype triggers. Urgency scoring, relevance scoring, and preference scoring work identically — the only change is the pool is wider.
3. The mission generator selects the winning (region, archetype) pair through the normal weighted random draw from top N candidates. The region may belong to any faction.
4. The **character selector** (Phase 4 algorithm) runs against the selected region. It searches for previous lineage descendants, nemesis descendants, or generates an unrelated person — same three-pool logic. The selected character may belong to whatever faction owns the mission region.
5. The **generational controller** reassigns the player to the selected character's faction. The player's new faction is whichever faction owns the region the mission generator picked. This is NOT a separate faction-scoring step — the faction is a consequence of which mission won the scoring.
6. Log the faction transition as a special event. The chronicle frames this naturally: "Three decades after [previous commander]'s final campaign, command authority was extended to [new commander], an officer of [new faction]..."

**Why this works:** The relevance score in the mission generator already considers lineage connections. If a previous lineage's descendants are thriving in faction B's territory near a crisis, that (region, archetype) pair gets a high relevance boost AND a high urgency boost. The faction selection is emergent from "what's the most interesting and connected mission in the entire world right now?" — which is exactly the bible's intent.

**Bible references:**
- `game_bible.md`: "Cross-faction lineage rotation" (line 175)
- `game_bible.md`: Character Selector Algorithm — "the selector is coupled to the mission generator — the mission region is already decided" (line 124)

### Step 6A — Expand Mission Generator Candidate Pool at Hard Cap

Modify the mission generator to accept a `cross_faction=True` parameter:
- When `cross_faction=False` (default, normal behavior): scan player-faction regions and adjacent contested regions only.
- When `cross_faction=True` (triggered at hard cap): scan ALL owned regions for ALL factions against all archetype triggers.

The generational controller passes `cross_faction=True` when `lineage_chapter_count >= LINEAGE_HARD_CAP`.

**CRITICAL: Do not change the scoring formula.** Urgency, relevance, and preference work identically. The only change is which regions enter the candidate pool. Do not add faction-preference scoring, faction-quality weighting, or any other new scoring term. The existing formula handles cross-faction selection naturally through relevance (lineage connections to regions in other factions) and urgency (crises in other factions are just as urgent).

### Step 6B — Wire Faction Reassignment

After the character selector picks a commander from the winning mission's region:
- If the selected character's faction differs from the player's current faction:
  - Update the generational controller's `player_faction_id` to the new faction
  - Log a faction transition event in the event log with `mission_consequence=False` (this is a structural transition, not a mission consequence)
  - The coherence ledger tracks the lineage's faction history (which factions the player has served)
- If the selected character's faction is the same as the player's current faction: no special handling needed (the hard cap rotation picked a new lineage within the same faction, which is valid)

### Step 6C — Test

- Mock scenario: Player has been with faction A for 6 chapters (hard cap). Set up the following world state:
  - Faction B has a crisis region (urgency 0.85) where a descendant of a previous player lineage lives
  - Faction C has a moderate-pressure region (urgency 0.5) where a nemesis descendant lives
  - Faction A has a calm region (urgency 0.3) with no lineage connections
- Run the mission generator with `cross_faction=True` 50 times with different seeds.
- **Print:**
  - Distribution of selected factions across the 50 runs (expect faction B to win most often due to high urgency + lineage relevance)
  - The full scoring breakdown for the top 3 candidates in one representative run (show urgency, relevance, preference, total for each)
  - Confirmation that the generational controller's faction assignment updated when a cross-faction mission was selected
  - The event log entry for the faction transition
- Run all existing invariants. Specifically check:
  - J14 (player faction collapse triggers reassignment) still works — this is a DIFFERENT reassignment path
  - M1 (every mission responds to real simulation condition) still passes — cross-faction missions must still respond to real triggers
  - M2 (urgency dominates in crisis) still passes across the wider pool

**🛑 CHECKPOINT 6 — Stop. Show faction distribution, scoring breakdown, faction transition event, and full invariant suite.**

---

## Phase 7 — Mission-Adjacent Features

These are smaller features that depend on the mission pipeline (Stage 5.5) and the lineage system (Phases 4–6). They can be implemented in any order within this phase.

### Step 7A — Mission Refusal

**Bible reference:** `bible_missions.md` — "Mission Briefing": player can refuse, treated as failed mission with its own consequence bundle.

**Implementation:**
- Add a `MISSION_REFUSAL` outcome band to the outcome resolver — treated as a specific consequence table entry per archetype. Consequence should be similar to `partial_failure` but with a tension penalty (the civilization sent you and you said no) and no military loss (no battle happened).
- Add `refusal` as a valid `MissionResult.outcome_band` value in `mission_contracts.py`.
- The generational controller checks for refusal before invoking the tactical engine — if the player refuses, skip tactical execution and go directly to the outcome resolver with the refusal band.
- Config: `REFUSAL_TENSION_PENALTY_PCT = 8` (tension +8% of deficit — the civilization's trust in the commander erodes)

**Test:**
- Mock a refusal for Defensive Stand. Compare consequence deltas to partial_failure. Verify: no military change (no battle), tension increase present, economy unchanged.
- Run all invariants.

**🛑 CHECKPOINT 7A — Stop. Show refusal consequence comparison.**

### Step 7B — Inheritance Missions (Narrative Modifier)

**Bible reference:** `bible_missions.md`: "Inheritance missions are not a separate archetype — they are a rare narrative modifier."

**Implementation:**
- After the mission generator selects a (region, archetype) pair and fills variables (Step 4), add a post-processing check:
  - Query the coherence ledger: has any previous lineage commander operated in this region? Was this region previously lost by the player's lineage (check event log for conquest events where the region was player-held and a lineage member was stationed there)?
  - If yes: set an `inheritance_flag` on the `MissionSetup.metadata` dict with the ancestor's name and the relevant historical event.
  - The briefing builder reads this flag and includes an inheritance framing line in the situation section.
- This is purely a narrative addition — no mechanical change to the mission.

**Test:**
- Set up a scenario where a region was conquered away from the player 500 ticks ago while a lineage member was stationed there. Generate a Reconquest mission targeting that region. Verify: `inheritance_flag` is set with the ancestor's name.
- Generate a mission for a region with no lineage history. Verify: no flag.

**🛑 CHECKPOINT 7B — Stop. Show inheritance detection results.**

### Step 7C — Per-Archetype Mission Time Limits

**Bible reference:** `bible_missions.md` — each archetype has time constraints in its objective shape. `MissionSetup.time_limit_ticks` exists but no spec defines how it's determined.

**Implementation:**
- Add per-archetype base time limit config values: `ARCHETYPE_TIME_LIMITS = {"defensive_stand": 3600, "siege_breaking": 5400, ...}` (in tactical ticks at 20/sec — e.g., 3600 = 3 minutes)
- The mission generator fills `time_limit_ticks` from the archetype config, with a simulation modifier: regions under more pressure get shorter time limits (urgency score scales the limit down by up to 20%).
- Formula: `time_limit = base_time * (1.0 - urgency * TIME_PRESSURE_SCALING)` where `TIME_PRESSURE_SCALING` is a config value (default 0.2).

**Write to bible:** Add a note in `bible_missions.md` under each archetype's section indicating the base time limit and scaling behavior. This ensures the bible captures the design decision.

**Test:**
- Generate missions for the same archetype at different urgency levels. Verify: higher urgency produces shorter time limits. Verify: the time limit never drops below a minimum floor (config value, e.g., 60% of base).

**🛑 CHECKPOINT 7C — Stop. Show time limit scaling results.**

### Step 7D — Complications Ownership

**Bible reference:** `bible_missions.md` — "Complications (Deferred)": mid-mission pre-computed disruptions.

**This is not an implementation task.** The bible correctly defers complications. The gap is that no stage claims ownership. 

**Action:** Add a note to the Stage 7 spec (or Stage 8 spec if Stage 7 is finalized) that complications are owned by that stage. Write a brief section header: "Complications System (from bible_missions.md) — to be implemented after core missions work end-to-end, as specified in the bible."

Also add to `bible_missions.md` under the complications section: "Implementation target: Stage 7 or later. Depends on working core missions (Stages 5.5 + 6)."

**🛑 CHECKPOINT 7D — Stop. Show the spec and bible additions.**

### Step 7E — Player-Initiated Revolts Ownership

**Bible reference:** `bible_antagonist.md` — "Player-initiated revolts"

**This is not an implementation task.** Same pattern as complications — the feature is designed but unassigned.

**Action:** Add to `bible_antagonist.md` under "Player-initiated revolts": "Implementation target: Stage 7 or later. Requires working mission generator and outcome resolver. Player-initiated revolt is a special outcome band or mission modifier that the outcome resolver processes — the revolt fires through the existing simulation revolt mechanics."

Also add a brief note to the relevant stage spec claiming ownership.

**🛑 CHECKPOINT 7E — Stop. Show the bible and spec additions.**

---

## Phase 8 — Bible and Spec Documentation Updates

These are documentation-only changes that ensure the bible and specs capture design decisions that currently live only in one place or neither.

### Step 8A — Recon Phase → Stage 8

**Action:** Add to the Stage 8 roadmap description in `game_bible.md` (under the Stage 8 paragraph): "Recon phase: free camera over the mission area with no time pressure. Terrain visible, enemy positions based on intelligence quality. Mission clock starts when the player hits 'Begin Mission.' See 'The Cycle' step 2 for the full design."

### Step 8B — Onboarding Screen → Stage 8

**Action:** Add to the Stage 8 roadmap description: "Onboarding screen: single screen with difficulty setting and mission preference weights (10 archetypes, up to 2 markable as rare). Permanent for the generational arc. Opening time jump after confirmation (20–50 years, abbreviated 3–5 entry chronicle scroll). See 'Onboarding and First Chapter' for the full design."

### Step 8C — Edge Type Propagation Queries Note

**Action:** If Phase 2 was implemented, add a note to `bible_world.md` under "Inter-Region Topology": "Implemented in [phase/date]. All adjacency queries specify edge type per the table below." Include the edge type assignment table from Phase 2A.

If Phase 2 was deferred, add: "Edge type filtering is implemented in the graph model. Current templates use 'both' for all edges. Typed edges will be introduced through template updates when land-based eras are designed."

### Step 8D — Per-Archetype Time Limits in Bible

**Action:** If Phase 7C was implemented, add a brief subsection to `bible_missions.md` after "Mission Briefing": "Mission Time Limits — Each archetype has a base time limit (in tactical ticks) scaled by urgency. Higher urgency compresses the time limit by up to 20%. See config for per-archetype values."

**🛑 CHECKPOINT 8 — Stop. Show all documentation changes for review.**

---

## Regression Testing Protocol

**After every phase**, run the full invariant suite (all groups A through current). Any regression is a blocker — do not proceed to the next phase until all previously passing invariants pass again.

**After Phases 2, 4, 5, and 6** (the most structurally impactful changes), additionally run:
- Scenario `07_lifecycle_4faction` for 2000 ticks across 3 seeds — verify lifecycle arc still produces expansion → conflict → fragmentation
- Scenario `10_chronicle_4faction` for 2000 ticks — verify chronicle still produces coherent entries
- Time jump test (scenario `08_time_jump`) — verify time jumps still produce meaningful change
- If Stage 5.5 scenarios exist: run mission generation scenarios and verify mission selection still responds to real simulation pressure

**The regression test results are part of every checkpoint.** Do not present a checkpoint without the invariant suite results attached.
