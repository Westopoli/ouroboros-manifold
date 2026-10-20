extends SceneTree
# Rule pins: R-143-01@e507dd, R-143-03@f98569, R-144-03@82524f, R-147-01@e12fb4, R-149-01@356d5b

# Lane F part 2, piece VG-F-S143 (the lobby's common era set), docs/northstar/plans/2026-10-07-visible-game-spec.md
# Rev 13 "F-S143". Story S-143 "Eras in sequence".
#
# Rules proved, word for word (docs/bible/epics/E-19-multiplayer.md):
#   R-143-01  "Given a lobby, When era packs are compared, Then the match may traverse only eras every peer owns, in
#              chronological order."
#   R-143-03  "Given a peer lacks a pack, When the lobby forms, Then the match is limited to the common set and the
#              lobby says so; once a universe is locked, R-144-03 governs instead."
# Where the first build has two eras (docs/bible/epics/E-20 R-147-01 "the first build ... contains exactly two, one in
# space and one on land ... chronologically ordered" and R-149-01 "the first build starts with two eras, one in
# space and one on land (S-147)"), the narrowing cases give the host two era ids (settled_reach, greek_placeholder,
# assets/eras/*/manifest.json era_order 0 and 1) through the --net-local-eras seam.
# The bible has NO rule that names the era line's words, the keys, the exchange between peers, the source of the local
# player's owned eras or the test seam. Those come from the Architect's gap rulings of 2026-10-14, not from the bible:
#   G1  the local player's owned eras are the installed packs of scenes/era_library/era_pack_source.gd manifests()
#       (era_order order, test_only skipped), filtered by UIDataBus.is_era_accessible(era_id); this file reads that
#       source itself to compare (on this tree: [settled_reach], the greek placeholder is not owned).
#   G2  each member sends ONE lobby chat message {t: "eras", ids: [era ids]} when it joins (a guest on lobby_joined);
#       the host keeps a table by lobby member id and publishes the intersection as lobby data key "playable_eras" (a
#       var_to_str list) and the whole table as "era_table" after every membership or table change, from
#       _on_lobby_created (never host_create); a leaving member drops its row; a malformed eras message is ignored
#       (ids not an Array, an item not a String, an empty Array; a sender that is not a lobby member); a member whose
#       message has not arrived is left out of the intersection; a guest shows its own set until the keys arrive; the
#       seam --net-local-eras <id,id> overrides the local owned list.
#   G3  EraLine reads exactly "Eras: you <list> · peers <list> · playable <intersection>" (middle dot U+00B7; ids
#       comma-space separated, known ids in era_order then unknown ids alphabetically; peers = union of the other
#       members' eras, "none" with no other member; playable = intersection over every member, the local one
#       included); qa_state gains eras {member id (String): [era ids]} and playable_eras, and keeps owned_eras
#       (= eras[local]) and common_eras (= playable_eras) (S-143.py:28-30).
#   Pin 1 (Architect 2026-10-19): the local row is always present in qa_state.eras, seeded from the owned list
#       independent of members(), with or without a lobby; playable_eras before a lobby exists = the local owned list.
# Not ruled, so not pinned: the words of the playable segment when the intersection is empty (the test pins only that
# no era id of the host follows "playable"); whether a member whose message has not arrived has an (empty) row in
# qa_state.eras.
#
# Fake lobby backend: no Steam, no pipe. Own FakeBackend with lobby_id and get_lobby_data (Architect pin 5 of
# 2026-10-19). Messages reach the lobby through the public on_chat the way lobby_message does; membership through the
# handler lobby_chat_update reaches. The narrowing cases need a host with two eras, and user args cannot be set
# in-process, so they run as a child of this file (--child, the pattern of tests/test_vg_f_w4_lobby.gd) with
# --net-local-eras. Headless, no display needed.

const LOBBY_SCENE := "res://scenes/lobby/lobby.tscn"
const SELF := "res://tests/test_vg_f_lobby_eras.gd"
const SETTLED := "settled_reach"
const GREEK := "greek_placeholder"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false
var _cur := ""


class FakeBackend extends RefCounted:
	var lobby_id := 0
	var created: Array = []
	var data := {}
	var sets: Array = []
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
	if "--child" in OS.get_cmdline_user_args():
		await _child_probe()
		return
	await _run_tests()
	_assert(_completed, "the checks did not run to the end (a script error aborted them)")
	print("\n=== VG-F S-143 Lobby Eras Test Results ===")
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
	await _t_one_player()
	await _t_local_row_always()
	await _t_exchange()
	await _t_guest_join_message()
	await _t_guest_reads_keys()
	await _t_seam_children()
	_completed = true


