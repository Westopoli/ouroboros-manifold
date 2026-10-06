# How an era is written

A form for whoever designs era 3 of 20 or more. Westley, 2026-10-05: "we're going to eventually have 20+ eras that are on top of the 'skeleton' we're currently building". The skeleton is shared; an era supplies the rest. Sources: the hub's "The skeleton" (`docs/bible/game_bible.md`), E-20 (R-145, R-146, R-147, S-243), E-11 (R-082-07, R-082-09, S-201), E-01 (era kind, R-001-07, R-005, R-162), `assets/eras/settled_reach/manifest.json` and `scripts/specfactory/pack_validate.py`.

## 1. What an era does not write

The simulation of civilizations, the time jump, the chronicle machinery (half of each prose and naming pool is shared), mission archetypes, the layout engine and its fairness numbers, the five layers, commands, formations, the three unit categories and their counter table, the three tiers, enemy AI, the economy's structure, the settlement generator, the landscape placement engine, the five skills, saves, lockstep and the UI. No identifier in the engine names an era, and there is no `if era ==` branch (R-145-01, R-145-02). A new era runs with zero engine changes (R-145-04).

## 2. The one choice that shapes the rest: era kind

Every era is space or ground, a formal property of the pack (E-01). The kind decides what is shared inside it:

| | Space | Ground |
|---|---|---|
| Vision | the ping, passive cross-layer sight very limited | high ground sees down, low ground cannot see up; vision units (seers, scouts) instead of a ping (R-005-12) |
| Movement | free layers, timed layer transfers | height bands, slopes, walking units, strongpoints |
| Landscape | space landscape (not yet designed, Q-166-02) | ground landscape |

Within a kind, units and rules are the same; between the two kinds they differ only in what the kind decides (R-146-02). A ground era with flying units (a world-war era) may borrow pieces of the space model for those units; that is the only exception (Westley, 2026-10-05).

## 3. The form

"Exists today" means a file or code reads it now. "Rule only" means a bible rule says the pack carries it and nothing reads it yet.

