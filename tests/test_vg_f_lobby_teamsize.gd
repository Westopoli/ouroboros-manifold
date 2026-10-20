extends SceneTree
# Rule pins: R-141-01@7d98ed, R-159-01@8f5df8, R-241-01@e3d3f6, R-241-03@4be4be, R-241-04@21e446

# Lane F part 2, piece VG-F-S241 (the lobby's team-size choice), docs/northstar/plans/2026-10-07-visible-game-spec.md
# Rev 13 "F-S241". Story S-241 "Teams, sub-commanders and sub-civilizations" (the lobby choice only; a STUB until
# R-241-03 scaling, ledger row FU-F-teamsize-scaling).
#
# Rules proved, word for word (docs/bible/epics/E-19-multiplayer.md):
#   R-141-01  "Given a match, When it starts, Then it is played by teams of 2 or 4 (S-241), and it is co-op only at
#              launch, the commanders of a team being in one civilization."
#   R-241-01  "Given the paired queue, When a team forms, Then it has 2 or 4 players, in pairs (R-159-01). Teams of 6
#              are a desired future feature (R-241-04)."
# The bible has NO rule that names the control, its default, its label, who changes it or how a guest reads it.
# Those come from the Architect's gap rulings, not from the bible: G5 (ruled 2026-10-14, round 3): a Label "Team size"
# and an OptionButton named exactly TeamSize offering 2 and 4 ONLY (item text the numeral, ids 2 and 4), default 2
# (DRAFT-team-size-default), only the host changes it (disabled for a guest, who reads the host's choice from lobby
# data key "team_size" published with set_lobby_data), Start gating UNCHANGED (_start_btn.disabled = not _hosting,
# no member-count rule), qa_state gains team_sizes = [2, 4] and team_size = the selected int. G4 (ruled (a)): the
# member cap stays 4 (MAX_MEMBERS, host_create, qa_state max_members; pins tests/test_vg_f_w4_lobby.gd:233-234 and
# plays/F/S-141.py do not move). Spec Rev 13 / 13a: the host publishes team_size on create and on every change; a lobby
# data frame emits no signal, so lobby.gd _process re-reads the keys every frame and refreshes when one changed (so
# this test never calls _refresh by hand for lobby data). The play tests/qa/desktop/plays/F/S-241.py:28-29 reads
# team_sizes == [2, 4] and finds the control named TeamSize.
#
# What this file does NOT pin because no rule or ruling states it: whether TeamSize is enabled before Host is pressed
# and before a join (G5 says only "the HOST can change it" and "disabled for a guest"); what a guest shows before the
# key arrives.
#
# Fake lobby backend: no Steam, no pipe. Own FakeBackend with lobby_id and get_lobby_data (Architect pin 5 of
# 2026-10-19; the w4 fake is not edited). Headless; the project viewport is 1920x1080 (project.godot:45-46).

const LOBBY_SCENE := "res://scenes/lobby/lobby.tscn"
const SCREEN := Rect2(0, 0, 1920, 1080)

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false
var _cur := ""


class FakeBackend extends RefCounted:
	var lobby_id := 0
	var created: Array = []
	var data := {}
	var sets: Array = []  # every set_lobby_data call, [key, value]
	var member_ids: Array = [11]
	var chats: Array = []
	var left := false
	func create_lobby(type: int, max_members: int) -> void:
		created.append([type, max_members])
	func set_lobby_data(key: String, value: String) -> void:
		sets.append([key, value])
		data[key] = value
	func get_lobby_data(key: String) -> String:
		return String(data.get(key, ""))
	func members() -> Array:
		return member_ids
	func send_chat(msg: Dictionary) -> void:
		chats.append(msg)
	func leave() -> void:
		left = true


class FakeNet extends Node:
	func drop(_peer: int) -> void:
		pass
	func on_lobby_chat(_from_peer: int, _msg: Dictionary) -> void:
		pass


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the checks did not run to the end (a script error aborted them)")
	print("\n=== VG-F S-241 Lobby Team Size Test Results ===")
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


func _run_tests() -> void:
	await _t_controls()
	await _t_state_and_node()
	await _t_host_change()
	await _t_guest()
	await _t_gating()
	await _t_refused()
	_completed = true


# --- helpers -----------------------------------------------------------------------------------------------------

func _mount(be: FakeBackend, local_id := 11) -> Node:
	var lobby: Node = (load(LOBBY_SCENE) as PackedScene).instantiate()
	var net := FakeNet.new()
	get_root().add_child(net)
	get_root().add_child(lobby)
	lobby.net_match = net
	lobby.setup({"backend": be, "local_steam_id": local_id, "version": "abc123"})
	await process_frame
	await process_frame
	return lobby


