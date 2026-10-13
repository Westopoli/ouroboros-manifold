extends Control

# S-104 / R-104-01: the quiet ticker, four beats (structure captured, structure lost, objective threshold,
# force routed). Force routed has no sim source yet, so it is absent. R-104-02 banner 4 s, R-104-03 clock.
# TickerBeats (lane E1m) feeds more beats through add_beat(); it connects to its "beat" signal when the node exists.

const BANNER_S := 4.0
const THRESHOLDS := [0.25, 0.5, 0.75, 1.0]
const TICKS_PER_S := 20
const MAX_LINES := 6

var _lines: Array = []
var _banner := ""
var _banner_left := 0.0
var _owners := {}
var _progress := {}
var _label: Label
var _banner_label: Label
var _ticker: Node


func _ready() -> void:
	name = "Events"
	_label = Label.new()
	add_child(_label)
	_banner_label = Label.new()
	_banner_label.position = Vector2(0, -40)
	add_child(_banner_label)


func feed(frame: Dictionary, local_faction: int) -> void:
	_connect_ticker()
	if frame.has("structures"):
		for s in frame["structures"]:
			_owners[int(s["id"])] = int(s["owner"])
	if frame.has("structures_changed"):
		for s in frame["structures_changed"]:
			var id := int(s["id"])
			var now := int(s["owner"])
			var was: int = _owners.get(id, now)
			_owners[id] = now
			if was != local_faction and now == local_faction:
				add_beat("captured", "Structure captured")
			elif was == local_faction and now != local_faction:
				add_beat("lost", "Structure lost")
	if frame.has("objectives"):
		for o in frame["objectives"]:
			var i := int(o["i"])
			var p := float(o["progress"])
			if frame.get("type", "") != "tactical_delta" and not _progress.has(i):
				_progress[i] = p
				continue
			var prev: float = _progress.get(i, 0.0)
			_progress[i] = p
			for t in THRESHOLDS:
				if prev < t and p >= t:
					add_beat("objective", "Objective %d%%" % int(round(t * 100.0)))


func add_beat(kind: String, text: String) -> void:
	_lines.append({"kind": kind, "text": text})
	while _lines.size() > MAX_LINES:
		_lines.pop_front()
	_banner = text
	_banner_left = BANNER_S
	_refresh()


func lines() -> Array:
	return _lines


func banner() -> String:
	return _banner


func advance(dt_s: float) -> void:
	if _banner_left <= 0.0:
		return
	_banner_left -= dt_s
	if _banner_left <= 0.0:
		_banner = ""
		_refresh()


func clock_text(tick: int) -> String:
	var s := int(tick / TICKS_PER_S)
	return "%02d:%02d" % [s / 60, s % 60]


func _connect_ticker() -> void:
	if _ticker != null or not is_inside_tree():
		return
	_ticker = get_tree().root.find_child("TickerBeats", true, false)
	if _ticker != null and _ticker.has_signal("beat"):
		_ticker.connect("beat", add_beat)


func _refresh() -> void:
	if _label == null:
		return
	var t := ""
	for l in _lines:
		t += String(l["text"]) + "\n"
	_label.text = t
	_banner_label.text = _banner
