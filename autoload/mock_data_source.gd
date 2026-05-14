extends RefCounted

var _save_slots: Array[Dictionary] = []

func _init() -> void:
	_save_slots = [
		{
			"id": "slot_001",
			"name": "Roman",
			"era_id": "roman",
			"era_name": "Roman",
			"chapter": 3,
			"generation": 7,
			"playtime_seconds": 14520,
			"last_played_timestamp": "2026-04-05T14:30:00Z",
			"era_accent_color": "#c9a84c"
		},
		{
			"id": "slot_002",
			"name": "1980s",
			"era_id": "1980s",
			"era_name": "1980s",
			"chapter": 1,
			"generation": 2,
			"playtime_seconds": 4500,
			"last_played_timestamp": "2026-04-07T09:15:00Z",
			"era_accent_color": "#8b9a3c"
		},
	]


func get_all_eras() -> Array[Dictionary]:
	return [
		{
			"id": "roman",
			"name": "Roman",
			"description": "Command the legions of a civilization that conquered the known world. Ground-only warfare across sun-baked provinces — no layers, no air support, just steel and discipline.",
			"accent_color": "#c9a84c",
			"is_owned": false,
			"tier_progress": {"current_tier": 2, "progress_to_next": 0.45, "max_tier_unlocked": 2},
			"mastery_progress": 0.12,
			"unit_roster": [
				{"abstract_type": "vanguard", "display_name": "Legionary", "category": "line", "tier": 1, "role_description": "Disciplined frontline infantry. The backbone of the legion."},
				{"abstract_type": "warden", "display_name": "Medicus", "category": "line", "tier": 1, "role_description": "Field surgeon who stabilizes nearby units under fire."},
				{"abstract_type": "raider", "display_name": "Velites", "category": "strike", "tier": 1, "role_description": "Fast flanking skirmishers with javelin harassment."},
				{"abstract_type": "interceptor", "display_name": "Equites", "category": "strike", "tier": 2, "role_description": "Mounted cavalry for rapid encirclement and pursuit."},
				{"abstract_type": "bombard", "display_name": "Onager", "category": "siege", "tier": 2, "role_description": "Stone-throwing siege engine. Devastating against fortifications."},
				{"abstract_type": "bastion", "display_name": "Testudo", "category": "siege", "tier": 3, "role_description": "Mobile shield formation. Absorbs punishment while advancing."},
			],
			"sample_chronicle_text": "In the autumn of the third year, the Confederation pressed south through the mountain passes. Consul Lucius Aurelius — seventh of his line — ordered the garrison to hold the river crossing at any cost. The legionaries dug in along the northern bank and waited for the dust clouds on the horizon to resolve into spears."
		},
		{
			"id": "settled_reach",
			"name": "Settled Reach",
			"description": "Far-future conflict across the void. Full 2.5D layer combat — orbital stations, surface strongholds, and deep-space engagements. The premium sci-fi experience.",
			"accent_color": "#4a9eb8",
			"is_owned": SimBridge.ENTITLEMENT_SETTLED_REACH,
			"tier_progress": {"current_tier": 1, "progress_to_next": 0.0, "max_tier_unlocked": 1},
			"mastery_progress": 0.0,
			"unit_roster": [
				{"abstract_type": "vanguard", "display_name": "Lancer", "category": "line", "tier": 1, "role_description": "Standard-issue assault infantry with kinetic rifles."},
				{"abstract_type": "warden", "display_name": "Apothecary", "category": "line", "tier": 1, "role_description": "Combat medic with nano-restoration field."},
				{"abstract_type": "raider", "display_name": "Wraith", "category": "strike", "tier": 1, "role_description": "Cloaked infiltrator. Disables systems before the assault."},
				{"abstract_type": "interceptor", "display_name": "Seraph", "category": "strike", "tier": 2, "role_description": "Atmospheric fighter. Dominates the air layer."},
				{"abstract_type": "bombard", "display_name": "Basilisk", "category": "siege", "tier": 2, "role_description": "Long-range plasma artillery platform."},
				{"abstract_type": "bastion", "display_name": "Aegis", "category": "siege", "tier": 3, "role_description": "Heavy shield generator. Protects surrounding units."},
			],
			"sample_chronicle_text": "The beacon at Thalassa Relay went dark on the forty-eighth cycle. When the survey corvette arrived, the station was intact — power flowing, atmo nominal — but every console displayed the same message, repeating: THEY REMEMBER WHAT WE BUILT. The Admiralty recalled all frontier patrols within the hour."
		},
		{
			"id": "1980s",
			"name": "1980s",
			"description": "Cold War gone hot. Submarines stalk the deep layers, destroyers command the surface, and aircraft dominate the sky. The definitive showcase for 2.5D vertical combat.",
			"accent_color": "#8b9a3c",
			"is_owned": false,
			"tier_progress": {"current_tier": 1, "progress_to_next": 0.15, "max_tier_unlocked": 1},
			"mastery_progress": 0.03,
			"unit_roster": [
				{"abstract_type": "vanguard", "display_name": "Destroyer", "category": "line", "tier": 1, "role_description": "Multi-role surface combatant. Anti-sub and anti-surface."},
				{"abstract_type": "warden", "display_name": "Tender", "category": "line", "tier": 1, "role_description": "Support vessel. Repairs and resupplies nearby ships."},
				{"abstract_type": "raider", "display_name": "Fast Attack Craft", "category": "strike", "tier": 1, "role_description": "Small, fast torpedo boat for hit-and-run raids."},
				{"abstract_type": "interceptor", "display_name": "F-14 Tomcat", "category": "strike", "tier": 2, "role_description": "Air superiority fighter. Controls the sky layer."},
				{"abstract_type": "bombard", "display_name": "Iowa-class", "category": "siege", "tier": 2, "role_description": "Battleship with 16-inch guns. Devastating shore bombardment."},
				{"abstract_type": "bastion", "display_name": "Typhoon-class", "category": "siege", "tier": 3, "role_description": "Ballistic missile submarine. The deep-layer fortress."},
			],
			"sample_chronicle_text": "The sonar contact appeared at 0347, bearing two-seven-zero, depth four hundred meters and descending. Captain Hargrove studied the waterfall display for eleven seconds before speaking. 'That's not one of ours.' The crew of the USS Tallahassee had trained for this moment for three years. None of them had believed it would actually come."
		},
	]