func _unmount(lobby: Node) -> void:
	var net: Node = lobby.net_match
	lobby.queue_free()
	if net != null:
		net.queue_free()
	await process_frame


# Becomes the host the way the player does: Host pressed, then the backend's lobby_created reaches the handler.
func _host(lobby: Node, be: FakeBackend) -> void:
	lobby.host_create()
	lobby._on_lobby_created(1, 4242, be)
	await process_frame
	await process_frame


# Becomes a guest the way the backend does it: lobby_joined reaches the handler with response 1 (success).
func _guest(lobby: Node, be: FakeBackend) -> void:
	lobby._on_lobby_joined(4242, 0, false, 1, be)
	await process_frame
	await process_frame


# lobby_chat_update reaches the handler: state 1 joined, 2 left (lobby.gd CHAT_LEFT_STATES).
func _members_changed(lobby: Node, be: FakeBackend, ids: Array, who: int, state: int) -> void:
	be.member_ids = ids
	lobby._on_chat_update(4242, who, who, state)
	await process_frame
	await process_frame


# The helper under test: the TeamSize control as daemon_client.find_control finds it (the last path segment).
func _team_size_node(root: Node) -> Node:
	return root.find_child("TeamSize", true, false)


func _label_with_text(root: Node, text: String) -> Label:
	if root is Label and (root as Label).text == text:
		return root as Label
	for c in root.get_children():
		var hit := _label_with_text(c, text)
		if hit != null:
			return hit
	return null


func _opt(lobby: Node) -> OptionButton:
	var n := _team_size_node(lobby)
	return n as OptionButton


func _choose(opt: OptionButton, index: int) -> void:
	opt.select(index)
	opt.item_selected.emit(index)  # the control's own signal, as a click would


func _frames() -> void:
	await process_frame
	await process_frame


func _old_keys(st: Dictionary) -> Dictionary:
	var out := {}
	for k in ["scene", "members", "max_members", "friends_only", "tick"]:
		out[k] = st.get(k)
	return out


# --- positive controls (green today) -----------------------------------------------------------------------------

func _t_controls() -> void:
	_cur = "controls"
	var be := FakeBackend.new()
	var lobby := await _mount(be)
	var st: Dictionary = lobby.qa_state()
	# C1: the lobby mounts with a FakeBackend and the existing qa_state keys keep their values.
	_assert(st.get("scene", "") == "lobby" and st.get("members", []) == [11] and st.get("max_members", 0) == 4
			and st.get("friends_only", false) == true and st.get("tick", 0) == -1,
		"CONTROL C1: qa_state keeps scene lobby, members [11], max_members 4, friends_only true, tick -1; got %s" % str(st))
	# C2: EraLine exists and names the eras.
	var era_line := lobby.find_child("EraLine", true, false) as Label
	_assert(era_line != null and era_line.text.to_lower().contains("era"),
		"CONTROL C2: EraLine exists and its text contains 'era'; got %s" % (era_line.text if era_line != null else "no node"))
	# C3: the TeamSize reader returns null on a tree with none (so a red later is the feature missing, not the helper)
	# and finds one that is there.
	var bare := VBoxContainer.new()
	bare.add_child(Label.new())
	var other := Button.new()
	other.name = "NotTeamSize"
	bare.add_child(other)
	_assert(_team_size_node(bare) == null, "CONTROL C3: the TeamSize reader returns null on a Control tree that has none")
	var planted := OptionButton.new()
	planted.name = "TeamSize"
	var wrap := HBoxContainer.new()
	wrap.add_child(planted)
	bare.add_child(wrap)
	_assert(_team_size_node(bare) == planted, "CONTROL C3: the TeamSize reader finds a node named TeamSize at any depth")
	bare.free()
	# The Label reader used for "Team size" works: the lobby's title label is found.
	_assert(_label_with_text(lobby, "MULTIPLAYER") != null, "CONTROL: the label reader finds the MULTIPLAYER title")
	# Today a lobby that is not hosting keeps StartButton disabled (lobby.gd _refresh); G5 leaves that unchanged.
	_assert((lobby.find_child("StartButton", true, false) as Button).disabled, "CONTROL: a lobby not hosting keeps StartButton disabled")
	await _unmount(lobby)


# --- T241 red until built ------------------------------------------------------------------------------------------