# --- helpers -----------------------------------------------------------------------------------------------------

func _mount(be: FakeBackend, local_id := 11, with_setup := true) -> Node:
	var lobby: Node = (load(LOBBY_SCENE) as PackedScene).instantiate()
	var net := FakeNet.new()
	get_root().add_child(net)
	get_root().add_child(lobby)
	lobby.net_match = net
	if with_setup:
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


func _host(lobby: Node, be: FakeBackend) -> void:
	lobby.host_create()
	lobby._on_lobby_created(1, 4242, be)
	await process_frame
	await process_frame


func _guest(lobby: Node, be: FakeBackend) -> void:
	lobby._on_lobby_joined(4242, 0, false, 1, be)
	await process_frame
	await process_frame


# lobby_chat_update reaches the handler: state 1 joined, 2 left (lobby.gd CHAT_LEFT_STATES).
func _members_changed(lobby: Node, be: FakeBackend, ids: Array, who: int, state: int) -> void:
	be.member_ids = ids
	lobby._on_chat_update(4242, who, who, state)
	await process_frame


func _say(lobby: Node, from_id: int, ids) -> void:
	lobby.on_chat(from_id, {"t": "eras", "ids": ids})
	await process_frame


func _line(lobby: Node) -> String:
	var n := lobby.find_child("EraLine", true, false) as Label
	return n.text if n != null else "<no EraLine>"


func _strs(a) -> Array:
	var out := []
	if a is Array:
		for v in a:
			out.append(String(v))
	return out


func _same(a, b) -> bool:
	return a is Array and b is Array and _strs(a) == _strs(b) and a.size() == b.size()


func _same_set(a, b) -> bool:
	if not (a is Array and b is Array):
		return false
	var x := _strs(a)
	var y := _strs(b)
	x.sort()
	y.sort()
	return x == y and a.size() == b.size()


# G1: the installed packs (era_order order, test_only skipped) filtered by ownership, read here from the source itself.
func _expected_owned() -> Array:
	var src = load("res://scenes/era_library/era_pack_source.gd").new()
	var bus = get_root().get_node_or_null("/root/UIDataBus")
	var out := []
	for m in src.manifests():
		if bus != null and bus.is_era_accessible(String(m["era_id"])):
			out.append(String(m["era_id"]))
	return out


# The helper under test (C3): the violations of "the common set is inside the owned set" (R-143-03).
func _violations(owned: Array, common: Array) -> Array:
	var out := []
	for e in common:
		if not owned.has(e):
			out.append(e)
	return out


func _line_text(you: Array, peers: Array, playable: Array) -> String:
	return "Eras: you %s · peers %s · playable %s" % [", ".join(you), "none" if peers.is_empty() else ", ".join(peers), ", ".join(playable)]


func _qa_eras(lobby: Node) -> Dictionary:
	var e = lobby.qa_state().get("eras", null)
	return e if e is Dictionary else {}


func _published(be: FakeBackend, key: String):
	var s := String(be.data.get(key, ""))
	return str_to_var(s) if s != "" else null


# --- positive controls (green today) -----------------------------------------------------------------------------

func _t_controls() -> void:
	_cur = "controls"
	var be := FakeBackend.new()
	var lobby := await _mount(be)
	var st: Dictionary = lobby.qa_state()
	_assert(st.get("scene", "") == "lobby" and st.get("members", []) == [11] and st.get("max_members", 0) == 4
			and st.get("friends_only", false) == true and st.get("tick", 0) == -1,
		"CONTROL C1: qa_state keeps scene lobby, members [11], max_members 4, friends_only true, tick -1; got %s" % str(st))
	var era_line := lobby.find_child("EraLine", true, false) as Label
	_assert(era_line != null and era_line.text.to_lower().contains("era"),
		"CONTROL C2: EraLine exists and its text contains 'era'; got %s" % (era_line.text if era_line != null else "no node"))
	# C3: the owned/common comparison reports a planted common set that is NOT inside the owned set.
	_assert(_violations([SETTLED], ["zeta_era"]) == ["zeta_era"], "CONTROL C3: the comparison flags a common era outside the owned set")
	_assert(_violations([SETTLED, GREEK], [GREEK]).is_empty() and _violations([SETTLED], []).is_empty(),
		"CONTROL C3: the comparison reports nothing for a subset or an empty common set")
	# G1 premise (the builder's stop rule): the source list is non-empty and holds the active era.
	var owned := _expected_owned()
	var active := String(get_root().get_node("/root/EraConfig").ACTIVE_ERA_ID)
	_assert(not owned.is_empty() and owned.has(active),
		"CONTROL G1 premise: the owned list from era_pack_source + UIDataBus is non-empty and contains EraConfig.ACTIVE_ERA_ID; got %s, active %s" % [str(owned), active])
	await _unmount(lobby)