func get_era_detail(era_id: String) -> Dictionary:
	for era in get_all_eras():
		if era["id"] == era_id:
			return era
	return {}


func is_era_accessible(era_id: String) -> bool:
	var era := get_era_detail(era_id)
	if era.is_empty():
		return false
	return era["is_owned"]


func get_save_slots() -> Array[Dictionary]:
	return _save_slots


func create_save_slot(era_id: String, slot_name: String) -> Dictionary:
	var safe_name := InputSanitizer.sanitize(slot_name, "save_name")
	var era := get_era_detail(era_id)
	if safe_name == "":
		safe_name = era.get("name", era_id)
	var slot := {
		"id": "slot_%03d" % (_save_slots.size() + 1),
		"name": safe_name,
		"era_id": era_id,
		"era_name": era.get("name", era_id),
		"chapter": 1,
		"generation": 1,
		"playtime_seconds": 0,
		"last_played_timestamp": Time.get_datetime_string_from_system(true),
		"era_accent_color": era.get("accent_color", "#888888"),
	}
	_save_slots.push_back(slot)
	return slot


func delete_save_slot(slot_id: String) -> bool:
	for i in range(_save_slots.size()):
		if _save_slots[i]["id"] == slot_id:
			_save_slots.remove_at(i)
			return true
	return false


func get_mission_briefing(_mission_id: String) -> Dictionary:
	return {
		"mission_id_label": "OP-2741",
		"chapter": 3,
		"generation": 7,
		"era_id": "roman",
		"mission_title": "The Siege of Thessalonica",
		"mission_subtitle": "A Fortifier pushes south with overwhelming force",
		"tick_counter": 48205,
		"situation_text": "The {accent}Northern Confederation{/accent} has marshaled {strong}42{/strong} companies along the Thessalonica frontier over the past {strong}1,200{/strong} ticks. Intelligence reports confirm a {accent}Fortifier{/accent}-archetype commander directing the buildup \u2014 defensive posture with rare but devastating committed assaults. Regional military readiness has declined to {strong}28{/strong} following last generation's losses at Naissus. Your predecessor, {accent}Marcus Aurelius{/accent}, fell holding the northern approach. The Confederation appears to be testing whether the new commander has the same resolve.",
		"objective_primary": {
			"text": "Hold the southern wall until reinforcements arrive.",
			"archetype": "Rear Guard",
			"success_spectrum_label": "EXTRACTION UNDER FIRE"
		},
		"objectives_secondary": [
			{"text": "Preserve the garrison supply depot.", "weight_label": "SECONDARY"},
		],
		"enemy_assessment": {
			"faction_name": "Northern Confederation",
			"archetype_label": "FORTIFIER",
			"military_stat": 72,
			"military_stat_max": 100,
			"tech_tier": 2,
			"behavior_tag": "DEFENSIVE POSTURE \u2014 RARE COMMITTED ATTACK"
		},
		"player_force": {
			"parity_percentage": 85,
			"units": [
				{"type_abstract": "vanguard", "type_display_name": "Legionary", "category": "line", "count": 4},
				{"type_abstract": "warden", "type_display_name": "Medicus", "category": "line", "count": 2},
				{"type_abstract": "raider", "type_display_name": "Velites", "category": "strike", "count": 3},
				{"type_abstract": "interceptor", "type_display_name": "Equites", "category": "strike", "count": 2},
				{"type_abstract": "bombard", "type_display_name": "Onager", "category": "siege", "count": 1},
				{"type_abstract": "bastion", "type_display_name": "Testudo", "category": "siege", "count": 1},
			]
		},
		"region_state": {
			"name": "Thessalonica",
			"tier": "Frontier",
			"economy": {"value": 45, "max": 100},
			"military": {"value": 28, "max": 100},
			"tension": {"value": 67, "max": 100}
		},
		"commander_lineage": {
			"name": "Lucius Aurelius",
			"generation_number": 7,
			"predecessor_name": "Marcus Aurelius",
			"predecessor_status": "KIA \u2014 Naissus"
		},
		"reinforcement_note": "Local military infrastructure degraded \u2014 expect sparse reinforcements from regional garrisons."
	}


func open_steam_dlc_page(era_id: String) -> void:
	# Stub — mock mode shows a placeholder modal via era_detail.gd. No-op here.
	print("[stub-mock] open Steam DLC page for ", era_id)