func _t_state_and_node() -> void:
	_cur = "state_and_node"
	var be := FakeBackend.new()
	var lobby := await _mount(be)
	var st: Dictionary = lobby.qa_state()
	_assert(st.get("team_sizes", null) == [2, 4],
		"R-141-01 / R-241-01 / G5: qa_state.team_sizes is [2, 4] in that order; got %s" % str(st.get("team_sizes", "missing")))
	_assert(typeof(st.get("team_size", null)) == TYPE_INT and st.get("team_size", 0) == 2,
		"G5: qa_state.team_size is the int 2 by default (DRAFT-team-size-default); got %s" % str(st.get("team_size", "missing")))
	_assert(_label_with_text(lobby, "Team size") != null, "G5: a Label with the text \"Team size\" is in the lobby")
	var node := _team_size_node(lobby)
	_assert(node != null, "G5: the lobby has a node named exactly TeamSize (S-241.py:29 finds it before Host is pressed)")
	var opt := node as OptionButton
	_assert(node == null or opt != null, "G5: TeamSize is an OptionButton, got %s" % (node.get_class() if node != null else "no node"))
	if opt != null:
		_assert(opt.is_visible_in_tree(), "G5: TeamSize is visible in the lobby")
		var rect := opt.get_global_rect()
		_assert(rect.size.x > 0.0 and rect.size.y > 0.0 and SCREEN.encloses(rect),
			"G5: TeamSize lies inside 1920x1080 with a non-empty rect; got %s" % str(rect))
		_assert(opt.item_count == 2, "R-141-01 / R-241-01 / G5: TeamSize offers exactly two items (2 and 4; no 1, no 3, no 6); got %d" % opt.item_count)
		if opt.item_count == 2:
			_assert(opt.get_item_id(0) == 2 and opt.get_item_id(1) == 4,
				"G5: the item ids are 2 then 4; got %d, %d" % [opt.get_item_id(0), opt.get_item_id(1)])
			_assert(opt.get_item_text(0) == "2" and opt.get_item_text(1) == "4",
				"G5: the item text is the numeral; got '%s', '%s'" % [opt.get_item_text(0), opt.get_item_text(1)])
		_assert(opt.get_selected_id() == 2 and opt.text == "2",
			"G5: the default selection is 2 and its visible text is \"2\"; got id %d text '%s'" % [opt.get_selected_id(), opt.text])
	await _unmount(lobby)


func _t_host_change() -> void:
	_cur = "host_change"
	var be := FakeBackend.new()
	var lobby := await _mount(be)
	await _host(lobby, be)
	var opt := _opt(lobby)
	_assert(opt != null, "G5: TeamSize exists in a hosting lobby")
	_assert(opt == null or not opt.disabled, "G5: only the host changes the choice, so a hosting lobby's TeamSize is enabled")
	_assert(be.data.get("team_size", "") == "2",
		"Spec Rev 13: the host publishes team_size \"2\" with set_lobby_data on create; lobby data has %s" % str(be.data.get("team_size", "none")))
	var before := _old_keys(lobby.qa_state())
	if opt != null and opt.item_count == 2:
		_choose(opt, 1)  # the item with id 4
		await _frames()
		var st: Dictionary = lobby.qa_state()
		_assert(st.get("team_size", 0) == 4, "G5: after the host picks 4, qa_state.team_size is 4; got %s" % str(st.get("team_size", "missing")))
		_assert(opt.get_selected_id() == 4 and opt.text == "4", "G5: after the pick the control's visible text is \"4\"; got '%s'" % opt.text)
		_assert(be.data.get("team_size", "") == "4" and be.sets.has(["team_size", "4"]),
			"Spec Rev 13: the host publishes team_size \"4\" on every change; lobby data has %s" % str(be.data.get("team_size", "none")))
		_assert(st.get("max_members", 0) == 4 and be.created == [[1, 4]],
			"G4: the cap stays 4 with 4 selected; max_members %s, create_lobby calls %s" % [str(st.get("max_members", "missing")), str(be.created)])
		_assert(_old_keys(st) == before, "G4/G5: choosing a team size changes nothing else in qa_state; before %s, after %s" % [str(before), str(_old_keys(st))])
		_choose(opt, 0)
		await _frames()
		_assert(lobby.qa_state().get("team_size", 0) == 2 and be.data.get("team_size", "") == "2",
			"G5: picking 2 again returns qa_state.team_size and the published key to 2; got %s / %s" % [str(lobby.qa_state().get("team_size", "missing")), str(be.data.get("team_size", "none"))])
	await _unmount(lobby)