# --- T143 red until built ------------------------------------------------------------------------------------------

func _t_one_player() -> void:
	_cur = "one_player"
	var owned := _expected_owned()
	var be := FakeBackend.new()
	var lobby := await _mount(be)
	var st: Dictionary = lobby.qa_state()
	var oe = st.get("owned_eras", null)
	var ce = st.get("common_eras", null)
	_assert(oe is Array and not (oe as Array).is_empty() and (oe as Array).all(func(v): return v is String),
		"R-143-01 / G1: qa_state.owned_eras is a non-empty Array of Strings; got %s" % str(oe))
	_assert(_same(oe, owned), "G1: owned_eras equals the installed packs filtered to owned, in era_order; expected %s, got %s" % [str(owned), str(oe)])
	_assert(ce is Array and _violations(_strs(oe), _strs(ce)).is_empty(),
		"R-143-03: common_eras is inside owned_eras; common %s, owned %s" % [str(ce), str(oe)])
	_assert(_same(ce, oe), "R-143-01: for a lobby of one player common_eras equals owned_eras; common %s, owned %s" % [str(ce), str(oe)])
	_assert(_same(st.get("playable_eras", null), owned), "G3: playable_eras is the intersection (the one player's set); got %s" % str(st.get("playable_eras", "missing")))
	var eras = st.get("eras", null)
	_assert(eras is Dictionary and (eras as Dictionary).size() == 1 and _same((eras as Dictionary).get("11", null), owned),
		"G3: qa_state.eras is {\"11\": owned} for the one local member (keys Strings); got %s" % str(eras))
	_assert(_same(oe, (eras as Dictionary).get("11", null) if eras is Dictionary else null), "G3: owned_eras equals eras[local member]")
	_assert(_line(lobby) == _line_text(owned, [], owned),
		"G3: EraLine reads exactly \"%s\"; got \"%s\"" % [_line_text(owned, [], owned), _line(lobby)])
	_assert(not _line(lobby).contains("Limited to the era set every player has."), "G3: the fixed sentence is replaced")
	await _unmount(lobby)


# Pin 1 (Architect 2026-10-19): the local row exists with or without a lobby, independent of members().
func _t_local_row_always() -> void:
	_cur = "local_row"
	var owned := _expected_owned()
	var be := FakeBackend.new()
	be.member_ids = []  # members() does not list the local player
	var lobby := await _mount(be)
	_assert(_same(_qa_eras(lobby).get("11", null), owned), "Pin 1: eras has the local row \"11\" although members() is empty; got %s" % str(_qa_eras(lobby)))
	_assert(_same(lobby.qa_state().get("owned_eras", null), owned), "Pin 1: owned_eras = eras[local] with members() empty")
	await _unmount(lobby)
	var bare := await _mount(null, 0, false)  # no setup, no backend: S-143.py reads right after go_to_lobby
	var st: Dictionary = bare.qa_state()
	_assert(_same(st.get("owned_eras", null), owned), "Pin 1: with no lobby, owned_eras is the local owned list; got %s" % str(st.get("owned_eras", "missing")))
	_assert(_same(st.get("playable_eras", null), owned) and _same(st.get("common_eras", null), owned),
		"Pin 1: with no lobby, playable_eras and common_eras are the local owned list; got %s / %s" % [str(st.get("playable_eras", "missing")), str(st.get("common_eras", "missing"))])
	var eras = st.get("eras", null)
	_assert(eras is Dictionary and (eras as Dictionary).size() == 1 and _same((eras as Dictionary).values()[0], owned),
		"Pin 1: with no lobby, eras holds exactly the local row; got %s" % str(eras))
	await _unmount(bare)


