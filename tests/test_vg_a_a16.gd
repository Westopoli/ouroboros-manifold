extends SceneTree

# VG-A piece A16, the layer order control (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 12c, Lane A).
# Proves S-002, R-001-07, R-103-04, R-104-09, R-105-03 and the named draft DRAFT-a16-qe-relative
# (register row Q-A16-01 (a); Westley decides it).
#
# The bible has NO rule that names the keys Q and E or the "To layer N" buttons. What states them:
#   [W 2026-10-11] "An explicit layer select control was built in a prototype I approved" (the buttons; prototype
#     scenes/mockups/layers/layers_mockup.gd:79-100, hud.gd:13-14 and :63-64, layer_view.gd:6).
#   [DRAFT-a16-qe-relative] Q and E step the selected units one layer up or down relative to the lowest selected
#     unit's layer (the mockup's Q/E were absolute, it had two layers).
#   Architect rulings of 2026-10-12 (gaps G1..G12 of the A16 brief) for numbering, walker source, edge cases.
#
# Rules quoted word for word (method rev 3), and which test proves each:
#   R-001-07 (last clause): "Given a walking unit, When a layer order of any kind reaches it, Then nothing happens: a
#     walker has no layer selector, because at any point there is only the one layer that has ground there"
#       -> _test_walkers (the view refuses a walker-only selection and dims the buttons).
#   R-002-01: "Given a selected unit on layer 3 at a position where layer 5 is open, When the player issues a hard
#     transfer to layer 5, Then the unit begins its transition on the same tick and finishes on layer 5 after its
#     transition duration (S-004)."
#       -> _test_keys, _test_buttons, _test_match_verb (the player can issue the hard transfer: the order reaches the
#          bridge with its layer; the transition itself is the sim's and the story play's).
#   R-103-04: "Given the camera, When it moves, Then it is never bound to a layer; the layer strip changes focus, not
#     the camera."
#       -> _test_camera.
#   R-104-09: "Given the right sidebar, When read, Then it holds the layer strip and nothing else at launch"
#       -> _test_five_buttons (the buttons are part of the strip and live under LayerView).
#   R-105-03: "Given the player presses Tab, When the layer strip has focus, Then focus cycles to the next layer."
#       -> the positive control and _test_focus_key.
#
# Layer numbering (G2): the view holds engine layers 0..4 everywhere and adds 1 only in player text; the button
# labelled "To layer 3" sends engine layer 2. Walker source (G3): EraConfig.movement_kinds(); the space era is all
# flying, so the walker fixture mounts the view under the ground era (greek_placeholder, all six types walking).
#
# Interface under test (the A16 brief; fixed for the builder and for this file):
#   tactical_view.gd: qa_state()["focus_layer"]; qa_state()["last_command"] gains "layer" for kind set_layer and
#     "reason" ("walkers" | "range") on a refusal; order_layer(layer) -> bool; order_layer_step(dir) -> bool
#     (+1 Q, -1 E); send_command passes "layer" to bridge.send_unit_command; MATCH_VERBS holds "set_layer" (G12).
#   layer_view.gd: to_layer_buttons() -> Array of Button, ascending, one per layer, named "ToLayer<N>", meta "layer",
#     text "To layer <N+1>"; set_orderable(on).
#
# Tests with no bible rule and no listed brief item, written because a G-ruling states them (strike on the
# Architect's word): _test_edges (G7: range, modifiers, empty selection), _test_qa_tl (G4, S-002's visible half).
# Not written, no stated behaviour or no accessor: button geometry (G6 gives no numbers), the layer_view colour for
# engine layers 0 and 1 (FINDING-layer-view-numbering, no accessor in the interface), the settings.gd card lines (G10),
# a mixed walker and flyer selection (G7: no era has both movement kinds, so no fixture can hold one).
# RED until A16 is built: see the stated reason beside each section.

const TITLE := "VG-A A16 layer order control"
const VIEW := "res://scenes/tactical_c/tactical_view.tscn"
const SIM_SESSION := "res://autoload/sim_session.gd"
const BRIDGE := "res://autoload/c_bridge.gd"
const GROUND_ERA := "greek_placeholder"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false
var _cur := ""
var _tick := 100