func _t_guest() -> void:
	_cur = "guest"
	var be := FakeBackend.new()
	be.member_ids = [11, 22]
	be.data["team_size"] = "4"  # what the host published; written straight into the fake, not through the lobby
	var lobby := await _mount(be, 22)
	await _guest(lobby, be)
	var opt := _opt(lobby)
	_assert(opt != null, "G5: TeamSize exists in a guest's lobby")
	if opt != null:
		_assert(opt.disabled, "G5: for a guest TeamSize is disabled (only the host changes it)")
		_assert(opt.get_selected_id() == 4 and opt.text == "4",
			"G5: a guest's control shows the host's choice from lobby data team_size \"4\"; got id %d text '%s'" % [opt.get_selected_id(), opt.text])
	_assert(lobby.qa_state().get("team_size", 0) == 4, "G5: a guest's qa_state.team_size reads the host's 4; got %s" % str(lobby.qa_state().get("team_size", "missing")))
	_assert(not be.sets.any(func(s): return s[0] == "team_size"), "G5: a guest never publishes team_size; sets %s" % str(be.sets))
	# The host changes its choice later: a lobby data frame emits no signal, the lobby re-reads the key each frame.
	be.data["team_size"] = "2"
	await _frames()
	_assert(lobby.qa_state().get("team_size", 0) == 2 and (opt == null or opt.get_selected_id() == 2),
		"Spec Rev 13a: a guest follows the host's later change to \"2\" without a hand-called _refresh; got %s" % str(lobby.qa_state().get("team_size", "missing")))
	await _unmount(lobby)


func _t_gating() -> void:
	_cur = "gating"
	# Host with one member and with four: Start enabled in both (G5: Start gating UNCHANGED, no member-count rule).
	var be := FakeBackend.new()
	var lobby := await _mount(be)
	await _host(lobby, be)
	var start := lobby.find_child("StartButton", true, false) as Button
	_assert(not start.disabled, "G5/R-141-01: a host with one member has StartButton enabled (the gate is unchanged)")
	var opt := _opt(lobby)
	if opt != null and opt.item_count == 2:
		_choose(opt, 1)
		await _frames()
		_assert(not start.disabled, "G5: a host with one member and 4 selected still has StartButton enabled; the choice does not gate Start")
	await _members_changed(lobby, be, [11, 22, 33, 44], 44, 1)
	_assert(not start.disabled and lobby.qa_state().get("members", []) == [11, 22, 33, 44],
		"G5: a host with four members has StartButton enabled; members %s, disabled %s" % [str(lobby.qa_state().get("members", [])), str(start.disabled)])
	if opt != null and opt.item_count == 2:
		_choose(opt, 0)
		await _frames()
		_assert(not start.disabled, "G5: a host with four members and 2 selected still has StartButton enabled")
	await _unmount(lobby)
	# A guest: Start not enabled for it, as today.
	var be2 := FakeBackend.new()
	be2.member_ids = [11, 22]
	var guest := await _mount(be2, 22)
	await _guest(guest, be2)
	_assert((guest.find_child("StartButton", true, false) as Button).disabled, "G5: a guest's StartButton stays disabled, as today")
	await _unmount(guest)


func _t_refused() -> void:
	_cur = "refused"
	var be := FakeBackend.new()
	be.member_ids = [11, 22]
	be.data["team_size"] = "4"
	var lobby := await _mount(be, 22)
	await _guest(lobby, be)
	var opt := _opt(lobby)
	_assert(opt != null and opt.item_count == 2, "R-141-01 / G5: the control has exactly two items (2 and 4)")
	_assert(lobby.qa_state().get("team_size", 0) == 4, "CONTROL-for-refusal: the valid 4 is taken first; got %s" % str(lobby.qa_state().get("team_size", "missing")))
	for bad in ["1", "3", "5", "0", "6", "-2", "24", "abc"]:
		be.data["team_size"] = bad
		await _frames()
		var got = lobby.qa_state().get("team_size", null)
		_assert(got == 4 and typeof(got) == TYPE_INT,
			"R-141-01 / R-241-01 / G5: a planted team_size \"%s\" is refused and the choice stays 4; qa_state.team_size is %s" % [bad, str(got)])
		_assert(opt == null or (opt.item_count == 2 and opt.get_selected_id() == 4),
			"G5: after a planted \"%s\" the control still has two items and shows 4" % bad)
	await _unmount(lobby)