# G2 with the default owned list (one era on this tree): host table, intersection, line, leaving, malformed.
func _t_exchange() -> void:
	_cur = "exchange"
	var owned := _expected_owned()
	var be := FakeBackend.new()
	var lobby := await _mount(be)
	lobby.host_create()
	_assert(not be.data.has("playable_eras") and not be.data.has("era_table"),
		"G2 / Rev 13: host_create publishes no era key (Steam's createLobby is asynchronous); data %s" % str(be.data.keys()))
	lobby._on_lobby_created(1, 4242, be)
	await process_frame
	_assert(_same(_published(be, "playable_eras"), owned), "G2: the host publishes playable_eras (var_to_str list) from _on_lobby_created; got %s" % str(be.data.get("playable_eras", "none")))
	var tab = _published(be, "era_table")
	_assert(tab is Dictionary and (tab as Dictionary).size() == 1 and _same((tab as Dictionary).get("11", null), owned),
		"Rev 13a: the host publishes era_table {\"11\": owned}; got %s" % str(be.data.get("era_table", "none")))
	# A member joins, message not arrived: left out of the intersection, not counted as an empty set.
	await _members_changed(lobby, be, [11, 22], 22, 1)
	_assert(_same(lobby.qa_state().get("playable_eras", null), owned), "G2: a member whose message has not arrived is left out of the intersection; got %s" % str(lobby.qa_state().get("playable_eras", "missing")))
	# 22 owns the host's era plus two ids this game has no pack for: they stay in its row and the line sorts them.
	await _say(lobby, 22, ["zeta_era", owned[0], "alpha_era"])
	var row = _qa_eras(lobby).get("22", null)
	_assert(_same_set(row, ["zeta_era", owned[0], "alpha_era"]), "G2: ids with no local pack stay in the member's row; got %s" % str(row))
	_assert(_same(lobby.qa_state().get("playable_eras", null), owned), "G2: the intersection is the host's era; got %s" % str(lobby.qa_state().get("playable_eras", "missing")))
	_assert(_line(lobby) == _line_text(owned, [owned[0], "alpha_era", "zeta_era"], owned),
		"G3: peers is the union of the others' eras, known ids in era_order then unknown ids alphabetically; expected \"%s\", got \"%s\"" % [_line_text(owned, [owned[0], "alpha_era", "zeta_era"], owned), _line(lobby)])
	var tab2 = _published(be, "era_table")
	_assert(tab2 is Dictionary and (tab2 as Dictionary).has("11") and (tab2 as Dictionary).has("22") and _same(_published(be, "playable_eras"), owned),
		"G2 / Rev 13a: after the message the host republishes playable_eras and era_table with both rows; got %s" % str(be.data.get("era_table", "none")))
	# A third member owns none of the host's eras: the intersection empties and the line says so.
	await _members_changed(lobby, be, [11, 22, 33], 33, 1)
	await _say(lobby, 33, ["other_era"])
	var st3: Dictionary = lobby.qa_state()
	_assert(_same(st3.get("playable_eras", null), []) and _same(st3.get("common_eras", null), []),
		"G2 / R-143-03: a member lacking every pack empties playable_eras and common_eras; got %s / %s" % [str(st3.get("playable_eras", "missing")), str(st3.get("common_eras", "missing"))])
	var line3 := _line(lobby)
	var after := line3.get_slice(" · playable", 1) if line3.contains(" · playable") else "<no playable segment>"
	_assert(line3.begins_with("Eras: you %s · peers " % ", ".join(owned)) and line3.contains(" · playable") and not after.contains(owned[0]),
		"G3 / R-143-03: the line says the playable set is empty (no host era id after \"playable\"); got \"%s\"" % line3)
	_assert(_same(_published(be, "playable_eras"), []), "G2: the host publishes the empty intersection; got %s" % str(be.data.get("playable_eras", "none")))
	# The third member leaves: its row drops and the set is restored.
	await _members_changed(lobby, be, [11, 22], 33, 2)
	_assert(not _qa_eras(lobby).has("33") and _same(lobby.qa_state().get("playable_eras", null), owned),
		"G2: a leaving member drops its row and the intersection is restored; eras %s, playable %s" % [str(_qa_eras(lobby)), str(lobby.qa_state().get("playable_eras", "missing"))])
	var tab3 = _published(be, "era_table")
	_assert(tab3 is Dictionary and not (tab3 as Dictionary).has("33") and _same(_published(be, "playable_eras"), owned),
		"Rev 13a: the host republishes both keys when a member leaves; got %s" % str(be.data.get("era_table", "none")))
	# Malformed messages and a non-member sender change nothing.
	var eras_before: Dictionary = _qa_eras(lobby).duplicate(true)
	var play_before: Array = _strs(lobby.qa_state().get("playable_eras", []))
	var line_before := _line(lobby)
	_assert(eras_before.has("11") and eras_before.has("22"), "G2 premise for the malformed cases: the table holds the local row and member 22's valid row; got %s" % str(eras_before))
	await _say(lobby, 22, "settled_reach")  # ids not an Array
	await _say(lobby, 22, [1, 2])  # items not Strings
	await _say(lobby, 22, [owned[0], 5])  # one item not a String
	await _say(lobby, 22, [])  # an empty Array
	lobby.on_chat(22, {"t": "eras"})  # no ids
	lobby.on_chat(22, "junk")
	lobby.on_chat(22, null)
	await _say(lobby, 99, ["other_era"])  # 99 is not a lobby member
	await process_frame
	_assert(_qa_eras(lobby) == eras_before and _strs(lobby.qa_state().get("playable_eras", [])) == play_before and _line(lobby) == line_before,
		"G2: malformed eras messages and a message from a non-member are ignored; eras before %s after %s, line \"%s\"" % [str(eras_before), str(_qa_eras(lobby)), _line(lobby)])
	# The last guest leaves: back to the one-player state.
	await _members_changed(lobby, be, [11], 22, 2)
	_assert(_line(lobby) == _line_text(owned, [], owned) and _qa_eras(lobby).size() == 1,
		"G2/G3: with every other member gone the line and the table are the one-player ones; got \"%s\", eras %s" % [_line(lobby), str(_qa_eras(lobby))])
	await _unmount(lobby)


