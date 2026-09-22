extends RefCounted

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const EDGES := {
	"title": {"new_campaign": "setup", "continue": "campaigns", "quit": "title"},
	"campaigns": {"back": "title", "resume": "briefing"},
	"setup": {"begin": "briefing", "back": "title"},
	"briefing": {"accept": "resolve", "refuse": "title"},
	"resolve": {"resolve_continue": "debrief"},
	"debrief": {"proceed": "title"},
}

var screen := "title"
var difficulty := ""
var campaigns: Array = []
var current_campaign := -1
var quit_requested := false
var message := ""


func attempt(from: String, action: String) -> Dictionary:
	var key: String = "resume" if action.begins_with("resume:") else action
	var table: Dictionary = EDGES.get(from, {})
	if not table.has(key):
		return {"ok": false, "reason": "no edge from %s via %s" % [from, action]}
	var to: String = table[key]
	if action == "new_campaign" and QaPlants.is_active("flow-skips-setup"):
		to = "briefing"
	return {"ok": true, "to": to}


func do(action: String, arg: String = "") -> Dictionary:
	var result: Dictionary = attempt(screen, action)
	if not result.ok:
		return result
	message = ""
	if action == "quit":
		quit_requested = true
		message = "would quit"
	elif action == "begin":
		var chosen: String = "medium" if QaPlants.is_active("difficulty-dropped") else arg
		difficulty = chosen
		campaigns.append({"name": "Campaign %d" % (campaigns.size() + 1), "difficulty": chosen, "chapter": 1, "last_band": ""})
		current_campaign = campaigns.size() - 1
	elif action == "refuse":
		message = "orders refused; the chapter passes"
		if current_campaign >= 0:
			campaigns[current_campaign].chapter += 1
	elif action.begins_with("resume:"):
		var name: String = action.substr(7)
		for i in range(campaigns.size()):
			if campaigns[i].name == name:
				current_campaign = i
				difficulty = campaigns[i].difficulty
				break
	screen = result.to
	return result


func record_resolve(band: String) -> void:
	if current_campaign >= 0:
		campaigns[current_campaign].chapter += 1
		campaigns[current_campaign].last_band = band
