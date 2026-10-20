class_name TickerBeats
extends Node

# S-235 / R-235-03: the economy beats on the quiet ticker (R-104-01). Six kinds and nothing else; a shipment
# (R-235-04) and a forward base are never a beat.
# Frame source (G2 ruled (b), Architect 2026-10-14): only strongpoint_taken and strongpoint_lost are fed from frames,
# from the structures rows joined to the strongpoint ids of frame["strongpoints"] (REAL).
# STUB (G3 (a) skeleton, Architect 2026-10-14): base_occupied, fallback, expansion and weather have no frame source;
# they are proven by emit_beat() and the A8 listening path only. See also: ledger rows FU-E1m-beat-base_occupied,
# FU-E1m-beat-fallback, FU-E1m-beat-expansion, FU-E1m-beat-weather (added by the landing clerk).
# See also: scenes/tactical_c/hud/events_feed.gd:94-96, the listener (add_beat), and its skip of strongpoint ids.

signal beat(kind: String, text: String)

const KINDS := ["base_occupied", "fallback", "expansion", "weather", "strongpoint_taken", "strongpoint_lost"]
# DRAFT-e1m-beat-text: wording is a draft, ledger row DRAFT-e1m-beat-text.
const TEXTS := {
	"base_occupied": "Base occupied",
	"fallback": "Fell back to an expansion",
	"expansion": "Expansion founded",
	"weather": "Weather arriving",
	"strongpoint_taken": "Strongpoint taken",
	"strongpoint_lost": "Strongpoint lost",
}

var _owners := {}
var _primed := false
var _emitted := 0
var _last := {}


func _ready() -> void:
	name = "TickerBeats"


func emit_beat(kind: String) -> bool:
	if not (kind in KINDS):
		return false
	_emitted += 1
	_last = {"kind": kind, "text": TEXTS[kind]}
	beat.emit(kind, TEXTS[kind])
	return true


func feed(frame: Dictionary, local_faction: int) -> void:
	if not frame.has("strongpoints") or not frame.has("structures"):
		return
	var rows := {}
	for s in frame["structures"]:
		rows[int(s["id"])] = int(s["owner"])
	for p in frame["strongpoints"]:
		var id := int(p["id"])
		var now: int = rows.get(id, -1)
		var was: int = _owners.get(id, now)
		_owners[id] = now
		if not _primed:
			continue
		if was != local_faction and now == local_faction:
			emit_beat("strongpoint_taken")
		elif was == local_faction and now != local_faction:
			emit_beat("strongpoint_lost")
	_primed = true


func beats_emitted() -> int:
	return _emitted


func last_beat() -> Dictionary:
	return _last
