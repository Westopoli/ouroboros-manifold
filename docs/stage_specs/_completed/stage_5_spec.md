# Stage 5 — Chronicle Pipeline, Coherence Ledger, Library Builder, and Naming System

## Goal

Prove that time jumps produce real narrative: named characters drawn from culturally coherent naming pools, events attached to those characters through a coherence ledger, and 5–10 assembled chronicle scroll entries per jump that read like fragments of a real history — with variable slots filled from simulation data, prose quality enforced by authored fragment rules, and combinatorial variety across seeds. The library builder pipeline generates all content offline (chronicle fragments and naming pools) as production-quality static JSON, using the Claude API or manual input via a MAX subscription. The coherence ledger tracks named characters across their full lifecycle. The distiller compresses hundreds of events into scroll entries through significance scoring, lineage-first clustering, and keyed composable template selection.

This is the stage where the simulation starts producing *story* rather than just *numbers*. Stages 1–4 proved that regions drift, events fire, factions fight, technology grows, empires fragment, and lifecycle phases emerge. Stage 5 proves that these mechanics generate prose a player would want to read.

## Bible References

Read these spoke sections before implementing:

- **`docs/bible_history/bible_2_00_chronicle.md`**: Full file — chronicle scroll distiller algorithm (three passes), template category taxonomy (20 categories), fragment structure (opening/detail/closing), fragment compatibility rule, variable slot vocabulary, fragment generation rules (8 rules), fragment volume per category, library builder validation pass (3 layers), lineage entanglement
- **`docs/bible_history/bible_2_00_ai_pipeline.md`**: "Library builder pipeline" (overview), "Dynamic Naming System" (full section — variable-driven prompt architecture, three variable categories, per-faction variable subsets, Schism cultural drift, era-split pools, library sizing, deduplication, name reuse, coherence ledger interface)
- **`docs/bible_history/bible_2_00_simulation.md`**: "Coherence Ledger" (named character registry, character roles, event attachment)
- **`game_bible.md` (hub)**: "The Generational Structure" (lineage persistence, character selector algorithm, lineage member generation during time jumps), "The Chronicle" (summary), "AI Integration Pillar" (summary)

## What to Build

### Files to create

**`library_builder.py`** — The offline content generation tool. Three operating modes, shared validation pipeline. Contains:
- Mode selection (`--mode api`, `--mode manual`, `--mode api-review`)
- Claude API integration (Anthropic SDK, model selection, prompt caching)
- Prompt construction for chronicle fragments (system prompt + per-category user messages)
- Prompt construction for naming pools (system prompt + per-faction user messages)
- Output parsing and structured JSON assembly
- Manual mode prompt file generation and response ingestion
- API-review mode interactive approval loop
- Dispatches to validation pipeline after each generation batch

See "Library Builder Architecture" section below for full design.

**`library_validator.py`** — Three-layer validation pipeline for all library content. Contains:
- Layer 1: Structural validation (slot vocabulary check, required slot enforcement, word count limits, mechanical language rejection list, fragment ID uniqueness)
- Layer 2: Deduplication (Levenshtein distance within same type pool and category, cross-category opening dedup, diminishing returns flag at configurable threshold)
- Layer 3: Tone and coherence validation (AI-assisted — classification task on individual fragments against category register, sampled assembly coherence check)
- Validation report generation (flags, rejections, thin pools, diminishing returns alerts)

**`naming_system.py`** — Dynamic naming system. Contains:
- Per-faction variable subset storage (linguistic roots, phoneme patterns, cultural flavor tags)
- Variable subset generation at world initialization (assigns 2–3 roots, 3–4 patterns, 3–4 tags per faction from full variable pools)
- Schism cultural drift (breakaway factions inherit parent subset with one value swapped)
- Name pool management per faction per category (people, places, units, factions)
- Pool loading from generated JSON library
- Usage tracking (names assigned to active characters are unavailable)
- 500-tick reuse cooldown (names return to pool after character has been dead 500+ ticks)
- Era-split pool selection (50% agnostic / 50% era-specific draws — Stage 5 generates agnostic pool only)
- Thin interface: `get_name(faction_id, category) → string`
- Levenshtein dedup is handled at build time by `library_validator.py`, not at runtime

**`coherence_ledger.py`** — Named character registry. The central data structure that the distiller, mission generator, and character selector all read from. Contains:
- Character record: ID, name, faction_id, region_id, role (supreme_commander, regional_commander, garrison_officer, lineage_member), birth_tick, death_tick, lineage_id (nullable), status (active, dead)
- Character creation: assigns name via `naming_system.get_name()`, registers in ledger, assigns role
- Character death: marks status, records death_tick, releases name to reuse cooldown
- Lineage tracking: family tree structure per lineage (parent → children links), region of residence per member, generation counter
- Lineage member generation during time jumps: N descendants produced (based on jump duration and fertility config), distributed across regions, registered in ledger with names
- Event attachment: when a significant event fires in a region where a named character resides, the ledger attaches that character to the event log entry
- Lineage significance bonus: events in lineage-occupied regions receive a static bonus in significance scoring (one config value)
- Character queries: `get_characters_in_region(region_id)`, `get_lineage_members(lineage_id)`, `get_character_by_id(char_id)`, `get_lineage_history(lineage_id)` (regions where lineage members have lived)
- Faction leader assignment: each faction gets a named supreme_commander at creation, regional_commanders for home regions

**`chronicle_distiller.py`** — Three-pass scroll distiller algorithm. Contains:
- **Pass 1 — Significance Scoring**: Every event in the time jump log receives a score. Template significance tier (1–5, pre-authored per event template) sets the floor. Delta magnitude (sum of absolute field changes) boosts above the floor. Context multiplier applied: bonus for events in player's last mission region, events involving coherence ledger characters, events in long causal chains (chain length as factor), events in lineage-occupied regions (lineage entanglement bonus). All multiplier weights are config values.
- **Pass 2 — Lineage-First Clustering**: Three tiers of clustering priority.
  - Tier 1 — Lineage clusters: events touching the player's lineage (descendants, commander's former region, family name in ledger, mission consequences). Guaranteed scroll slots. Degrades to "life went on" entry if the lineage had a quiet jump.
  - Tier 2 — Chain clusters: remaining events sharing a chain tag grouped into chain clusters. Each causal chain becomes one potential entry.
  - Tier 3 — Regional summary clusters: standalone events (no lineage, no chain) grouped by region.
  - Consequence cluster (special): events directly resulting from the player's last mission. Always first in scroll.
  - Clusters ranked by highest-scoring event. Top clusters fill 5–10 entry budget. Lineage clusters always included.
