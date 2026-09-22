extends RefCounted

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
var message := ""


func attempt(from: String, action: String) -> Dictionary:
	return {"ok": false, "reason": "not implemented"}


func do(action: String, arg: String = "") -> Dictionary:
	return {"ok": false, "reason": "not implemented"}


func record_resolve(band: String) -> void:
	pass