| Field an era must supply | Lives in | Decided by | Settled Reach example | Status |
|---|---|---|---|---|
| Era id (no era name inside any unit id, R-145-01) | manifest `era_id` | Westley | `settled_reach` | exists, validated |
| Display name | manifest `era_display_name` | Westley; checked against `banned_words.txt` | The Settled Reach | exists, validated |
| Accent color | manifest `era_accent_color` | Westley | `#4a9eb8` | exists, validated |
| Spatial scale | manifest `era_spatial_scale` | Westley | "placeholder: a future era played at the scale of whole regions..." | exists, validated |
| Tone | manifest `era_tone` | Westley | "Vast civilizational arcs, where individual action runs against historical momentum..." | exists, validated |
| Era order (chronology) | manifest `era_order` | Westley | `0` | exists, validated |
| Era kind (space or ground) | no manifest key yet (Q-146-04: whether it is a pack field) | Westley, 2026-10-05 | space | rule only |
| Unit models, per type per tier | manifest `units.<type>.tiers.<n>.scene`, plus `category`, `squad_count`, `visual_scale`, `facing_offset_rad` | era artist; category is E-11 | `vanguard` tier 1: `units/vanguard_t1.glb`, category `line` | exists, validated (scene paths must exist) |
| Unit types and stats (20 to 40 per era, R-082-07) | roster rows registered through `om_roster_register_custom_unit` (`csrc/unit.c`); the six built-in types are the tuning baseline | stats: Westley, balance scoring (Q-082-04) | Raider, Interceptor, Vanguard, Warden, Bombard, Bastion | six exist; 20 to 40 is rule only (Q-082-03, Q-082-05) |
| Per unit: category, role, movement kind, reach, can-ping, cost, population weight, one ability (R-082-06, R-082-09) | roster row | Westley; category from the fixed triangle | every Settled Reach type flies; Raider is Strike | category and movement exist; role, cost, population weight are rule only |
| Structures, tiered | manifest `structures` | era artist | `settlement`, three tiers, all `placeholder.glb` | exists; count is open (Q-133-01) |
| Environment objects (5 to 10) | manifest `environment` | era artist | `obstacle_small` to `obstacle_large` (asteroids), `cargo`, `derelict`, `cover_pylon`, `nav_beacon`, `hazard_volume` | exists, validated |
| Materials per tier, palette | manifest `materials` | era artist | tier 1 matte grey hull, tier 2 polished silver | exists, validated |
| Faction colors | manifest `faction_colors` | era artist | four entries, `0` to `3` | exists, validated |
| Naming pools | `naming_pools` in the manifest (checked if present); engine tables `name_tables` in `library/chronicle/fragments.json` | writer | none in the Settled Reach manifest yet | partly exists (the validator checks the key when present; whether the shipped `name_tables` are split per era is not recorded) |
| Chronicle and briefing fragments | prose pool, `library/chronicle/fragments.json` | writer | the shared pool | one shared pool exists; per-era pools are rule only (R-146-01) |
| Ability visual mappings, attack visual categories | not in the manifest | era artist | none | rule only (R-146-01) |
| Building pieces with construction stages | not in the manifest | era artist | none | rule only (R-243-01, E-18 S-237) |
| Names of the three resources and the category-to-resource mapping | not in the manifest | Westley (Q-159-08, Q-146-02) | none | rule only |
| Doctrines | not in the manifest | open (Q-243-01: pack content or engine config) | none | rule only |
| Landscape kit (landforms, palette, pieces per abstract type, borders and crossings) | kit JSON, today under `scenes/mockups/landscape/kits/` | era artist; one placement engine reads it (E-17 S-196) | `settled_reach.json`: palette, `terrain`, `city`, `borders` (wall, coast, cliff) and `nodes` | mockup only; not part of the manifest or the validator |
| Unit kit (silhouettes for the unit mockups) | `scenes/mockups/units/kits/` | era artist | `settled_reach.json` | mockup only |
| Environmental troubles of regions | not in the manifest | open (Q-146-02, E-15) | none | rule only; the space entries wait for the space landscape (R-243-02) |
| Worker model and animation | not in the manifest | era artist | none | rule only (R-243-01) |
| Per-era config: tier stat profile, restriction mask, elevation flag, reinforcement constants, fog constants | not in the manifest | Westley | none | rule only; the elevation flag is open (Q-146-03) |
| Strategic view definition | not in the manifest | Westley | none | rule only |

Two checks the validator runs today, beside the key list: every scene path exists on disk, and no unit id contains the era's own id. A missing required key fails the load with the key named; a missing optional asset uses the placeholder (R-146-03). The required keys today are `era_id`, `era_display_name`, `era_accent_color`, `era_spatial_scale`, `era_tone`, `era_order`, `units`, `structures`, `environment`, `materials`, `faction_colors`.

## 4. Fields the record does not yet name

From the 2026-10-05 era audit as the brief for this page records it (the audit's own text is not in the repo). The record has no place for these, so a designer cannot yet write them:

- **Vision model per kind.** The rules say which model each kind uses (E-01 R-005), and the era kind is not a manifest field (Q-146-04). Nothing says where a pack declares its kind or its vision units (seers, scouts) for a ground era.
- **Layout kit.** The landscape kits exist as mockup files and E-17 S-196 says each era has one, but the manifest has no `landscape_kit` entry, the validator does not check one, and nothing says how the layout engine's pieces per abstract type are named.
- **Roster by role.** E-11 says each type declares category and role and that the roster keeps invariants by role past six types (Q-082-03). No file holds roles, and no table says how many of each role an era of 20 to 40 types needs.

Also open from E-20: how many structures a pack carries (Q-133-01), which economy entries count as names and which as mechanics (Q-146-02), and the launch size of the roster (Q-082-05).