- **Pass 3 — Template Selection and Assembly**: Each cluster matched to a template category from the 20-category taxonomy. Category determines fragment pools. Assembly draws one opening + one detail + one closing from category's pools, filtered to fragments whose required slots are resolvable from the cluster's data. Variable slots filled from cluster event data, coherence ledger, and simulation state snapshot. Base form = opening + detail. Expanded form = opening + detail + closing with full slot resolution.
- Output: ordered list of 5–10 scroll entries, each with base_text, expanded_text, cluster_type, category, fragment_ids, resolved_slots

**`chronicle_assembler.py`** — Template assembly engine. Separated from the distiller for clean architecture. Contains:
- Fragment pool loading from generated JSON library
- Category-based pool filtering (filter to fragments whose required slots are resolvable)
- Random fragment selection (one opening + one detail + one closing per entry)
- Variable slot resolution: pull data from three sources (cluster event data, coherence ledger, simulation snapshot)
- State slot mapping: raw numeric values → qualitative prose labels (stability_level: 23 → "precarious", tension_level: 78 → "volatile")
- Duration prose mapping: tick counts → human-readable time phrases ("over three decades," "in a matter of years")
- Base form assembly (opening + detail, under 90 words)
- Expanded form assembly (opening + detail + closing, under 140 words, with full slot resolution)

### Files to modify

**`tick.py`** — Add coherence ledger updates as a new step in the tick resolution sequence, after all existing steps. Per-tick ledger operations: attach named characters to significant events that fired this tick in their region. Character attachment uses the ledger's `get_characters_in_region()` query.

**`faction.py`** — On faction creation (including breakaway factions), assign a named supreme_commander via the coherence ledger. On faction collapse (zero regions), mark the supreme_commander as dead in the ledger.

**`time_jump.py`** — After running N ticks, invoke the lineage member generation step (coherence ledger creates descendants for tracked lineages). After lineage generation, invoke the chronicle distiller on the accumulated event log. Return the distiller's scroll entries alongside the existing structured summary.

**`events.py`** — Add a `significance_tier` field to every event template (integer 1–5). The tier is pre-authored per template — high-tier events (first contact, faction collapse, conquest) score higher in the distiller's Pass 1 regardless of their mechanical impact. Assign tiers to all existing event templates.

**`config.py`** — Add all new config values (see Config Values to Add section).

**`sim_tuner.py`** — Add Chronicle Review Report mode (see Validation section).

**`invariants.py`** — Add Group K invariants (see below).

### Files NOT to create or modify

The mission generator, mission outcome resolver, force allocation algorithm, and mission briefing templates are all Stage 5.5. The tactical layer, combat system, Godot frontend, chronicle scroll UI, and map generation system are later stages. Era-specific naming pools (sci-fi era names) are a future task — Stage 5 generates the era-agnostic pool only. The character selector algorithm is structurally defined in Stage 4's `generational.py` with placeholder character IDs — Stage 5 wires it to the coherence ledger for real names, but does not change the selection logic.

---

## Mandatory Checkpoints

> **REMINDER — THIS IS NON-NEGOTIABLE.** Each lettered step below is a mandatory checkpoint. After completing each step, run the specified test, show the output to Westley, and **stop executing. Do not continue to the next step until Westley approves.** Do not evaluate output yourself and decide to proceed. Do not batch multiple steps. Do not "fix" something and continue without showing the fix. Each checkpoint requires Westley's explicit approval before the next step begins. See dev_rules.md "Mandatory Checkpoints — STOP AND WAIT" for the full policy.

## Implementation Steps

### A — Naming System (standalone, no dependencies)

Build `naming_system.py` with the runtime interface (`get_name`, `release_name`, `is_available`), pool loading from JSON, usage tracking, and 500-tick reuse cooldown. Use a small hardcoded test pool (10 names per category for 2 test factions) — the real pools come from the library builder later.

**Test:** Create 2 test factions with 10-name pools. Draw 8 names from faction 1 — confirm all unique. Draw a 9th — confirm it's different from the first 8. Release a name at tick 100. Confirm `is_available()` returns False at tick 599, True at tick 601. Draw from faction 2 — confirm names come from faction 2's pool, not faction 1's. Print all draws, releases, and availability checks.

**🛑 CHECKPOINT A — Stop executing. Show output to Westley. Wait for approval before continuing.**

---

### B — Coherence Ledger (standalone, depends on naming system)

Build `coherence_ledger.py` with character records, creation, death, lineage tracking, event attachment, and all query methods. Wire it to the naming system for name assignment.

**Test:** Create 2 factions. Confirm each gets a supreme_commander with a name from the naming system. Create a region — confirm a regional_commander is assigned. Kill the regional_commander — confirm status changes to "dead", death_tick recorded, name enters cooldown. Create 3 lineage members for a test lineage — confirm parent-child links, region assignments, and unique names. Simulate event attachment: fire a test event in a region with a named character, confirm the character is attached to the event log entry. Print all character records, lineage tree, and the event attachment.

**🛑 CHECKPOINT B — Stop executing. Show output to Westley. Wait for approval before continuing.**

---

### C — Coherence Ledger Integration (wire into tick loop and faction creation)

Modify `tick.py` to add the per-tick ledger step (character attachment to significant events). Modify `faction.py` to assign supreme_commanders on faction creation and mark them dead on faction collapse.

**Test:** Run scenario `08_lifecycle_2faction` for 300 ticks with the ledger enabled. Print: total characters created, total characters dead, total event attachments, faction leaders at tick 300 (name, faction, status for each). Confirm every faction with ≥1 region has an active supreme_commander. Confirm at least 1 event attachment occurred (a significant event had a named character in its region).

**🛑 CHECKPOINT C — Stop executing. Show output to Westley. Wait for approval before continuing.**

---

### D — Library Builder: Chronicle Fragment Generation

Build `library_builder.py` with mode selection (`--mode api`, `--mode manual`, `--mode api-review`). Implement the chronicle fragment generation workflow (system prompt construction, per-category user messages, response parsing).

**Test (manual mode):** Run `library_builder.py --mode manual --content chronicle`. Confirm it generates 20 numbered prompt files in `prompts/`. Open prompt file 01 — confirm it contains the system prompt with all 8 fragment rules, the slot vocabulary, and the per-category instructions. Confirm the output format specification asks for JSON. Print the prompt file count and the first prompt's category name and required slots.

**🛑 CHECKPOINT D — Stop executing. Show output to Westley. Wait for approval before continuing.**

---

### E — Library Validator

Build `library_validator.py` with all three validation layers: structural (slot checking, word limits, mechanical language rejection), dedup (Levenshtein within pools, cross-category opening dedup, diminishing returns flag), and tone/coherence (AI-assisted classification on fragments, sampled assembly coherence).