# The bridge double: the real bridge (the live mission loads through it) with the unit-command call recorded whole.
class DoubleBridge extends "res://autoload/c_bridge.gd":
	var sent: Array = []

	func send_unit_command(cmd: Dictionary) -> bool:
		sent.append(cmd.duplicate())
		return true


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the checks did not run to the end (a script error aborted them)")
	print("\n=== %s Results ===" % TITLE)
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count > 0:
		print("Failures:")
		for msg in _fail_msgs:
			print("  - " + msg)
		print("=== RED ===\n")
		quit(1)
	else:
		print("=== GREEN ===\n")
		quit(0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append("[%s] %s" % [_cur, msg])


func _need(m: Object, names: Array) -> bool:
	var ok := true
	for n in names:
		if m == null or not m.has_method(n):
			_assert(false, "%s lacks method %s" % [str(m), n])
			ok = false
	return ok


# Section 2 unit object: {id,faction,type,tier,x,y,hp,layer,facing,target,state,tl?,ld?}
func _unit(id: int, faction: int, type: int, layer: int, extra: Dictionary = {}) -> Dictionary:
	var u := {"id": id, "faction": faction, "type": type, "tier": 0, "x": 1000.0 + 10.0 * id, "y": 1000.0, "hp": 100.0,
		"layer": layer, "facing": 0.0, "target": -1, "state": 0}
	u.merge(extra, true)
	return u


func _profiles() -> Array:
	var out := []
	for t in range(6):
		out.append({"type": t, "max_hp": 100.0, "range": 600.0, "interval": 10, "sensor": 800.0,
			"ability": t, "acd_max": 100, "aoe": 0.0})
	return out


func _frame(units: Array) -> Dictionary:
	var vis0 := []
	for u in units:
		vis0.append(int(u["id"]))
	_tick += 1
	return {"type": "tactical", "tick": _tick, "player_faction": 0, "units": units,
		"visible": {"0": vis0, "1": []}, "profiles": _profiles(), "events": [], "structures": [], "objectives": []}


# Own flyers (space era) or walkers (ground era), one on each of the engine layers 0..4: ids 11..15 = layers 0..4.
func _five_layers() -> Array:
	var us := []
	for l in range(5):
		us.append(_unit(11 + l, 0, 0, l))
	return us


func _key(v: Node, code: int, mods: Array = []) -> void:
	var e := InputEventKey.new()
	e.keycode = code
	e.physical_keycode = code
	e.pressed = true
	e.echo = false
	e.alt_pressed = "alt" in mods
	e.ctrl_pressed = "ctrl" in mods
	e.shift_pressed = "shift" in mods
	v.call("_unhandled_input", e)


# A fresh view on the live mission with the bridge double installed after SimSession.reset(); era "" keeps the default.
func _mount(era: String, old: Node) -> Array:
	var ec: Node = get_root().get_node("EraConfig")
	if old != null:
		old.queue_free()
		await process_frame
	var S = load(SIM_SESSION)
	S.call("reset")
	var dbl := DoubleBridge.new()
	S.set("_bridge", dbl)
	ec.call("set_era", era if era != "" else "settled_reach")
	var v: Node = (load(VIEW) as PackedScene).instantiate()
	get_root().add_child(v)
	await process_frame
	v.set_process(false)
	await process_frame
	return [v, dbl]


func _lv(v: Node) -> Node:
	return v.find_child("LayerView", true, false)


func _last(v: Node) -> Dictionary:
	return v.qa_state().get("last_command", {})


func _button_with_text(lv: Node, text: String) -> Button:
	if not lv.has_method("to_layer_buttons"):
		return null
	for b in lv.call("to_layer_buttons"):
		if (b as Button).text == text:
			return b
	return null


func _run_tests() -> void:
	var m := await _mount("", null)
	var v: Node = m[0]
	var dbl: DoubleBridge = m[1]
	var lv := _lv(v)
	if lv == null or not _need(v, ["load_frame", "qa_set_selected", "qa_state", "send_command", "_unhandled_input"]):
		return
	_assert(load(SIM_SESSION).call("bridge") == dbl, "setup: SimSession.set(\"_bridge\", double) is not what the view calls")
	_cur = "control"
	_test_control(v, lv, dbl)
	_cur = "focus"
	_test_focus_key(v, lv, dbl)
	_cur = "keys"
	_test_keys(v, lv, dbl)
	_cur = "buttons"
	_test_buttons(v, lv, dbl)
	_cur = "five"
	_test_five_buttons(v, lv)
	_cur = "camera"
	_test_camera(v, lv, dbl)
	_cur = "edges"
	_test_edges(v, lv, dbl)
	_cur = "qa_tl"
	_test_qa_tl(v)
	_cur = "match_verb"
	_test_match_verb(v)
	# Walkers: the ground era, a second view (the era is read when the order is given and when the view mounts).
	m = await _mount(GROUND_ERA, v)
	var gv: Node = m[0]
	var gdbl: DoubleBridge = m[1]
	_cur = "walkers"
	_test_walkers(gv, _lv(gv), gdbl)
	get_root().get_node("EraConfig").call("set_era", "settled_reach")
	_completed = true


# -- POSITIVE CONTROL, green today ------------------------------------------------------------------------------------

func _test_control(v: Node, lv: Node, dbl: DoubleBridge) -> void:
	_assert(_last(v).is_empty(), "control: last_command is not empty on a fresh view: %s" % str(_last(v)))
	v.load_frame(_frame(_five_layers().slice(0, 3)))  # three layers: engine 0, 1, 2
	var strip: Array = lv.call("strip_layers")
	_assert(strip == [0, 1, 2], "control: the three-layer fixture should give the strip [0, 1, 2]; got " + str(strip))
	if strip.size() < 2:
		return
	lv.call("set_focus_layer", int(strip[0]))
	_key(v, KEY_TAB)
	# R-105-03 "Given the player presses Tab, When the layer strip has focus, Then focus cycles to the next layer."
	_assert(int(lv.call("focus_layer")) == int(strip[1]), "control R-105-03: Tab should move LayerView focus from %d to %d; got %d" % [strip[0], strip[1], lv.call("focus_layer")])
	_assert(dbl.sent.is_empty(), "control: Tab sent a unit command: " + str(dbl.sent))
	# Every other kind keeps today's last_command keys (no "layer").
	v.load_frame(_frame(_five_layers()))
	v.qa_set_selected([12])
	v.send_command({"kind": "move", "unit_ids": [12], "x": 5.0, "y": 6.0})
	var lc := _last(v)
	var keys := lc.keys()
	keys.sort()
	_assert(keys == ["kind", "ok", "units", "x", "y"] and lc["kind"] == "move", "control: a move keeps last_command keys {ok, kind, units, x, y}; got " + str(lc))
	_assert(dbl.sent.size() == 1 and not dbl.sent[0].has("layer"), "control: a move dict handed to the bridge has no layer; got " + str(dbl.sent))
	dbl.sent.clear()


# -- (1) qa_state focus_layer, R-105-03 ---------------------------------------------------------------------------------
# RED because tactical_view.qa_state() has no "focus_layer" key.

func _test_focus_key(v: Node, lv: Node, dbl: DoubleBridge) -> void:
	v.load_frame(_frame(_five_layers()))
	var st: Dictionary = v.qa_state()
	_assert(st.has("focus_layer"), "(1) R-105-03: qa_state has no key \"focus_layer\" (keys: %s)" % str(st.keys()))
	lv.call("set_focus_layer", 0)
	_key(v, KEY_TAB)
	var st2: Dictionary = v.qa_state()
	_assert(st2.has("focus_layer") and int(st2["focus_layer"]) == int(lv.call("focus_layer")) and int(st2["focus_layer"]) == 1,
		"(1) R-105-03: after Tab from layer 0 qa_state focus_layer should equal LayerView.focus_layer() == 1; got %s vs %s" % [str(st2.get("focus_layer")), str(lv.call("focus_layer"))])
	_assert(dbl.sent.is_empty(), "(1) Tab sent a unit command: " + str(dbl.sent))


# -- (2) Q and E, DRAFT-a16-qe-relative, G1 G2 G7 -----------------------------------------------------------------------
# RED because tactical_view._unhandled_input has no KEY_Q / KEY_E case and no order_layer_step / order_layer.

func _sent_layer_cmd(dbl: DoubleBridge, ids: Array, layer: int, what: String) -> void:
	var c: Dictionary = dbl.sent.back() if not dbl.sent.is_empty() else {}
	_assert(not c.is_empty() and c.get("kind") == "set_layer" and c.get("unit_ids") == ids and int(c.get("layer", -99)) == layer,
		"%s: expected the bridge to get {kind: set_layer, unit_ids: %s, layer: %d}; got %s" % [what, str(ids), layer, str(c)])


func _test_keys(v: Node, _lv_unused: Node, dbl: DoubleBridge) -> void:
	v.load_frame(_frame(_five_layers()))
	# E on a flyer on engine layer 1: one layer down is 0.
	dbl.sent.clear()
	v.qa_set_selected([12])
	_key(v, KEY_E)
	_assert(dbl.sent.size() == 1, "(2) DRAFT-a16-qe-relative: E on a selected flyer should send one set_layer; the bridge got %d commands" % dbl.sent.size())
	_sent_layer_cmd(dbl, [12], 0, "(2) E on a flyer on layer 1")
	var lc := _last(v)
	_assert(lc.get("kind") == "set_layer" and lc.get("ok") == true and int(lc.get("layer", -99)) == 0 and int(lc.get("units", 0)) == 1,
		"(2) E: last_command should be {kind: set_layer, ok: true, units: 1, layer: 0}; got " + str(lc))
	# Q: one layer up.
	dbl.sent.clear()
	_key(v, KEY_Q)
	_sent_layer_cmd(dbl, [12], 2, "(2) Q on a flyer on layer 1")
	lc = _last(v)
	_assert(lc.get("kind") == "set_layer" and lc.get("ok") == true and int(lc.get("layer", -99)) == 2,
		"(2) Q: last_command should be {kind: set_layer, ok: true, layer: 2}; got " + str(lc))
	# Relative to the LOWEST selected unit's layer: ids 13, 14, 15 are on layers 2, 3, 4; Q goes to 3, E to 1.
	dbl.sent.clear()
	v.qa_set_selected([15, 13, 14])
	_key(v, KEY_Q)
	_assert(dbl.sent.size() == 1, "(2) a group is one command; the bridge got %d" % dbl.sent.size())
	var c: Dictionary = dbl.sent.back() if not dbl.sent.is_empty() else {}
	var ids: Array = c.get("unit_ids", [])
	ids = ids.duplicate()
	ids.sort()
	_assert(c.get("kind") == "set_layer" and ids == [13, 14, 15] and int(c.get("layer", -99)) == 3,
		"(2) Q with units on layers 2, 3, 4 should send every selected id with layer 3 (lowest + 1); got " + str(c))
	dbl.sent.clear()
	_key(v, KEY_E)
	c = dbl.sent.back() if not dbl.sent.is_empty() else {}
	_assert(c.get("kind") == "set_layer" and int(c.get("layer", -99)) == 1,
		"(2) E with units on layers 2, 3, 4 should send layer 1 (lowest - 1); got " + str(c))
	# The one entry, direct: order_layer(n) with the order's own spec text.
	dbl.sent.clear()
	v.qa_set_selected([11])
	var r = v.call("order_layer", 3) if v.has_method("order_layer") else null
	_assert(v.has_method("order_layer") and r == true, "(2) order_layer(3) should return true for a selected flyer; got " + str(r))
	_sent_layer_cmd(dbl, [11], 3, "(2) order_layer(3)")
	# send_command itself carries the layer (today the dicts drop it).
	dbl.sent.clear()
	v.send_command({"kind": "set_layer", "unit_ids": [11], "layer": 4})
	_sent_layer_cmd(dbl, [11], 4, "(2) send_command({kind: set_layer, layer: 4})")
	_assert(int(_last(v).get("layer", -99)) == 4, "(2) send_command: last_command should carry layer 4; got " + str(_last(v)))
	dbl.sent.clear()


# -- (3) the "To layer N" buttons, [W 2026-10-11], G2 G6 ---------------------------------------------------------------
# RED because layer_view.gd has no to_layer_buttons().

func _test_buttons(v: Node, lv: Node, dbl: DoubleBridge) -> void:
	v.load_frame(_frame(_five_layers()))
	v.qa_set_selected([12])
	dbl.sent.clear()
	if not _need(lv, ["to_layer_buttons", "set_orderable"]):
		return
	var bs: Array = lv.call("to_layer_buttons")
	var b3 := _button_with_text(lv, "To layer 3")
	_assert(b3 != null, "(3) no button with text \"To layer 3\"; texts: " + str(bs.map(func(b): return (b as Button).text)))
	if b3 == null:
		return
	_assert(b3.name == &"ToLayer2" and int(b3.get_meta("layer", -99)) == 2,
		"(3) G2: the button labelled 3 is engine layer 2: name ToLayer2, meta layer 2; got name %s meta %s" % [b3.name, str(b3.get_meta("layer", null))])
	_assert(not b3.disabled, "(3) with a flyer selected the button is enabled")
	b3.pressed.emit()
	_assert(dbl.sent.size() == 1, "(3) pressing \"To layer 3\" should send one command; the bridge got %d" % dbl.sent.size())
	_sent_layer_cmd(dbl, [12], 2, "(3) \"To layer 3\" sends engine 2")
	var lc := _last(v)
	_assert(lc.get("kind") == "set_layer" and lc.get("ok") == true and int(lc.get("layer", -99)) == 2,
		"(3) last_command after the button: {kind: set_layer, ok: true, layer: 2}; got " + str(lc))
	# Ascending by layer, text "To layer N" with N = engine + 1.
	var texts := []
	for b in bs:
		texts.append((b as Button).text)
	_assert(texts == ["To layer 1", "To layer 2", "To layer 3", "To layer 4", "To layer 5"], "(3) G6: button texts ascending \"To layer 1\" .. \"To layer 5\"; got " + str(texts))
	# R-104-09: the buttons are part of the strip (under LayerView), never direct children of the view root.
	var stray := bs.filter(func(b): return (b as Node).get_parent() == v)
	_assert(stray.is_empty(), "(3) R-104-09: To-layer buttons are direct children of the view root (pins on child count)")
	_assert(bs.all(func(b): return lv.is_ancestor_of(b)), "(3) R-104-09: every To-layer button lives under LayerView")
	dbl.sent.clear()


# -- (5) five buttons when the strip has five layers, G5, R-104-09 -------------------------------------------------------
# RED because layer_view.gd has no to_layer_buttons().

func _test_five_buttons(v: Node, lv: Node) -> void:
	v.load_frame(_frame(_five_layers()))
	var st: Dictionary = v.qa_state()
	_assert(int(st["inventory"]["hud"]["strip"]) == 5, "(5) control: five occupied layers give inventory.hud.strip == 5; got " + str(st["inventory"]["hud"]["strip"]))
	_assert(lv.has_method("to_layer_buttons") and lv.call("to_layer_buttons").size() == 5, "(5) R-104-09 / G5: to_layer_buttons().size() should be 5; layer_view has no to_layer_buttons()" if not lv.has_method("to_layer_buttons") else "(5) to_layer_buttons().size() should be 5; got %d" % lv.call("to_layer_buttons").size())
	# G5: all five layers get a button always, also when the strip shows fewer (transfer to an empty layer is the point).
	v.load_frame(_frame(_five_layers().slice(0, 3)))
	_assert(int(v.qa_state()["inventory"]["hud"]["strip"]) == 3, "(5) control: three occupied layers give strip == 3")
	_assert(lv.has_method("to_layer_buttons") and lv.call("to_layer_buttons").size() == 5, "(5) G5: five buttons also with three occupied layers")


# -- (6) R-103-04: the strip changes focus, not the camera ---------------------------------------------------------------
# The Tab half is green today (the control that the camera does not move); the button half is RED with (3).

func _test_camera(v: Node, lv: Node, dbl: DoubleBridge) -> void:
	v.load_frame(_frame(_five_layers()))
	v.qa_set_selected([12])
	var before: Dictionary = v.qa_state()["camera"]
	lv.call("set_focus_layer", 0)
	_key(v, KEY_TAB)
	_assert(int(lv.call("focus_layer")) == 1, "(6) setup: Tab changed focus 0 -> 1")
	var after: Dictionary = v.qa_state()["camera"]
	_assert(before == after, "(6) R-103-04: Tab moved the camera from %s to %s" % [str(before), str(after)])
	var b := _button_with_text(lv, "To layer 4")
	_assert(b != null, "(6) R-103-04: no \"To layer 4\" button to press (layer_view has no to_layer_buttons())")
	if b != null:
		b.pressed.emit()
		var after2: Dictionary = v.qa_state()["camera"]
		_assert(before == after2, "(6) R-103-04: a To-layer button press moved the camera from %s to %s" % [str(before), str(after2)])
	_key(v, KEY_Q)
	_assert(before == v.qa_state()["camera"], "(6) R-103-04: Q moved the camera")
	dbl.sent.clear()


# -- (4) walkers, R-001-07, G3 --------------------------------------------------------------------------------------------
# RED because tactical_view has no walker check (no order_layer / reason \"walkers\") and layer_view no set_orderable.

func _test_walkers(v: Node, lv: Node, dbl: DoubleBridge) -> void:
	var ec: Node = get_root().get_node("EraConfig")
	var mk: Array = ec.call("movement_kinds")
	var all_walk := true
	for i in range(1, mk.size(), 2):
		all_walk = all_walk and int(mk[i]) == 1
	_assert(ec.call("kind") != "space" and all_walk, "(4) setup G3: EraConfig.movement_kinds() under %s should be all walking; kind %s kinds %s" % [GROUND_ERA, str(ec.call("kind")), str(mk)])
	_assert(load(SIM_SESSION).call("bridge") == dbl, "(4) setup: the double is not the session bridge")
	if lv == null:
		return
	var ws := []
	for l in range(2):
		ws.append(_unit(21 + l, 0, 2, l))  # type 2 = vanguard, walking under the ground era
	ws.append(_unit(23, 0, 3, 0))
	v.load_frame(_frame(ws))
	v.qa_set_selected([21, 22, 23])
	dbl.sent.clear()
	_key(v, KEY_Q)
	_assert(dbl.sent.is_empty(), "(4) R-001-07: Q with walkers selected reached the bridge: " + str(dbl.sent))
	var lc := _last(v)
	_assert(lc.get("ok") == false and lc.get("kind") == "set_layer" and lc.get("reason") == "walkers" and int(lc.get("units", -1)) == 3 and int(lc.get("layer", -99)) == 1,
		"(4) R-001-07: last_command should be {ok: false, kind: set_layer, units: 3, layer: 1, reason: walkers}; got " + str(lc))
	var lck := lc.keys()
	lck.sort()
	_assert(lck == ["kind", "layer", "ok", "reason", "units", "x", "y"], "(4) the refusal's keys are {ok, kind, units, x, y, layer, reason}; got " + str(lck))
	var r = v.call("order_layer", 3) if v.has_method("order_layer") else null
	_assert(r == false and dbl.sent.is_empty(), "(4) R-001-07: order_layer(3) on walkers should return false and not call the bridge; got %s, sent %s" % [str(r), str(dbl.sent)])
	if not _need(lv, ["to_layer_buttons", "set_orderable"]):
		return
	var bs: Array = lv.call("to_layer_buttons")
	_assert(bs.size() == 5 and bs.all(func(b): return (b as Button).disabled),
		"(4) R-001-07: with only walkers selected every To-layer button is disabled; got %s" % str(bs.map(func(b): return (b as Button).disabled)))


# -- G7 edges (no bible rule; strike on the Architect's word) ---------------------------------------------------------------
# RED because the keys are not bound.

func _test_edges(v: Node, lv: Node, dbl: DoubleBridge) -> void:
	v.load_frame(_frame(_five_layers()))
	dbl.sent.clear()
	# Q at engine layer 4, E at engine layer 0: no send, ok false, reason range.
	v.qa_set_selected([15])
	_key(v, KEY_Q)
	var lc := _last(v)
	_assert(dbl.sent.is_empty() and lc.get("ok") == false and lc.get("reason") == "range",
		"(7) G7: Q at engine layer 4 should send nothing and set last_command {ok: false, reason: range}; sent %s, last_command %s" % [str(dbl.sent), str(lc)])
	v.qa_set_selected([11])
	_key(v, KEY_E)
	lc = _last(v)
	_assert(dbl.sent.is_empty() and lc.get("ok") == false and lc.get("reason") == "range",
		"(7) G7: E at engine layer 0 should send nothing and set last_command {ok: false, reason: range}; sent %s, last_command %s" % [str(dbl.sent), str(lc)])
	# Any modifier held: Q and E do nothing (Alt+N is narrowing's).
	v.qa_set_selected([12])
	var before := _last(v)
	for mod in ["alt", "ctrl", "shift"]:
		_key(v, KEY_Q, [mod])
		_key(v, KEY_E, [mod])
	_assert(dbl.sent.is_empty() and _last(v) == before, "(7) G7: Q/E with Alt, Ctrl or Shift held should do nothing; sent %s, last_command %s" % [str(dbl.sent), str(_last(v))])
	# Empty selection: nothing, last_command untouched. Control first: the same key with a selection does send.
	v.qa_set_selected([])
	var before_e := _last(v)
	_key(v, KEY_Q)
	_assert(dbl.sent.is_empty() and _last(v) == before_e, "(7) G7: an empty selection does nothing; sent %s, last_command %s" % [str(dbl.sent), str(_last(v))])
	v.qa_set_selected([12])
	_key(v, KEY_Q)
	_assert(dbl.sent.size() == 1, "(7) control for the empty-selection check: the same Q with a flyer selected sends one command; got %d (the keys are not bound)" % dbl.sent.size())
	dbl.sent.clear()


# -- G4: qa_state units carry tl and ld (the story play asserts state & 4 and tl) --------------------------------------------
# RED because tactical_view.qa_state() builds unit entries without tl and ld.

func _test_qa_tl(v: Node) -> void:
	var us := _five_layers()
	us.append(_unit(31, 0, 0, 0, {"state": 4, "tl": 1, "ld": 130}))
	v.load_frame(_frame(us))
	var ents: Dictionary = v.qa_state()["units"]
	var e: Dictionary = ents.get("31", {})
	_assert(int(e.get("state", 0)) & 4 == 4, "(8) control: qa_state keeps state bit 4 for the unit in transfer; got " + str(e))
	_assert(e.has("tl") and int(e["tl"]) == 1 and e.has("ld") and int(e["ld"]) == 130, "(8) G4: the unit entry in transfer should carry tl 1 and ld 130; got " + str(e))
	_assert(not (ents.get("11", {}) as Dictionary).has("tl"), "(8) G4: a unit whose frame object omits tl has no tl key; got " + str(ents.get("11")))


# -- G12: the set_layer verb passes the match filter -----------------------------------------------------------------------------
# RED because MATCH_VERBS is {move, attack_move, attack_target}.

func _test_match_verb(v: Node) -> void:
	var consts: Dictionary = v.get_script().get_script_constant_map()
	var mv = consts.get("MATCH_VERBS")
	_assert(mv is Dictionary, "(9) control: tactical_view has a MATCH_VERBS dictionary (_send_match_command's filter)")
	if mv is Dictionary:
		_assert((mv as Dictionary).has("move"), "(9) control: MATCH_VERBS holds move")
		_assert((mv as Dictionary).has("set_layer"), "(9) G12 / R-002-01: MATCH_VERBS lacks \"set_layer\", so in a match _send_match_command refuses the hard transfer; keys: " + str((mv as Dictionary).keys()))
