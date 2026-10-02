# Audit: chronicle versus galaxy name agreement (origin/main, 2026-10-02)

Scope: read-only. `scenes/mockups/galaxy/` and branch `push/mockup-galaxy-scale` were not opened.

## Short answer

1. The galaxy view on main (`scenes/galaxy/galaxy_view.gd`, `galaxy_gen.gd`) has no names at all. It draws one point per region coloured by owner id and has no label, tooltip or name table. So today there is nothing to disagree with.
2. Whatever builds names for the galaxy later must read them from one place. The snapshot frame carries no names by design (`autoload/c_bridge.gd` line 8: "no positions, no names -- C5 rule"; docs/architecture.md says the same for the mission frame). The only name sources that exist are the sim chronicle's tables and a client copy of the same tables. Both are currently identical, so a galaxy that reuses the client copy agrees with the sim chronicle for region and faction names. A galaxy that invents its own table would disagree, and the sim does not send names for it to read.
3. Recommendation: either keep the one shared table (`library/chronicle/fragments.json` `name_tables`, via `scenes/world/chronicle_names.gd`) and make the galaxy use it, or add a names field to a sim frame. The first needs no contract change; the second is a frozen-contract change.

## Name sources

| Source | Location | Content |
|---|---|---|
| Sim region table | `csrc/chronicle.c` `CHRON_REGION_NAMES`, count `CHRON_N_REGION_NAMES` 528; `chron_region_name(idx)` = table[idx % 528] (line 875) | 528 distinct names |
| Sim faction table | `CHRON_FACTION_NAMES`, 18 names; `chron_faction_name(id)` = table[id % 18]; negative id returns "an unclaimed people" (line 879) | 18 |
| Sim lineage surnames | `CHRON_LINEAGE_SURNAMES`, 8; `chron_lineage_surname(region_idx)` = table[region % 8] | 8 |
| Library copy | `library/chronicle/fragments.json` `name_tables.{region_names, faction_names, lineage_surnames}` | 528, 18, 8; generated from the C pool by `scripts/library/emit_chronicle_fragments.py` |
| Client resolver | `scenes/world/chronicle_names.gd` `_region_name`, `_faction_name`, `_lineage_name`: table[id % size], negative or empty table gives "[region]" or "[faction]" | loads the JSON copy (`chronicle_scroll_panel.gd` `_ensure_fragment_library`, `mission_briefing.gd` `_marker_name_for_node`) |
| Galaxy view | `scenes/galaxy/galaxy_view.gd` | none |
| Other client name inputs | `scenes/world/time_jump_sequencer.gd` `_faction_names` dict, `region_info_panel.gd`/`faction_info_panel.gd` meta `"name"`, `autoload/sim_bridge.gd` "time_jump_start" `faction_names` | from the legacy message path (the C pipe never sends `time_jump_start`; `csrc/pipe/om_pipe.c` has 0 matches), string ids, not sim ids |

I compared the three tables programmatically: the C arrays and the JSON arrays are element-for-element identical (528 = 528, 18 = 18, 8 = 8; all 528 region names unique).

## Same id, same name?

For the sim chronicle versus the client chronicle resolver: yes for region id, faction id and lineage surname when the id is in range. Region 3 is "the Iron Vale" in both (matches the docs/architecture.md chronicle example). In practice the sim's finished `text` and `expanded_text` already carry the sim's names, and the client only resolves names itself when `text` is empty (`chronicle_scroll_panel.gd` lines 381 to 386).

For the galaxy: there is no galaxy name to compare.

## Mismatch categories (client resolver or its callers versus the sim)

| # | Category | Example | Code locations |
|---|---|---|---|
| 1 | Placeholder slot with different fill | Sim fills `{character_name}` with "<Surname> Vane" (e.g. "Voss Vane") and `{character_rank}`, `{duration_prose}`, `{mission_outcome}` etc. with real values; the client fills them with "[name]", "[rank]", "[duration]", "[outcome]" | `csrc/chronicle.c` line 1275 (and the slot builder around it); `scenes/world/chronicle_names.gd` `fill_template` lines 25 to 41 |
| 2 | `{adjacent_region}` derived differently | Sim: the region's first neighbour (`neigh[0]`, or "the neighbouring lands" when none), line 1286. Client: `_region_name(region_id + 1)`, so region 5 with neighbour 41 reads "the Garlor" in the client and region 41's name in the sim | `csrc/chronicle.c` lines 1283 to 1287; `chronicle_names.gd` line 27 |
| 3 | `{mission_region}` | Sim fills `chron_region_name(mission_region)`; client always "[region]" | `csrc/chronicle.c` line 1314; `chronicle_names.gd` line 36 |
| 4 | Unowned region | Sim says "an unclaimed people"; client says "[faction]" for faction -1 (client "[region]" for region -1 has no sim twin) | `chronicle.c` line 879; `chronicle_names.gd` line 53 |
| 5 | Mission briefing marker name | Client names the position `table[(region + node) % 528]`, a derived index, not the region's own name. The region "the Iron Vale" (id 3) with node 2 shows region 5's name. No sim frame carries the name (docs/architecture.md line 302 says the client derives it) | `scenes/mission_briefing/mission_briefing.gd` lines 888 to 898 |
| 6 | Faction id wrap | Both sides wrap at 18, but a world may have up to 64 factions (`gen_faction_count` 2 to 64, `csrc/worldgen.c` line 181; default 15). With more than 18 factions, id 18 reads "the Dominion", the same as id 0, on both sides. Agreement, but two factions share a name | `chronicle.c` line 881; `chronicle_names.gd` line 55 |
| 7 | Region id wrap | Both wrap at 528. OM_MAX_REGIONS is 512, so no collision on any real world (this is what `tests/test_region_name_table.gd` and `tests/csim/test_E09_region_name_pool.py` pin) | `chronicle.c` line 876; `chronicle_names.gd` line 49 |
| 8 | Legacy string-id name paths | Time-jump sequencer and the info panels take names from a `{faction_id: name}` dict of string ids and region meta `"name"` from the legacy message shapes, not from the sim tables. With the C pipe these dicts are empty, so the panels fall back to the id (`String(_faction_names.get(fid, fid))`) | `scenes/world/time_jump_sequencer.gd` lines 625, 636; `autoload/sim_bridge.gd` lines 262 to 273 |

None of 1 to 4 can show up in chronicle text the player reads when the sim's `text` is present; they only show on the client's fallback path (empty `text`). Category 5 is live today; categories 6 and 8 are latent.

## Does the galaxy side need the sim frame?

Not for the current contract. The two choices:

- Reuse `chronicle_names.gd` and the JSON tables: the galaxy gets the same name as the sim chronicle for the same region index and faction id (verified identical tables). No pipe change. Remaining gap is faction id above 17, where both sides repeat names, and the galaxy would need the unowned-case string ("an unclaimed people") if it prints an owner.
- Read names from a sim frame: this needs a new field on the snapshot (frozen contract, C5 says no names) and is only worth it if the tables stop being identical copies or per-world names are wanted (for example procedurally unique faction names past 18).

## Uncertainty

- `scenes/mockups/galaxy/` and `push/mockup-galaxy-scale` were deliberately not read, so I do not know whether the mockup already carries labels or its own table. If it does, adopting it would create a third table.
- I did not run the Godot client or compare rendered strings; the agreement claim rests on reading the code and a programmatic comparison of the tables, not a live frame check.
- Line numbers refer to origin/main at the time of this audit.