**Test:** Create a small test fragment library (3 categories, 5 fragments each) with deliberate errors: one fragment using an invalid slot, one exceeding the word limit, two near-duplicate fragments, one with mechanical language ("stability dropped to 23"). Run all three validation layers. Print the validation report: structural failures with reasons, dedup matches with edit distances, mechanical language rejections. Confirm all deliberate errors are caught.

**🛑 CHECKPOINT E — Stop executing. Show output to Westley. Wait for approval before continuing.**

---

### F — Library Builder: Naming Pool Generation

Add the naming pool generation workflow to `library_builder.py` (variable subset generation, per-faction per-category name generation, response parsing).

**Test (manual mode):** Run `library_builder.py --mode manual --content naming`. Confirm it generates variable subsets for 10 factions (written to `variable_subsets.json`) and 40 numbered prompt files. Open `variable_subsets.json` — confirm each faction has 2–3 roots, 3–4 patterns, 3–4 tags, and that the player faction has a wider subset. Open one naming prompt — confirm it includes the faction's variable subset, the category, and the count with 10% overshoot. Print subset summary (faction ID → root count, pattern count, tag count) and prompt file count.

**🛑 CHECKPOINT F — Stop executing. Show output to Westley. Wait for approval before continuing.**

---

### G — Generate Production Library Content

