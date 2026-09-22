extends Control

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")
const Flow := preload("res://scenes/mockups/menus/flow.gd")
const Resolve := preload("res://scenes/mockups/menus/resolve.gd")
const BriefingScreen := preload("res://scenes/mockups/menus/screens/briefing.gd")
const TitleScreen := preload("res://scenes/mockups/menus/screens/title.gd")
const SetupScreen := preload("res://scenes/mockups/menus/screens/setup.gd")
const ResolveCardScreen := preload("res://scenes/mockups/menus/screens/resolve_card.gd")
const DebriefScreen := preload("res://scenes/mockups/menus/screens/debrief.gd")
const CampaignsScreen := preload("res://scenes/mockups/menus/screens/campaigns.gd")

const PLANTS: Array[String] = [
	"band-random",
	"briefing-two-sections",
	"difficulty-dropped",
	"flow-skips-setup",
	"four-bands",
	"digits-in-prose",
]

const FIXTURES := {
	11: "res://scenes/mockups/menus/fixtures/briefing_seed11.json",
	12: "res://scenes/mockups/menus/fixtures/briefing_seed12.json",
}
const DEFAULT_FIXTURE_SEED := 11
const DEFENSIVE_THRESHOLDS := [0.20, 0.40, 0.60, 0.80]

var _flow := Flow.new()
var _seed := DEFAULT_FIXTURE_SEED
var _fixture: Dictionary = {}
var _selected_difficulty := ""
var _resolve_result: Dictionary = {}
var _parity_override := -1.0
var _campaign_seeds: Array = []
var _regen_count := 0
var _swap_ms := 0.0

var _screens: Dictionary = {}
var _backdrop: Control
var _screens_root: Control


func _ready() -> void:
	_backdrop = get_node("Backdrop")
	_screens_root = get_node("Screens")
	_screens = {
		"title": _make_screen(TitleScreen, "Title"),
		"setup": _make_screen(SetupScreen, "Setup"),
		"briefing": _make_screen(BriefingScreen, "Briefing"),
		"resolve": _make_screen(ResolveCardScreen, "Resolve"),
		"debrief": _make_screen(DebriefScreen, "Debrief"),
		"campaigns": _make_screen(CampaignsScreen, "Campaigns"),
	}
	_load_fixture(_seed)
	_show_screen("title")


func _make_screen(script: GDScript, node_name: String) -> Control:
	var scr: Control = script.new()
	scr.name = node_name
	scr.set_anchors_preset(Control.PRESET_FULL_RECT)
	scr.root = self
	_screens_root.add_child(scr)
	return scr


func _load_fixture(n: int) -> void:
	var path: String = FIXTURES.get(n, FIXTURES[DEFAULT_FIXTURE_SEED])
	var text := FileAccess.get_file_as_string(path)
	var parsed = JSON.parse_string(text)
	_fixture = parsed if typeof(parsed) == TYPE_DICTIONARY else {}


func _force_size() -> int:
	var total := 0
	for u in _fixture.get("player_force", {}).get("units", []):
		total += int(u.get("count", 0))
	return total if total > 0 else 12


func _parity_fraction() -> float:
	if _parity_override >= 0.0:
		return _parity_override
	return float(_fixture.get("player_force", {}).get("parity_percentage", 100)) / 100.0


func _show_screen(screen_name: String) -> void:
	var t0 := Time.get_ticks_usec()
	for key in _screens.keys():
		_screens[key].visible = (key == screen_name)
	_backdrop.visible = (screen_name == "title")
	var target: Control = _screens[screen_name]
	if target.has_method("refresh"):
		target.refresh(_state_for(screen_name))
	_swap_ms = (Time.get_ticks_usec() - t0) / 1000.0


func _state_for(screen_name: String) -> Dictionary:
	if screen_name == "briefing":
		return {"fixture": _fixture}
	if screen_name == "resolve":
		return {"result": _resolve_result, "force_size": _force_size()}
	if screen_name == "debrief":
		return {"result": _resolve_result, "fixture": _fixture}
	if screen_name == "campaigns":
		return {"campaigns": _flow.campaigns}
	return {"message": _flow.message}


func qa_go(action: String) -> void:
	if action == "pick_easy" or action == "pick_medium" or action == "pick_hard":
		_selected_difficulty = action.substr(5)
		_screens.setup.select_external(_selected_difficulty)
		return

	var arg: String = _selected_difficulty if action == "begin" else ""
	var result: Dictionary = _flow.do(action, arg)
	if not result.ok:
		return

	_regen_count += 1
	if action == "new_campaign":
		_selected_difficulty = ""
	elif action == "begin":
		_campaign_seeds.append(_seed)
	elif action == "accept":
		_resolve_result = Resolve.resolve(_parity_fraction(), _flow.difficulty, _seed, DEFENSIVE_THRESHOLDS, _force_size())
		_flow.record_resolve(String(_resolve_result.get("band", "")))
	elif action == "refuse":
		_resolve_result = {}
	elif action.begins_with("resume:") and _flow.current_campaign >= 0 and _flow.current_campaign < _campaign_seeds.size():
		_seed = _campaign_seeds[_flow.current_campaign]
		_load_fixture(_seed)

	_show_screen(_flow.screen)


func qa_seed(n: int) -> void:
	_seed = n
	_load_fixture(n)
	_backdrop.qa_seed(n)
	_regen_count += 1
	_show_screen(_flow.screen)


func qa_set(name: String, value) -> void:
	if name == "parity":
		_parity_override = float(value)


func qa_plant(id: String) -> bool:
	if not PLANTS.has(id):
		return false
	QaPlants.activate(id)
	_regen_count += 1
	_show_screen(_flow.screen)
	return true


func qa_state() -> Dictionary:
	return {
		"seed": _seed,
		"hash": _compute_hash(),
		"screen": _flow.screen,
		"difficulty": _flow.difficulty,
		"campaigns": _flow.campaigns.duplicate(true),
		"briefing": _briefing_summary(),
		"resolve": _resolve_result if not _resolve_result.is_empty() else null,
		"controls": _collect_controls(),
		"timing_ms": {"swap": _swap_ms},
		"regen_count": _regen_count,
	}


func _briefing_summary() -> Dictionary:
	var c: Dictionary = BriefingScreen.compose(_fixture)
	return {
		"title": c.title,
		"sections": c.sections,
		"attacker_named": c.attacker_named,
		"has_digits": c.has_digits,
	}


func _compute_hash() -> int:
	return hash(JSON.stringify({
		"screen": _flow.screen,
		"seed": _seed,
		"difficulty": _flow.difficulty,
		"campaigns": _flow.campaigns,
		"resolve": _resolve_result,
	}))


func _collect_controls() -> Array:
	var out: Array = []
	var current: Control = _screens.get(_flow.screen)
	if current == null:
		return out
	_walk_buttons(current, out)
	return out


func _walk_buttons(node: Node, out: Array) -> void:
	for child in node.get_children():
		if child is Button and child.visible:
			out.append(String(child.text))
		_walk_buttons(child, out)