# G2: a guest sends ONE eras message on lobby_joined.
func _t_guest_join_message() -> void:
	_cur = "guest_join"
	var owned := _expected_owned()
	var be := FakeBackend.new()
	be.member_ids = [11, 22]
	var lobby := await _mount(be, 22)
	_assert(be.chats.filter(func(m): return m.get("t", "") == "eras").is_empty(), "G2: nothing is sent before the guest joins")
	await _guest(lobby, be)
	var sent: Array = be.chats.filter(func(m): return m.get("t", "") == "eras")
	_assert(sent.size() == 1 and sent[0].get("ids", null) is Array and _same(sent[0].get("ids"), owned),
		"G2: on lobby_joined the guest sends one lobby chat message {t: \"eras\", ids: owned}; sent %s" % str(be.chats))
	await process_frame
	await process_frame
	_assert(be.chats.filter(func(m): return m.get("t", "") == "eras").size() == 1, "G2: the eras message is sent once, not again on later frames")
	await _unmount(lobby)


# G2/G3: a guest takes playable_eras and era_table from the lobby data keys, shows its own set until they arrive.
func _t_guest_reads_keys() -> void:
	_cur = "guest_keys"
	var owned := _expected_owned()
	var be := FakeBackend.new()
	be.member_ids = [11, 22]
	var lobby := await _mount(be, 22)
	await _guest(lobby, be)
	_assert(_same(lobby.qa_state().get("playable_eras", null), owned), "G2: before the keys arrive a guest shows its own set; got %s" % str(lobby.qa_state().get("playable_eras", "missing")))
	be.data["playable_eras"] = var_to_str([owned[0]])
	be.data["era_table"] = var_to_str({"11": [owned[0], "x_era"], "22": owned})
	await process_frame
	await process_frame
	var eras = _qa_eras(lobby)
	_assert(eras.size() == 2 and _same_set(eras.get("11", null), [owned[0], "x_era"]) and _same(eras.get("22", null), owned),
		"Rev 13a: a guest's qa_state.eras is the host's era_table without a hand-called _refresh; got %s" % str(eras))
	_assert(_same(lobby.qa_state().get("playable_eras", null), [owned[0]]) and _same(lobby.qa_state().get("common_eras", null), [owned[0]]),
		"G2: a guest's playable_eras and common_eras read the host's key; got %s" % str(lobby.qa_state().get("playable_eras", "missing")))
	_assert(_same(lobby.qa_state().get("owned_eras", null), owned), "G3: a guest's owned_eras stays its own (= eras[local]); got %s" % str(lobby.qa_state().get("owned_eras", "missing")))
	_assert(_line(lobby) == _line_text(owned, [owned[0], "x_era"], [owned[0]]),
		"G3: the guest's line shows the host's peers and playable; expected \"%s\", got \"%s\"" % [_line_text(owned, [owned[0], "x_era"], [owned[0]]), _line(lobby)])
	await _unmount(lobby)


