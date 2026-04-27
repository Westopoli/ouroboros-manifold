# Era Naming Prompts

Prompt files for generating culturally coherent name pools across 7 launch eras. Each file is a self-contained prompt ready to paste into claude.ai using the `claude-opus-4-6` model.

## Quick Start

1. Open a prompt file (e.g., `settled_reach/player_people.txt`)
2. Copy everything below the divider line into claude.ai
3. Set the model to **Claude Opus 4.6** (not Sonnet)
4. Paste the system prompt first, then the user message
5. Save the JSON response to the path indicated in the file header

## Directory Structure

```
era_naming/
├── strategy.md              # Full strategy doc (read this first)
├── README.md                # You are here
├── era_agnostic/            # 50% pool — names that work in any era
│   └── {archetype}_{category}.txt (×16)
├── settled_reach/           # Branch 1 hallmark (far-future interstellar)
│   ├── era_style.md         # Era setting, tone, naming philosophy
│   └── {archetype}_{category}.txt (×16)
├── interplanetary/          # Branch 1 pos 2 (early spacefaring)
│   ├── era_style.md
│   └── {archetype}_{category}.txt (×16)
├── planetary_colonization/  # Branch 1 pos 1 (alien world homesteads)
│   ├── era_style.md
│   └── {archetype}_{category}.txt (×16)
├── colonial_independence/   # Branch 2 pos 1 (18th-century Atlantic)
│   ├── era_style.md
│   └── {archetype}_{category}.txt (×16)
├── ww2/                     # Branch 2 pos 2 (1939-1945)
│   ├── era_style.md
│   └── {archetype}_{category}.txt (×16)
├── 1980s/                   # Branch 2 hallmark (Cold War)
│   ├── era_style.md
│   └── {archetype}_{category}.txt (×16)
└── roman/                   # Standalone free tier (Roman Mediterranean)
    ├── era_style.md
    └── {archetype}_{category}.txt (×16)
```

## Archetypes & Categories

**4 archetypes:** player, conqueror, fortifier, opportunist
**4 categories:** people, places, units, factions

Each archetype has a distinct cultural profile (linguistic roots, phoneme patterns, flavor tags) defined in `simulation/prompts/variable_subsets.json`. Era-specific prompts layer era context on top of these profiles.

## Pool Sizes

| Category | Per faction per pool | Batch size | Batches needed |
|----------|---------------------|------------|----------------|
| People   | 250                 | 20         | 13             |
| Places   | 100                 | 20         | 5              |
| Units    | 100                 | 20         | 5              |
| Factions | 50                  | 20         | 3              |

Each prompt file generates one batch (20 names). Run multiple batches per category to reach the target pool size.

## Multi-Batch Workflow

1. Run the prompt file as-is for batch 1
2. For batch 2+: add the previous batch's output to the deduplication blocklist at the bottom of the user message:
   ```
   DEDUPLICATION BLOCKLIST — do not generate any of these exact names:
   [paste previous batch output here]
   ```
3. Repeat until you reach the target pool size
4. Run the quality filter across all batches to remove duplicates and overused components

## Quality Gate

Before full production, run the 4 test prompts first:
1. `era_agnostic/player_units.txt`
2. `settled_reach/conqueror_people.txt`
3. `roman/player_places.txt`
4. `1980s/opportunist_factions.txt`

### Pass/Fail Parameters (per batch of 20)

| Parameter | Threshold |
|-----------|-----------|
| Component reuse | No component appears more than 2× |
| Structural variety | ≥3 distinct name structures |
| Invented source ratio | 4-6 names feel genuinely invented |
| Era fit (era-specific) | Every name passes the "read aloud in-era" test |
| Category authenticity | Names feel right for their category |
| No systematic construction | No alphabetical or template patterns |
| Phonetic distinctness | No two names sound alike |

All 7 must pass. Failure triggers prompt revision before scaling.

## Assembling Output

After generating all batches for an era:
1. Collect all JSON responses per archetype × category
2. Merge name arrays, removing exact duplicates
3. Run overuse filter (no component > 5× across the full pool)
4. Format into per-era `names.json` matching the structure in `simulation/library/naming/names.json`
5. Each era gets its own file; era-agnostic names are shared across all eras