Run the library builder (manual or API mode — Westley's choice) to generate the full production library: 380 chronicle fragments across 20 categories, and 10,000 names across 10 factions × 4 categories. Run the full validation pipeline on the output.

**Test:** Print the validation report summary: fragments per category (confirm 19 per category — 6 openings, 8 details, 5 closings), dedup losses per category, any thin pool flags, any diminishing returns flags, structural failure count (should be 0 after clean generation). For naming: names per faction per category (should be ≥ target after dedup), cross-faction dedup results, any pool exhaustion warnings. Print 3 sample fragments from 3 different categories and 5 sample names from 3 different factions for Westley to eyeball quality.

**🛑 CHECKPOINT G — Stop executing. Show output AND the sample content to Westley. This is a quality gate — Westley evaluates prose quality and naming coherence. Wait for approval before continuing.**

---

### H — Chronicle Distiller (standalone)

Build `chronicle_distiller.py` with all three passes (significance scoring, lineage-first clustering, template selection) and `chronicle_assembler.py` (fragment pool loading, slot resolution, assembly). Wire the assembler to use the production fragment library generated in step G.

**Test:** Construct a mock event log (30 events across 5 regions, including: 2 events in a lineage-occupied region, 1 chain of 3 linked events, 5 standalone events, 1 conquest event with a named character attached). Run the distiller. Print the full Pass 1 significance scores (all 30 events ranked). Print the Pass 2 clustering output (which events went into which clusters, cluster types, category assignments). Print all assembled scroll entries with base_text, expanded_text, fragment_ids, and resolved slots. Confirm: 5–10 entries produced, lineage cluster present, chain cluster present, all slots resolved to non-empty strings, word counts within limits.

**🛑 CHECKPOINT H — Stop executing. Show the assembled scroll entries to Westley. This is a prose quality gate. Wait for approval before continuing.**

---

### I — Chronicle Distiller Integration (wire into time jump)

Modify `time_jump.py` to invoke lineage member generation and the chronicle distiller after running N ticks. Add significance tiers to all existing event templates in `events.py`. Wire the distiller to read from the coherence ledger and simulation state.

**Test:** Run scenario `09_chronicle_2faction` for 1000 ticks with chronicle review at ticks 300, 600, 900. Print the Chronicle Review Report for each time jump (full format as specified in the Validation section — event log summary, top significance scores, clusters formed, all scroll entries with base and expanded text). Confirm: each jump produces 5–10 entries, lineage clusters appear in every jump, slot resolution produces natural prose, no empty slots.

**🛑 CHECKPOINT I — Stop executing. Show the Chronicle Review Report to Westley. This is the primary prose quality gate. Wait for approval before continuing.**

---

### J — Schism Cultural Drift and Naming Edge Cases

Implement Schism cultural drift in `naming_system.py` (breakaway inherits parent subset with one value swapped). Wire into `faction.py` breakaway creation.

**Test:** Create a parent faction with a known variable subset. Create 3 breakaway factions from it. Print each breakaway's subset alongside the parent's — confirm exactly 1 value differs per breakaway, and the differing value is in a random category each time. Draw 5 names from the parent and 5 from each breakaway — print them side by side. Confirm they sound related but distinct (Westley evaluates).

**🛑 CHECKPOINT J — Stop executing. Show the naming comparison to Westley. Wait for approval before continuing.**

---

### K — Invariants and Full Validation

Add all K1–K12 invariants to `invariants.py`. Add scenarios 09, 10, 11 to `sim_tuner.py`.

**Test:** Run scenario `10_chronicle_4faction` with seeds 1–3. Print the invariant results table for all K1–K12 plus regression check K12 (all A–J invariants). Print any failures or warnings with full detail. Run scenario `11_naming_stress` (3000 ticks) — confirm no naming pool exhaustion.

**🛑 CHECKPOINT K — Stop executing. Show the full invariant report to Westley. Wait for approval before continuing.**

---

### L — Chronicle Review Report: Final Quality Gate

Run `sim_tuner.py --chronicle-review` on scenario `10_chronicle_4faction` with seeds 1, 2, 3. Generate the full Chronicle Review Reports.

**Test:** Present all 3 review reports to Westley. This is the final subjective quality gate — Westley reads the scroll entries across multiple seeds and multiple time jumps, evaluates prose quality, fragment coherence, naming consistency, lineage entanglement, and significance scoring.

**🛑 CHECKPOINT L — Stop executing. Show all Chronicle Review Reports to Westley. This is the Stage 5 sign-off gate. Do not proceed to any further work until Westley explicitly approves Stage 5 as complete.**

---

## Library Builder Architecture

The library builder is the offline content generation tool that produces the JSON libraries the game reads at runtime. It makes Claude API calls (or accepts manual input) to generate chronicle fragments and naming pools, then runs a validation pipeline on the output. All generated content is **production-quality and ships with the game**. This is not test content.

### Three Operating Modes

**`--mode api`** — Fully automated. The builder constructs prompts, sends them to the Claude API, parses responses, runs validation, and writes the output JSON. Hands-off except for reviewing the validation report afterward. Uses prompt caching for input efficiency.

**`--mode manual`** — Zero API cost, uses the developer's Claude MAX subscription. The builder constructs the same prompts it would send to the API and writes them to numbered prompt files in a `prompts/` directory, each with clear instructions:

```
=== PROMPT 03 of 20 — Category: lineage_military_action ===
Copy everything below the line into Claude (claude.ai).
Save Claude's complete response to: batch_output/03_lineage_military_action.txt
────────────────────────────────────────────────────────
[system prompt content]

[user message content]
```

The builder watches the `batch_output/` directory and processes response files as they appear, running the same validation pipeline on each. A progress display shows which categories are complete and which are pending.

**EMPHASIS: The manual mode is the primary recommended workflow.** A Claude MAX subscription provides unlimited access to the same models at zero marginal cost per generation. The API mode exists for convenience and automation, but for a solo developer, the manual mode is the cost-optimal path for generating production content. The spec is designed so that manual mode is not a second-class experience — it produces identical output and runs identical validation. The only difference is the human copy-paste step.

**`--mode api-review`** — Hybrid. The builder constructs each prompt and displays it in the terminal with the prompt content and a confirmation prompt:

```
=== Category: lineage_military_action (03/20) ===
[prompt preview — first 10 lines + "..." + last 5 lines]

Send this prompt? [y/n/edit/skip]:
```

On `y`, the builder sends the prompt to the API and processes the response. On `n`, it skips to the next. On `edit`, it opens the prompt in the system editor for modification before sending. On `skip`, it marks the category for later. After all categories are processed, skipped categories can be re-run. This mode is for developers who want to review prompts before incurring API cost, or who want to tweak individual prompts based on earlier results.

### API Integration

**Model:** `claude-sonnet-4-20250514` for all content generation. Sonnet is sufficient for structured prose generation within well-defined constraints (category definitions, fragment rules, slot vocabulary). Opus is not needed — the quality floor is enforced by the fragment rules and validation pipeline, not by model capability.

**Prompt caching:** The system prompt contains all universal context (fragment rules, slot vocabulary, word limits, prose quality rules, tone lock, example fragments). This content is identical across all calls and is cached by the Anthropic API. Per-category context (emotional register, required slots, category-specific instructions) goes in the user message. Caching reduces effective input cost by ~90% on the shared context across the 20 chronicle category calls and across per-faction naming calls.

**System prompt structure for chronicle generation:**
```
[Universal context — cached across all calls]
- Fragment generation rules (all 8 rules from bible)
- Variable slot vocabulary (full list with descriptions)
- Fragment structure definitions (opening/detail/closing with word limits)
- Compatibility rule explanation
- 2–3 example fragments showing expected quality and format
- Output format specification (JSON array of fragment objects)

[User message — per-category, not cached]
- Category name and emotional register
- Required and optional slots for this category
- "Generate 6 opening fragments, 8 detail fragments, and 5 closing fragments for this category."
```

**System prompt structure for naming generation:**
```
[Universal context — cached across all calls]
- Variable category definitions (linguistic roots, phoneme patterns, cultural flavor tags)
- Full value lists for each variable category
- Dedup guidance (avoid phonetically similar names within a batch)
- Output format specification (JSON array of name strings)
- Era-agnostic constraint (no era-specific references)

[User message — per-faction per-category, not cached]
- Faction's variable subset (which roots, patterns, tags are allowed)
- Name category (people/places/units/factions)
- Count to generate (e.g., "Generate 55 people names" — 10% overshoot for dedup losses)
- Any previously generated names for this faction (for cross-batch dedup)
```

### Output Format

All library content is stored as JSON files in the `data/library/` directory:

```
data/library/
├── chronicle/
│   ├── fragments.json          # All 380 fragments, keyed by category and type
│   └── validation_report.json  # Builder validation output
├── naming/
│   ├── faction_{id}_people.json
│   ├── faction_{id}_places.json
│   ├── faction_{id}_units.json
│   ├── faction_{id}_factions.json
│   ├── variable_subsets.json   # Per-faction variable assignments
│   └── validation_report.json
└── manifest.json               # Library version, generation date, model used, mode used
```

**Fragment JSON structure:**
```json
{
  "category": "lineage_thrived",
  "type": "opening",
  "id": "LT_O_001",
  "text": "In the {duration_prose} since {character_name}'s command, the {lineage_name} family found itself ascending —",
  "slots_used": ["duration_prose", "character_name", "lineage_name"],
  "word_count": 17
}
```

**Name JSON structure:**
```json
{
  "faction_id": "faction_001",
  "category": "people",
  "names": ["Kaelith Vorn", "Suranna Deshkov", ...],
  "variable_subset": {
    "linguistic_roots": ["Tolkien-esque", "Germanic compound"],
    "phoneme_patterns": ["two-part compound", "patronymic"],
    "cultural_flavor_tags": ["martial", "frontier/rough", "imperial/formal"]
  }
}
```

### Builder Workflow — Chronicle Fragments

The builder generates chronicle fragments category-by-category (20 categories, one API call per category). Each call produces all 19 fragments for that category (6 openings + 8 details + 5 closings).

**Step 1:** Load or construct the system prompt (universal fragment rules, slot vocabulary, examples). This is identical across all 20 calls and is cached.

**Step 2:** For each category (in the order defined in the taxonomy):
1. Construct the user message with the category's emotional register, required/optional slots, and generation instruction.
2. Send (or display for manual/review mode).
3. Parse the response into fragment objects.
4. Run Layer 1 validation (structural) on the batch immediately.
5. If structural failures > 30% of the batch, flag the category and log the issues. Do not retry automatically — the prompt needs revision.
6. Store passing fragments in the accumulating library.

**Step 3:** After all 20 categories are processed, run Layer 2 validation (dedup) across the full library. Cross-category opening dedup runs here. Report diminishing returns flags for any category that lost >30% to dedup.

**Step 4:** Run Layer 3 validation (tone/coherence). Sample ~10 random assembled entries per category. Flag tone mismatches. This step uses one additional API call per category (20 calls total) for the tone classification task.

**Step 5:** Write `fragments.json` and `validation_report.json`.

### Builder Workflow — Naming Pools

The builder generates naming pools per-faction, per-category. For 10 factions × 4 categories = 40 generation batches. Each batch generates 10% more names than the target (to absorb dedup losses).

**Step 1:** Generate or load variable subsets for all 10 factions. This is one API call that produces 10 subsets, or can be done manually. Store in `variable_subsets.json`.

**Step 2:** For each faction, for each name category:
1. Construct the user message with the faction's variable subset, the category, the count (target + 10%), and any previously generated names for this faction (for cross-category dedup within a faction).
2. Send (or display for manual/review mode).
3. Parse the response into a name list.
4. Run Levenshtein dedup against all previously generated names for this faction (edit distance threshold: configurable, default 3).
5. Store passing names.

**Step 3:** After all factions are complete, run cross-faction dedup on place names and faction names (people names and unit names are allowed to overlap across factions — real naming conventions reuse similar sounds). Report any thin pools.

**Step 4:** Write per-faction JSON files and `validation_report.json`.

### Cost Optimization

**Prompt caching** is the primary cost optimization. The system prompt (~800 tokens) is cached and reused across all calls within a session. Cached input tokens are charged at 10% of the standard rate.

**Batching** within calls: each call generates all fragments for a category (19 fragments) or a large batch of names (50–55 per call), rather than individual items.

**Estimated total API cost (api mode):**
- Chronicle fragments: 20 generation calls + 20 validation calls = 40 calls. ~30K effective input tokens (after caching), ~40K output tokens. Estimated cost: ~$0.40.
- Naming pools: 1 subset call + 40 generation calls = 41 calls. ~25K effective input tokens (after caching), ~50K output tokens. Estimated cost: ~$0.50.
- Total: ~$1.00 for the full production library.

**Manual mode cost: $0.** Uses the developer's existing Claude MAX subscription. Same output quality, same validation pipeline. The only cost is the developer's time for copy-paste operations (~40 paste cycles for chronicle, ~41 for naming).

---

## Coherence Ledger Design

The coherence ledger is the named character registry that connects the simulation's mechanical events to narrative identity. Every character in the game world — commanders, faction leaders, garrison officers, lineage members — exists as a record in the ledger. The ledger is the single source of truth for "who exists, where they are, and what they've been involved in."

### Character Lifecycle

**Creation:** Characters are created when:
- A faction is created (supreme_commander assigned)
- A region is conquered or colonized (regional_commander assigned)
- Lineage members are generated during time jumps (lineage_member role)
- The character selector picks a new commander (upgrades a lineage_member to supreme_commander or regional_commander)

Each creation calls `naming_system.get_name(faction_id, "people")` for the character's name.

**Active life:** While active, characters:
- Reside in a region (tracked, can change during time jumps)
- Are attached to events that fire in their region (via the per-tick attachment step)
- Accumulate event history (list of event IDs they were attached to)

**Death:** Characters die when:
- Their faction collapses (supreme_commander dies)
- Their region is conquered (regional_commander may die — probability based on battle severity)
- Natural death during time jumps (age-based probability, checked during lineage generation step)
- Commander killed during a mission (logged from mission outcome)

On death: status set to "dead", death_tick recorded, name enters 500-tick reuse cooldown in the naming system.

### Lineage Tracking

The ledger maintains family trees for the player's lineages (current and all previous). Each lineage is a tree of character records linked by parent-child relationships.

**During time jumps:** The lineage generator runs for every tracked lineage. It produces N new descendants (N based on jump duration × fertility config value), assigns them regions (based on where the family currently lives, with small probability of spreading to adjacent regions), creates character records in the ledger, and assigns names.

**Minimal simulation:** Lineage members are not full agents. They don't make decisions, don't have personality traits, don't have careers. They are entries in a registry: name, region, age, alive/dead. The chronicle distiller and template system add narrative richness in prose — the ledger just tracks who exists and where.

### Event Attachment

Each tick, after all simulation steps complete, the ledger scans for significant events that fired this tick. For each significant event, the ledger checks if any named characters reside in the event's region. If yes, the highest-ranking character is attached to the event log entry. Attachment means the event's log entry gains a `character_id` field that the distiller's variable slot resolution can read.

"Significant" for attachment purposes uses a simple threshold: events with significance tier ≥ 3 (out of 5) trigger character attachment. This is a separate, simpler check than the distiller's full significance scoring — it runs per-tick during the simulation, not in batch during distillation.

### Lineage Entanglement

Events in regions where lineage members reside receive a static significance bonus in the distiller's Pass 1 scoring. This is one additional term in the scoring formula controlled by `LINEAGE_SIGNIFICANCE_BONUS` in config. The bonus ensures lineage events naturally bubble up through the distiller's ranking without hard-scripting lineage involvement. The ledger provides the data; the distiller applies the bonus during scoring.

---

## Chronicle Distiller Design

The distiller compresses a time jump's full event log (potentially hundreds of events) into 5–10 scroll entries. It runs once per time jump, after the simulation ticks complete and the lineage generator has run.

### Input

- The complete event log from the time jump (every event that fired, with: event_id, template_id, region_id, tick, field deltas, chain_tag, chain_position)
- The coherence ledger (current state after the jump)
- The simulation state snapshot (region fields at end of jump)
- The player's last mission result (region, archetype, outcome band) — for consequence entries
- The player's current lineage_id

### Output

An ordered list of 5–10 `ScrollEntry` objects:

```python
@dataclass
class ScrollEntry:
    base_text: str           # Opening + detail, under 90 words
    expanded_text: str       # Opening + detail + closing, under 140 words
    cluster_type: str        # "lineage", "chain", "regional", "consequence"
    category: str            # One of 20 template categories
    fragment_ids: list[str]  # IDs of the opening, detail, closing fragments used
    resolved_slots: dict     # All variable slots and their resolved values
    source_events: list[int] # Event IDs that contributed to this entry's cluster
    region_id: str           # Primary region for this entry (for map sync)
    tick_range: tuple[int, int]  # First and last tick of events in this cluster
```

### Pass 1 — Significance Scoring

```python
def score_event(event, ledger, player_lineage_id, last_mission_region):
    # Floor: template significance tier (1–5)
    base = event.template.significance_tier

    # Boost: delta magnitude
    delta_mag = sum(abs(d) for d in event.field_deltas.values())
    delta_boost = min(delta_mag / SIGNIFICANCE_DELTA_SCALE, SIGNIFICANCE_DELTA_CAP)

    # Context multiplier (combined, not stacked)
    context = 1.0
    if event.region_id == last_mission_region:
        context += SIGNIFICANCE_MISSION_REGION_BONUS
    if event.character_id is not None:
        context += SIGNIFICANCE_CHARACTER_BONUS
    if event.chain_length > 1:
        context += SIGNIFICANCE_CHAIN_LENGTH_BONUS * min(event.chain_length, CHAIN_LENGTH_CAP)
    if ledger.lineage_in_region(player_lineage_id, event.region_id):
        context += LINEAGE_SIGNIFICANCE_BONUS

    return (base + delta_boost) * context
```

### Pass 2 — Lineage-First Clustering

1. **Extract consequence cluster.** All events that are direct consequences of the player's last mission (identified by mission_consequence flag in event log). This cluster is always first in the scroll. Matched to one of the three consequence categories (success/failure/mixed) based on the outcome band.

2. **Extract lineage clusters.** Scan all remaining events for lineage connection: event in a region where a lineage member resides, event attached to a lineage character, event in the last mission region, event resulting from mission consequences that propagated. Group connected lineage events by region into lineage clusters. Match each to a lineage category (thrived/suffered/quiet/military_action/succession) based on the dominant event types and field deltas.

3. **Extract chain clusters.** Group remaining events by chain_tag. Each chain becomes a cluster. Match to a chain category based on chain resolution (crisis resolved well/badly, conflict victory/stalemate/defeat, revolt spawned, expansion, cascade).

4. **Extract regional summary clusters.** Group remaining standalone events by region. Match to a regional category (decline/growth/stable/faction_shift) based on net field deltas.

5. **Rank and select.** Consequence cluster is slot 1 (always). Lineage clusters fill the next slots (always included regardless of score). Remaining slots (up to 5–10 total budget) filled by the highest-scoring chain and regional clusters, ranked by their peak event score.

### Pass 3 — Template Selection and Assembly

For each selected cluster, the assembler:

1. Determines the template category from the cluster's type and classification.
2. Loads the fragment pools for that category from the JSON library.
3. Filters each pool to fragments whose required slots can be resolved from this cluster's available data (e.g., exclude fragments requiring `{character_name}` if no character is attached).
4. Randomly selects one opening, one detail, one closing from the filtered pools.
5. Resolves all variable slots from three data sources:
   - **Cluster event data** → `{event_description}`, `{chain_length}`, `{duration_ticks}`, `{duration_prose}`
   - **Coherence ledger** → `{character_name}`, `{character_rank}`, `{character_faction}`, `{lineage_name}`, `{faction_name}`, `{region_name}`, `{adjacent_region}`
   - **Simulation snapshot** → `{field_delta_summary}`, `{stability_level}`, `{capacity_level}`, `{tension_level}`
   - **Consequence slots** (if consequence cluster) → `{mission_outcome}`, `{mission_archetype}`, `{mission_region}`
   - **Relational slots** → `{previous_event_reference}`, `{lineage_history_note}` (resolved from ledger history)
6. Assembles base_text (opening + detail) and expanded_text (opening + detail + closing).
7. Validates word counts (base < 90, expanded < 140). If over, the entry is flagged in the review report but still included.

---

## Naming System Design

The naming system generates names offline via the library builder and serves them at runtime through a thin interface. It has no AI dependencies at runtime.

### Variable Architecture

Three variable categories with pre-defined value pools:

**Linguistic roots** (~15–20 values): Semitic triconsonantal, Polynesian open syllables, Germanic compound, Sino-monosyllabic, Tolkien-esque (Elvish-inspired), ancient Greek, Sumerian, invented liquid-heavy, invented guttural-aspirated, Sanskrit-derived, Bantu agglutinative, Gaelic consonant-cluster, Persian flowing, Nahuatl compound, Japanese mora-based, Slavic palatalized. (Final list generated by the builder's first call.)

**Phoneme patterns** (~10–15 values): patronymic (-son, -ov, -ibn), place-derived (-of-[place]), title-prefix, two-part compound, single name only, three-syllable cadence, consonant-final, vowel-final, reduplicative, honorific-suffix, clan-prefix. (Final list generated by the builder's first call.)

**Cultural flavor tags** (~8–12 values): martial, pastoral, mercantile, priestly, frontier/rough, imperial/formal, scholarly, nomadic, maritime, aristocratic, revolutionary, ancient/archaic. (Final list generated by the builder's first call.)

### Per-Faction Subsets

At world generation, each of the 10 factions receives:
- 2–3 linguistic roots (randomly selected from the full pool)
- 3–4 phoneme patterns (randomly selected)
- 3–4 cultural flavor tags (randomly selected)

The subset width is a tuning knob: the player's faction gets a wider subset (more cosmopolitan names), isolated factions get narrower subsets (more culturally coherent names).

### Schism Cultural Drift

When a breakaway faction is created (from admin revolt or tension revolt), it inherits its parent faction's variable subset with exactly one value swapped in one randomly chosen category. The breakaway's names sound *almost* like the parent's but slightly off. This is automatic — no special generation step needed, just subset manipulation at faction creation.

### Pool Sizing

Per faction: 500 people, 200 places, 200 units, 100 factions. For 10 factions = 10,000 names total.

Names are generated with a 10% overshoot (e.g., 550 people names per faction) to absorb Levenshtein dedup losses. The dedup threshold is configurable (default: edit distance 3). Matches are dropped silently — no regeneration.

### Runtime Interface

```python
class NamingSystem:
    def get_name(self, faction_id: str, category: str) -> str:
        """Draw a name from the faction's pool for the given category.
        Marks the name as in-use. Returns a random available name."""

    def release_name(self, name: str, death_tick: int) -> None:
        """Mark a name as released. Available again after 500-tick cooldown."""

    def is_available(self, name: str) -> bool:
        """Check if a name is currently available (not in use, past cooldown)."""
```

The ledger calls `get_name()` on character creation and `release_name()` on character death. The naming system handles pool management internally. Clean separation of concerns.

---

## Behavioral Claims

### Chronicle Distiller

**Claim K1: Every time jump produces 5–10 scroll entries.** The distiller must always output between 5 and 10 entries, regardless of how many or few events occurred during the jump.
- When: chronicle distiller runs after any time jump of ≥20 ticks
- Then: len(scroll_entries) is between 5 and 10 inclusive
- Over: every time jump in every scenario
- Pattern: threshold bound
- Governing configs: `CHRONICLE_MIN_ENTRIES`, `CHRONICLE_MAX_ENTRIES`
- Severity: critical

**Claim K2: Lineage clusters always appear in the scroll.** At least one scroll entry must be a lineage cluster, even if the lineage had a quiet jump.
- When: chronicle distiller runs and a player lineage exists
- Then: at least one entry has cluster_type == "lineage"
- Over: every time jump
- Pattern: threshold bound
- Governing configs: (code bug if violated — lineage clusters are guaranteed slots)
- Severity: critical

**Claim K3: Consequence entries always appear first.** If the player completed a mission before this time jump, the first scroll entry must be a consequence cluster.
- When: chronicle distiller runs and a mission outcome exists for this jump
- Then: scroll_entries[0].cluster_type == "consequence"
- Over: every time jump following a mission
- Pattern: threshold bound
- Severity: critical

**Claim K4: No fragment exceeds word limits.** Every assembled entry must respect the hard limits: base form < 90 words, expanded form < 140 words.
- When: any scroll entry is assembled
- Then: word_count(base_text) < 90 and word_count(expanded_text) < 140
- Over: every scroll entry in every time jump
- Pattern: threshold bound
- Severity: warning (flagged in review report, not a hard failure)

**Claim K5: All required slots resolve.** Every fragment selected for assembly must have all its required slots successfully resolved to non-empty strings.
- When: assembler selects a fragment
- Then: all slots marked as required in the category definition resolve to non-empty values
- Over: every scroll entry
- Pattern: threshold bound
- Governing configs: (code bug if violated — slot filtering should prevent unresolvable selections)
- Severity: critical

**Claim K6: No duplicate fragments in the library.** After the dedup pass, no two fragments in the same type pool within the same category should have a Levenshtein distance below the threshold.
- When: library validation runs
- Then: all fragment pairs in the same pool have edit distance ≥ threshold
- Over: full fragment library
- Pattern: threshold bound
- Governing configs: `FRAGMENT_DEDUP_THRESHOLD`
- Severity: critical

### Coherence Ledger

**Claim K7: Every faction has a named leader.** At any point in the simulation, every faction with ≥1 region has a character with role supreme_commander in the ledger.
- When: any tick
- Then: for each faction with region_count > 0, at least one character with role == "supreme_commander" and status == "active" exists
- Over: every tick
- Pattern: threshold bound
- Severity: critical

**Claim K8: Lineage members are generated during time jumps.** After a time jump of N ticks, the player's current lineage should have gained at least 1 new descendant (for jumps > 50 ticks).
- When: time jump completes with duration > 50 ticks
- Then: lineage member count increased by ≥ 1
- Over: every qualifying time jump
- Pattern: threshold bound
- Governing configs: `LINEAGE_FERTILITY_RATE`
- Severity: warning

**Claim K9: Dead characters' names eventually become available.** A character who dies at tick T should have their name available for reuse by tick T + 500.
- When: character death at tick T
- Then: naming_system.is_available(character.name) returns True at tick T + 501
- Over: every character death
- Pattern: threshold bound
- Governing configs: `NAME_REUSE_COOLDOWN_TICKS`
- Severity: warning

### Naming System

**Claim K10: Names are unique within a faction at any point in time.** No two active characters in the same faction should share a name.
- When: any tick
- Then: no duplicate names among active characters in the same faction
- Over: every tick
- Pattern: threshold bound
- Severity: critical

**Claim K11: Schism factions have distinct but related naming.** A breakaway faction's variable subset should differ from its parent's by exactly one value in one category.
- When: breakaway faction created
- Then: faction's variable subset differs from parent's by exactly 1 value swap
- Over: every breakaway creation
- Pattern: threshold bound
- Severity: warning

### Regression

**Claim K12: All Stage 4 invariants still pass.** No regression in previously validated behavior.
- Over: full run
- Pattern: regression check
- Severity: critical

---

## Validation — Chronicle Review Report

The Chronicle Review Report is the primary validation mechanism for prose quality, fragment compatibility, and narrative coherence. It is designed for human review — the developer reads the output, evaluates quality, and provides feedback to Claude Code for adjustments.

### Report Generation

`sim_tuner.py` gains a `--chronicle-review` flag:

```bash
python sim_tuner.py --scenario 07_lifecycle_4faction --chronicle-review --seeds 1,2,3
```

This runs the scenario for each seed, executes time jumps at configurable tick intervals (default: every 500 ticks), and for each jump produces a review section in the output report.

### Report Format

The report is a plain text file (`chronicle_review_seed_{N}.txt`) designed for readability. Each time jump produces a section:

```
════════════════════════════════════════════════════════════════
TIME JUMP: Tick 500 → 600 (100 ticks, ~40 simulated years)
Seed: 1 | Factions alive: 6 | Events fired: 47
════════════════════════════════════════════════════════════════

── Event Log Summary ──────────────────────────────────────────
  Total events: 47
  By type: ATTACK (12), CONQUEST (3), ADMIN_REVOLT (4), TENSION_THRESHOLD (8),
           COLONIZE (2), DIPLOMATIC_OVERTURE (1), BETRAYAL (1), drift events (16)
  Chains completed: 5
  Characters attached: 8

── Top 10 Significance Scores ────────────────────────────────
  1. [Score 14.2] CONQUEST in Region_04 (tick 523) — char: Kaelith Vorn
  2. [Score 12.8] ADMIN_BREAKAWAY in Region_07 (tick 551)
  3. [Score 11.1] ATTACK in Region_02 (tick 534) — char: Suranna Deshkov (lineage)
  ...

── Clusters Formed ───────────────────────────────────────────
  Consequence: 1 cluster (mission success in Region_02)
  Lineage: 2 clusters (military_action, thrived)
  Chain: 3 clusters (conflict_victory, revolt_spawned, crisis_resolved_well)
  Regional: 2 clusters (regional_decline, regional_growth)
  Selected for scroll: 7 entries (budget: 5–10)

── SCROLL ENTRY 1 of 7 ──────────────────────────────────────
  Type: consequence_success
  Category: consequence_success
  Fragments: [CS_O_003] + [CS_D_005] + [CS_C_002]
  Slots: {mission_outcome: "a decisive victory", mission_region: "Korath Expanse",
          character_name: "Suranna Deshkov", lineage_name: "Deshkov"}

  BASE TEXT:
  "In the wake of Suranna Deshkov's command, the defense of the Korath Expanse
  proved a decisive victory. The garrison held against three waves, and the
  Deshkov name carried new weight along the frontier."

  EXPANDED TEXT:
  "In the wake of Suranna Deshkov's command, the defense of the Korath Expanse
  proved a decisive victory. The garrison held against three waves, and the
  Deshkov name carried new weight along the frontier. Stability returned to
  the region within a decade, though the scars of the assault marked
  the landscape for a generation longer."

  Word count: base 38, expanded 61
  ──────────────────────────────────────────────────────────────

── SCROLL ENTRY 2 of 7 ──────────────────────────────────────
  [... same format ...]

════════════════════════════════════════════════════════════════
```

### Review Workflow

1. Run `sim_tuner.py --chronicle-review` across 3–5 seeds.
2. Read the review reports. Evaluate:
   - Do the scroll entries read like fragments of a real history?
   - Do fragments within an entry feel coherent when assembled?
   - Are variable slots resolving to natural-sounding prose?
   - Is the lineage entanglement producing meaningful family connections?
   - Is the significance scoring surfacing the right events?
3. If a category's fragments are weak (e.g., `lineage_quiet` entries feel flat), provide feedback to Claude Code: "The `lineage_quiet` openings are too generic — they need more specificity about the passage of time." Claude Code adjusts the generation prompts in the builder and regenerates that category only.
4. If config tuning is needed (e.g., lineage bonus is too high, drowning out chain clusters), adjust config values and re-run.
5. Repeat until the prose quality meets the bar across multiple seeds.

### What the Report Does NOT Do

The report does not auto-tune anything. It does not evaluate prose quality programmatically (beyond word count limits). It does not compare across seeds automatically. It is a **display tool** — it shows you what the system produced so you can judge it. The mechanical invariants (K1–K12) catch structural bugs. The review report catches quality issues.

---

## Scenarios to Add

```python
"09_chronicle_2faction": {
    "template":     "contested_border",
    "ticks":        1000,
    "seed":         1,
    "description":  "Chronicle test — 2 factions, 1000 ticks, chronicle review at tick 300, 600, 900",
    "use_tick_engine": True,
    "features": {
        "events": True, "factions": True, "border_friction": True,
        "recruitment": True, "adjacency_bonus": True, "oscillation": True,
        "technology": True, "diplomacy": True, "admin_revolts": True,
        "chronicle": True, "coherence_ledger": True, "naming": True,
    },
    "chronicle_review_ticks": [300, 600, 900],
},

"10_chronicle_4faction": {
    "template":     "four_way",
    "ticks":        2000,
    "seed":         1,
    "description":  "Full chronicle test — 4 factions, 2000 ticks, chronicle review every 500 ticks",
    "use_tick_engine": True,
    "features": {
        "events": True, "factions": True, "border_friction": True,
        "recruitment": True, "adjacency_bonus": True, "oscillation": True,
        "technology": True, "diplomacy": True, "admin_revolts": True,
        "chronicle": True, "coherence_ledger": True, "naming": True,
    },
    "chronicle_review_ticks": [500, 1000, 1500, 2000],
},

"11_naming_stress": {
    "template":     "four_way",
    "ticks":        3000,
    "seed":         1,
    "description":  "Naming stress test — 4 factions, 3000 ticks, verify pool exhaustion doesn't occur",
    "use_tick_engine": True,
    "features": {
        "events": True, "factions": True, "border_friction": True,
        "recruitment": True, "adjacency_bonus": True, "oscillation": True,
        "technology": True, "diplomacy": True, "admin_revolts": True,
        "chronicle": True, "coherence_ledger": True, "naming": True,
    },
},
```

## Config Values to Add

```python
# ── Chronicle distiller (Stage 5) ─────────────────────────────────
CHRONICLE_MIN_ENTRIES              = 5     # minimum scroll entries per time jump
CHRONICLE_MAX_ENTRIES              = 10    # maximum scroll entries per time jump
SIGNIFICANCE_DELTA_SCALE           = 50.0  # delta magnitude divisor for boost calculation
SIGNIFICANCE_DELTA_CAP             = 3.0   # maximum boost from delta magnitude
SIGNIFICANCE_MISSION_REGION_BONUS  = 0.5   # context bonus for events in last mission region
SIGNIFICANCE_CHARACTER_BONUS       = 0.3   # context bonus for events with attached characters
SIGNIFICANCE_CHAIN_LENGTH_BONUS    = 0.1   # context bonus per chain link (multiplied by chain length)
CHAIN_LENGTH_CAP                   = 5     # maximum chain length counted for bonus
LINEAGE_SIGNIFICANCE_BONUS         = 0.8   # context bonus for events in lineage-occupied regions
CHARACTER_ATTACHMENT_TIER_THRESHOLD = 3     # minimum event significance tier for character attachment

# ── Coherence ledger (Stage 5) ─────────────────────────────────────
LINEAGE_FERTILITY_RATE         = 0.03   # descendants per lineage member per tick during time jumps
LINEAGE_SPREAD_PROBABILITY     = 0.1    # probability a new descendant is placed in an adjacent region
REGIONAL_COMMANDER_DEATH_PROB  = 0.3    # probability regional commander dies on conquest
NATURAL_DEATH_BASE_AGE         = 200    # tick-age at which natural death probability begins
NATURAL_DEATH_RATE             = 0.01   # per-tick death probability above base age

# ── Naming system (Stage 5) ────────────────────────────────────────
NAME_REUSE_COOLDOWN_TICKS      = 500    # ticks after death before name returns to pool
FRAGMENT_DEDUP_THRESHOLD       = 3      # minimum Levenshtein distance between fragments in same pool
NAME_DEDUP_THRESHOLD           = 3      # minimum Levenshtein distance between names in same faction
PLAYER_FACTION_SUBSET_WIDTH    = (3, 4, 4)  # (roots, patterns, tags) — wider than default
DEFAULT_FACTION_SUBSET_WIDTH   = (2, 3, 3)  # (roots, patterns, tags) — standard width

# ── Library builder (Stage 5) ──────────────────────────────────────
BUILDER_MODEL                  = "claude-sonnet-4-20250514"
BUILDER_NAME_OVERSHOOT         = 1.10   # generate 10% extra names to absorb dedup losses
BUILDER_DEDUP_LOSS_FLAG        = 0.30   # flag category if >30% lost to dedup
BUILDER_TONE_SAMPLE_SIZE       = 10     # random assembled entries to sample per category for tone check
```

## Validation Criteria

- All K1–K12 invariants pass across 3+ seeds for scenarios 09 and 10
- All existing invariants (A through J) still pass (K12 regression check)
- Library builder successfully generates and validates the full fragment library (380 fragments, all structural checks pass, dedup complete, no thin pools flagged)
- Library builder successfully generates and validates naming pools for 10 factions (10,000 names, dedup complete, no pool exhaustion)
- Chronicle Review Reports for scenario 10 reviewed by Westley across 3 seeds
- Scroll entries read as coherent prose fragments (subjective — Westley's judgment)
- Variable slot resolution produces natural-sounding text (no raw numbers, no mechanical language, no empty slots)
- Lineage clusters appear in every time jump and feel connected to the player's story
- Consequence entries accurately reflect the mission outcome
- Naming pools produce culturally coherent names within factions and audibly distinct names across factions with different variable subsets
- Schism faction names sound related-but-different from parent faction
- No naming pool exhaustion occurs in scenario 11 (3000 ticks)
- Westley signs off on the Chronicle Review Reports and the generated library content

## Done Condition

All validation criteria met. Westley signs off on:
1. The Chronicle Review Reports (prose quality across 3+ seeds)
2. The generated fragment library (read a sample, confirm quality)
3. The generated naming pools (read a sample per faction, confirm cultural coherence)
4. The final validator report (all K1–K12 invariants passing)

The library content generated during Stage 5 validation is the production library — it ships with the game. If quality is satisfactory, no regeneration is needed.