# --- the --net-local-eras seam and the two-era narrowing, as children ----------------------------------------------

func _run_child(seam: String) -> Dictionary:
	var args := ["--headless", "--path", ProjectSettings.globalize_path("res://"), "--script", SELF, "--", "--child"]
	if seam != "":
		args.append_array(["--net-local-eras", seam])
	var out: Array = []
	OS.execute(OS.get_executable_path(), args, out, true)
	for line in "\n".join(out).split("\n"):
		if line.begins_with("CHILD-ERAS "):
			var v = JSON.parse_string(line.substr("CHILD-ERAS ".length()))
			return v if v is Dictionary else {}
	return {}


func _dig(d, path: Array):
	var cur = d
	for k in path:
		if cur is Dictionary and (cur as Dictionary).has(k):
			cur = cur[k]
		else:
			return null
	return cur


func _t_seam_children() -> void:
	_cur = "seam_two_eras"
	var both := "%s,%s" % [SETTLED, GREEK]
	var two := _run_child(both)
	print("CHILD two eras keys: ", two.keys())
	_assert(not two.is_empty(), "CONTROL: the child run with --net-local-eras printed a CHILD-ERAS line, so the child harness works")
	var you := [SETTLED, GREEK]
	_assert(_same(_dig(two, ["alone", "qa", "owned_eras"]), you), "G2: --net-local-eras %s overrides owned_eras; got %s" % [both, str(_dig(two, ["alone", "qa", "owned_eras"]))])
	_assert(_same(_dig(two, ["alone", "qa", "common_eras"]), you), "G2: a lone host with two eras has common_eras equal to both; got %s" % str(_dig(two, ["alone", "qa", "common_eras"])))
	_assert(_dig(two, ["alone", "line"]) == _line_text(you, [], you), "G3: the lone two-era line is \"%s\"; got \"%s\"" % [_line_text(you, [], you), str(_dig(two, ["alone", "line"]))])
	_assert(_same(_dig(two, ["alone", "pub"]), you), "G2: the host publishes both eras as playable_eras; got %s" % str(_dig(two, ["alone", "pub"])))
	# A second member naming only one of the host's two eras narrows the set.
	_cur = "seam_narrow"
	var one := [GREEK]
	_assert(_same(_dig(two, ["narrow", "qa", "playable_eras"]), one) and _same(_dig(two, ["narrow", "qa", "common_eras"]), one),
		"G2 / R-143-01: a second member whose message names only %s narrows playable_eras and common_eras to it on the host; got %s / %s" % [GREEK, str(_dig(two, ["narrow", "qa", "playable_eras"])), str(_dig(two, ["narrow", "qa", "common_eras"]))])
	_assert(_same(_dig(two, ["narrow", "qa", "owned_eras"]), you), "G3: owned_eras is unchanged by the narrowing (still both); got %s" % str(_dig(two, ["narrow", "qa", "owned_eras"])))
	_assert(_dig(two, ["narrow", "line"]) == _line_text(you, one, one), "G3: the narrowed line is \"%s\"; got \"%s\"" % [_line_text(you, one, one), str(_dig(two, ["narrow", "line"]))])
	_assert(_same(_dig(two, ["narrow", "pub"]), one), "G2: the host publishes the narrowed playable_eras; got %s" % str(_dig(two, ["narrow", "pub"])))
	_assert(_dig(two, ["narrow", "table", "22"]) != null and _same(_dig(two, ["narrow", "table", "22"]), one), "Rev 13a: the published era_table carries the second member's row; got %s" % str(_dig(two, ["narrow", "table"])))
	# A third member owning neither: empty, and the line says so.
	_cur = "seam_empty"
	_assert(_same(_dig(two, ["empty", "qa", "playable_eras"]), []) and _same(_dig(two, ["empty", "qa", "common_eras"]), []),
		"G2 / R-143-03: a third member lacking both empties common_eras; got %s" % str(_dig(two, ["empty", "qa", "common_eras"])))
	var el := String(_dig(two, ["empty", "line"]) if _dig(two, ["empty", "line"]) != null else "")
	var tail := el.get_slice(" · playable", 1) if el.contains(" · playable") else "<no playable segment>"
	_assert(el.begins_with("Eras: you %s · peers " % ", ".join(you)) and not tail.contains(SETTLED) and not tail.contains(GREEK),
		"G3: the empty case line has no host era id after \"playable\"; got \"%s\"" % el)
	# The third member leaves: the narrowed set is back; the second leaves: the full set is back.
	_cur = "seam_restore"
	_assert(_same(_dig(two, ["after33", "qa", "playable_eras"]), one) and _dig(two, ["after33", "line"]) == _line_text(you, one, one),
		"G2: a member leaving restores the set it had; got %s / \"%s\"" % [str(_dig(two, ["after33", "qa", "playable_eras"])), str(_dig(two, ["after33", "line"]))])
	_assert(_same(_dig(two, ["restored", "qa", "playable_eras"]), you) and _dig(two, ["restored", "line"]) == _line_text(you, [], you),
		"G2: with every other member gone playable is both eras again; got %s / \"%s\"" % [str(_dig(two, ["restored", "qa", "playable_eras"])), str(_dig(two, ["restored", "line"]))])
	_assert(_same(_dig(two, ["restored", "pub"]), you), "G2: the host republishes the restored set; got %s" % str(_dig(two, ["restored", "pub"])))
	# The guest sends the seam list when it joins (S-143 two-process case: the guest owns one era).
	_cur = "seam_guest"
	_assert(_same(_dig(two, ["guest", "sent"]), you), "G2: a guest launched with --net-local-eras %s sends those ids on lobby_joined; got %s" % [both, str(_dig(two, ["guest", "sent"]))])
	var single := _run_child(GREEK)
	_assert(not single.is_empty(), "CONTROL: the child run with a one-era seam printed a CHILD-ERAS line")
	_assert(_same(_dig(single, ["alone", "qa", "owned_eras"]), one) and _dig(single, ["alone", "line"]) == _line_text(one, [], one),
		"G2/G3: --net-local-eras %s gives owned_eras [%s] and the one-era line; got %s / \"%s\"" % [GREEK, GREEK, str(_dig(single, ["alone", "qa", "owned_eras"])), str(_dig(single, ["alone", "line"]))])
	_assert(_same(_dig(single, ["guest", "sent"]), one) and _same(_dig(single, ["guest", "qa", "owned_eras"]), one),
		"G2: a guest launched with a one-era seam sends and owns just that era; got %s / %s" % [str(_dig(single, ["guest", "sent"])), str(_dig(single, ["guest", "qa", "owned_eras"]))])


