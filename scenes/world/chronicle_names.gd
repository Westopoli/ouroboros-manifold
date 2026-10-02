extends RefCounted

# Chronicle name registry. Resolves region/faction/lineage ref ids to
# placeholder name strings using the tables from library/chronicle/fragments.json.
# Only the structural-line fallback of A73. Unowned (negative faction id) reads the
# sim's wording (csrc/chronicle.c chron_faction_name); other unknown ids render a
# safe placeholder; never crash.

const SAFE_REGION := "[region]"
const UNOWNED_FACTION := "an unclaimed people"
const SAFE_LINEAGE := "[lineage]"

var _region_names: Array = []
var _faction_names: Array = []
var _lineage_surnames: Array = []


func load_tables(name_tables: Dictionary) -> void:
	_region_names = name_tables.get("region_names", [])
	_faction_names = name_tables.get("faction_names", [])
	_lineage_surnames = name_tables.get("lineage_surnames", [])


# Replace all {slot} placeholders in text using region_id and faction_id
# from the entry's refs. Slots that cannot be resolved from refs receive
# a safe bracketed fallback.
func fill_template(text: String, region_id: int, faction_id: int) -> String:
	var out := text
	out = out.replace("{region_name}", _region_name(region_id))
	out = out.replace("{adjacent_region}", _region_name(region_id + 1))
	out = out.replace("{lineage_name}", _lineage_name(region_id))
	out = out.replace("{faction_name}", _faction_name(faction_id))
	out = out.replace("{character_name}", "[name]")
	out = out.replace("{character_rank}", "[rank]")
	out = out.replace("{duration_prose}", "[duration]")
	out = out.replace("{field_delta_summary}", "[delta]")
	out = out.replace("{mission_outcome}", "[outcome]")
	out = out.replace("{mission_region}", "[region]")
	out = out.replace("{mission_archetype}", "[mission]")
	out = out.replace("{stability_level}", "[stability]")
	out = out.replace("{tension_level}", "[tension]")
	out = out.replace("{capacity_level}", "[capacity]")
	out = out.replace("{chain_length}", "[length]")
	out = out.replace("{event_description}", "[event]")
	return out


func _region_name(region_id: int) -> String:
	if _region_names.is_empty() or region_id < 0:
		return SAFE_REGION
	return str(_region_names[region_id % _region_names.size()])


func _faction_name(faction_id: int) -> String:
	if faction_id < 0:
		return UNOWNED_FACTION
	if _faction_names.is_empty():
		return "[faction]"
	return str(_faction_names[faction_id % _faction_names.size()])


func _lineage_name(region_id: int) -> String:
	if _lineage_surnames.is_empty() or region_id < 0:
		return SAFE_LINEAGE
	return str(_lineage_surnames[region_id % _lineage_surnames.size()])
