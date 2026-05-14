extends RefCounted

var _latest_state: Dictionary = {}
var _mission_briefing: Dictionary = {}

func _init() -> void:
	SimBridge.state_updated.connect(_on_state_updated)


func _on_state_updated(state: Dictionary) -> void:
	if state.get("type") == "sim_state":
		if state.has("mission_briefing"):
			_mission_briefing = state["mission_briefing"]
	else:
		_latest_state = state


func get_all_eras() -> Array[Dictionary]:
	var settled_reach_owned: bool = SimBridge.ENTITLEMENT_SETTLED_REACH
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
			"is_owned": settled_reach_owned,
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
	return []


func create_save_slot(_era_id: String, _slot_name: String) -> Dictionary:
	return {}


func delete_save_slot(_slot_id: String) -> bool:
	return false


func get_mission_briefing(_mission_id: String) -> Dictionary:
	return _mission_briefing


func open_steam_dlc_page(era_id: String) -> void:
	# Stub — wire to Steam.activateGameOverlayToStore(<dlc_app_id>) once GodotSteam is integrated.
	print("[stub] open Steam DLC page for ", era_id)