# Child half: runs the scenario and prints observations as one JSON line; the parent asserts on them.
func _snap(lobby: Node, be: FakeBackend) -> Dictionary:
	var pub = _published(be, "playable_eras")
	var tab = _published(be, "era_table")
	return {"qa": lobby.qa_state(), "line": _line(lobby), "pub": pub, "table": tab}


func _child_probe() -> void:
	var obs := {}
	var be := FakeBackend.new()
	var lobby := await _mount(be)
	await _host(lobby, be)
	obs["alone"] = _snap(lobby, be)
	await _members_changed(lobby, be, [11, 22], 22, 1)
	await _say(lobby, 22, [GREEK])
	obs["narrow"] = _snap(lobby, be)
	await _members_changed(lobby, be, [11, 22, 33], 33, 1)
	await _say(lobby, 33, ["x_era"])
	obs["empty"] = _snap(lobby, be)
	await _members_changed(lobby, be, [11, 22], 33, 2)
	obs["after33"] = _snap(lobby, be)
	await _members_changed(lobby, be, [11], 22, 2)
	obs["restored"] = _snap(lobby, be)
	await _unmount(lobby)
	var be2 := FakeBackend.new()
	be2.member_ids = [11, 22]
	var guest := await _mount(be2, 22)
	await _guest(guest, be2)
	var sent: Array = be2.chats.filter(func(m): return m.get("t", "") == "eras")
	obs["guest"] = {"sent": sent[0].get("ids", null) if sent.size() == 1 else null, "qa": guest.qa_state()}
	await _unmount(guest)
	print("CHILD-ERAS " + JSON.stringify(obs))
	quit(0)
