# Era Naming Strategy

## Overview

The naming system produces culturally coherent name pools for 4 faction archetypes across 7 launch eras. Each era has two pools: **era-agnostic** (50%) and **era-specific** (50%). Era-agnostic names work in any theme pack; era-specific names are tuned to the era's setting and tone.

All generation uses `claude-opus-4-6` via manual prompt (paste into claude.ai).

## Pool Sizes

| Category | Per faction per pool | Total per faction (agnostic + specific) |
|----------|---------------------|----------------------------------------|
| People   | 250                 | 500 per era                            |
| Places   | 100                 | 200 per era                            |
| Units    | 100                 | 200 per era                            |
| Factions | 50                  | 100 per era                            |

With 4 archetypes, each era produces 1,000 people + 400 places + 400 units + 200 factions = 2,000 names total. Across 7 eras: 14,000 names.

## Batch Size

**20 names per batch.** Larger batches (the old system used 75) cause the model to exhaust creative space and fall into combinatorial construction. At 20, the model treats each name as individually crafted.

Multiple batches per category are expected. Each subsequent batch receives the previous batch's output as a **deduplication blocklist only** — not as style guidance. Creative direction comes exclusively from the prompt's exemplars and structural guidance.

## Prompt Architecture

Each prompt contains:

1. **System prompt** — universal rules, output format, anti-pattern warnings
2. **Era style block** (era-specific only) — setting, tone, naming philosophy, era-specific anti-patterns
3. **Category structural guidance** — what makes a good name in this category, with structural variety requirements
4. **Faction cultural profile** — linguistic roots, phoneme patterns, cultural flavor tags (from variable subsets)
5. **Exemplar names** — 5-8 hand-crafted names demonstrating the desired quality range
6. **Invented source instruction** — requirement that ~20-30% of names come from constructed/novel sources
7. **Deduplication blocklist** — previously generated names to avoid (no "stay consistent" framing)

## Source Diversity: Historical + Invented

Each batch must contain roughly **20-30% invented names** (4-6 out of 20). These are names that:
- Feel authentic but cannot be traced to any real-world language
- Use novel phoneme combinations or unfamiliar syllable shapes
- Could belong to a culture that never existed on Earth
- Still feel coherent with the faction's established phonetic identity

This prevents the "I recognize that as [culture X]" effect and creates genuinely alien-feeling factions while maintaining cultural coherence through shared phonetic patterns.

## Category Structural Guidance

### People
Expected structures (vary across the batch):
- Given name + family name (most common, ~50%)
- Given name + patronymic/matronymic (~20%)
- Mononym with cultural title or honorific (~15%)
- Three-part formal name (~15%)

Names should feel like real people who lived, worked, and died — not fantasy character generators.

### Places
Expected structures:
- Geographic feature + descriptor ("Druim Hollow" but better)
- Founder/explorer name + place suffix
- Functional label (station, port, crossing, seat)
- Poetic/evocative single word
- Compound indigenous-style name

Places should feel like they were named by the people who found them or built them.

### Units
Expected structures:
- Formation name from the faction's military tradition (not "fantasy-word + English military noun")
- Operational codenames that feel culturally appropriate
- Ship/vehicle class names
- Regiment/company designations that feel historical
- Named after people, places, or events in the faction's history

**Anti-pattern:** "Druim Vane", "Skarath Hold", "Cnoc Blade" — these are just faction-prefix + generic English military word. Real military units are named things like "Coldstream Guards", "Bismarck", "Operation Overlord", "The Old Contemptibles", "Praetorian Guard."

### Factions
Expected structures:
- Geographic polity names (Republic of X, X Confederation)
- Ideological movement names (The Reform League, Liberation Front)
- Dynastic/clan house names (House Vorrath, Clan Seketha)
- Cultural/ethnic identity names (The Zhemari, The Coastal Peoples)
- Institutional names (The Commerce Guild, The Admiralty Board)

Factions should feel like real political entities — the kind that appear on maps and in treaties.

## Anti-Patterns (What Went Wrong Before)

1. **Combinatorial construction** — the model generated names by systematically combining a small set of roots and suffixes. Every "Druim" got paired with every "Hold/Vane/Blade/Shore." This is immediately detectable and destroys immersion.

2. **Component reuse** — the same 15 last names appearing 8-10 times each across a pool. Maximum allowed: **2 uses of any component per batch of 20, 5 uses across the entire pool.**

3. **Gap-fill reinforcement** — feeding previously generated names as "stay consistent with this style" caused the model to lock onto existing repetitive patterns and amplify them. Now: blocklist only.

4. **Generic military nouns on units** — "Guard", "Blade", "Vane", "Hold", "Tide", "Shore", "Pike" bolted onto faction-flavored prefixes. Unit names should come from the faction's military culture, not from a bag of English weapon/fortification words.

5. **Alphabetical enumeration** — names that step through the alphabet (Aath, Baeth, Caeth). Any batch showing alphabetical progression is immediately discarded.

6. **Monoculture sourcing** — drawing 100% from one real-world linguistic tradition makes the faction feel like "reskinned [culture]" rather than its own civilization.

## Era-Specific Layer

For era-specific prompts, an additional block describes:
- The era's setting and historical/fictional context
- What names in this era *feel like* — the naming philosophy
- Era-appropriate naming constraints (what works, what doesn't)
- Era-specific exemplar names per category
- Era-specific anti-patterns (e.g., no sci-fi prefixes in Roman, no medieval titles in 1980s)

Each era has its own `era_style.md` reference document that prompt files draw from.

## Quality Gate

Before producing the full set, 4 test prompts are generated and run:
1. `era_agnostic/player_units.txt` — hardest category (was worst quality)
2. `settled_reach/conqueror_people.txt` — worst component reuse previously
3. `roman/player_places.txt` — most constrained historical era
4. `1980s/opportunist_factions.txt` — most modern era

### Pass/Fail Parameters (per batch of 20)

| Parameter | Threshold |
|-----------|-----------|
| Component reuse | No component appears more than 2× in a batch |
| Structural variety | At least 3 distinct name structures present |
| Invented source ratio | 4-6 names feel genuinely invented (not traceable) |
| Era fit (era-specific only) | Every name passes the "read aloud in-era" test |
| Category authenticity | Names feel appropriate to their category |
| No systematic construction | No alphabetical, enumerative, or template patterns |
| Phonetic distinctness | No two names sound alike when read aloud |

All 7 must pass. Any failure triggers prompt revision before scaling.

## Workflow

1. Operator pastes prompt into claude.ai (Opus model)
2. Model returns JSON: `{"names": [...]}`
3. Operator saves response to `batch_output/` as specified in prompt header
4. For subsequent batches: add previous output to dedup blocklist in the prompt
5. After all batches complete: run dedup/quality filter, assemble into per-era `names.json`

## File Organization

```
simulation/prompts/era_naming/
├── strategy.md              (this file)
├── README.md                (operator instructions)
├── era_agnostic/            (16 prompt files)
├── settled_reach/           (era_style.md + 16 prompt files)
├── interplanetary/          (era_style.md + 16 prompt files)
├── planetary_colonization/  (era_style.md + 16 prompt files)
├── colonial_independence/   (era_style.md + 16 prompt files)
├── ww2/                     (era_style.md + 16 prompt files)
├── 1980s/                   (era_style.md + 16 prompt files)
└── roman/                   (era_style.md + 16 prompt files)
```
