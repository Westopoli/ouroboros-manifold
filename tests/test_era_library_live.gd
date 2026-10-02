extends SceneTree

# Piece C4-E1 (owner G-eralib, docs/northstar/plans/push/pieces.toml; ruling A45 in
# docs/northstar/plans/2026-10-01-architect-rulings-2.md). Proves:
#   R-110-05  one card per installed era pack that passes validation; a failing pack is not listed;
#             each card has name and owned flag
#   R-110-06  the detail shows identity, three tiers and unit roster, all from the pack manifest;
#             nothing on screen is hard-coded
#   R-110-07  ownership comes from a local ownership store; in dev builds every installed era is
#             owned; the screen shows no mastery or tier progress (A51, Q-110-05 closed (a):
#             removed, not "not yet tracked")
# Validation here is the required-key rule of scripts/specfactory/pack_validate.py (R-146-03).
#
# Contract required (the scene roots, res://scenes/era_library/):
#   era_library.tscn root:
#     qa_set_sources(packs_root: String, ownership_path: String) -> void
#         re-reads packs from <packs_root>/<era_id>/manifest.json and rebuilds the cards;
#         ownership_path "" or a missing file = the dev default (every installed era owned)
#     qa_state() -> Dictionary   gains "eras": Array of {id, name, owned: bool};
#         "era_count" == eras.size(); no mastery or tier-progress key anywhere in the state
#   era_detail.tscn root:
#     qa_set_sources(packs_root, ownership_path) -> void   (call before setup)
#     setup({"era_id": id}) as today
#     qa_state() -> Dictionary   gains "era_id", "name", "owned": bool, "tiers": Array[int]
#         (the tier numbers in the manifest), "roster": Array of {abstract_type, category};
#         no mastery or tier-progress key
# With no qa_set_sources call both scenes read res://assets/eras/ (the live default).

const LIB := "res://scenes/era_library/era_library.tscn"
const DETAIL := "res://scenes/era_library/era_detail.tscn"
const REAL_PACKS := "res://assets/eras"
const FIX_ROOT := "user://c4_e1_fixture_packs"
const PROGRESS_TEXT := ["mastery", "tier progress", "not yet tracked"]
const LEGACY_TEXT := ["Legionary", "Medicus", "Roman", "Cold War", "Available on Steam", "COMING SOON", "Thalassa", "Tomcat"]

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the era-library checks did not run to the end (a script error aborted them)")
	print("\n=== Era Library Live Test Results ===")
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
		_fail_msgs.append(msg)


func _unit(cat: String, scale := 1.0) -> Dictionary:
	var tiers := {}
	for t in ["1", "2", "3"]:
		tiers[t] = {"scene": "placeholder.glb"}
	return {"category": cat, "squad_count": 1, "visual_scale": scale, "facing_offset_rad": 0.0, "tiers": tiers}


func _manifest(era_id: String, name: String, accent: String, units: Dictionary) -> Dictionary:
	return {
		"era_id": era_id, "era_display_name": name, "era_accent_color": accent,
		"units": units, "structures": {}, "environment": {}, "materials": {},
		"faction_colors": {"0": "#4099FF"},
	}


func _write_pack(era_id: String, manifest: Dictionary) -> void:
	var dir := FIX_ROOT + "/" + era_id
	DirAccess.make_dir_recursive_absolute(dir)
	var f := FileAccess.open(dir + "/manifest.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(manifest))
	f.close()
	# placeholder.glb so scene paths resolve for the validator; content is irrelevant here
	var g := FileAccess.open(dir + "/placeholder.glb", FileAccess.WRITE)
	g.store_string("x")
	g.close()


func _texts(node: Node, out: Array) -> Array:
	if node is Label:
		out.append((node as Label).text)
	elif node is RichTextLabel:
		out.append((node as RichTextLabel).text)
	elif node is Button:
		out.append((node as Button).text)
	for c in node.get_children():
		_texts(c, out)
	return out


func _legacy_hits(node: Node) -> Array:
	var hits := []
	for t in _texts(node, []):
		for bad in LEGACY_TEXT:
			if str(t).findn(bad) >= 0:
				hits.append("%s in '%s'" % [bad, t])
	return hits


# Names of any mastery/tier-progress text, state key, or progress-bar node under the scene or state.
func _progress_hits(node: Node, state) -> Array:
	var hits := []
	for t in _texts(node, []):
		for bad in PROGRESS_TEXT:
			if str(t).findn(bad) >= 0:
				hits.append("text '%s'" % t)
	_progress_nodes(node, hits)
	_progress_keys(state, hits)
	return hits


func _progress_nodes(node: Node, hits: Array) -> void:
	if node is ProgressBar:
		hits.append("ProgressBar node %s" % node.name)
	for c in node.get_children():
		_progress_nodes(c, hits)


func _progress_keys(v, hits: Array) -> void:
	if v is Dictionary:
		for k in v.keys():
			var ks := str(k).to_lower()
			if ks.find("mastery") >= 0 or ks.find("progress") >= 0:
				hits.append("state key '%s'" % k)
			_progress_keys(v[k], hits)
	elif v is Array:
		for x in v:
			_progress_keys(x, hits)


func _entry(eras: Array, id: String) -> Dictionary:
	for e in eras:
		if e is Dictionary and e.get("id", "") == id:
			return e
	return {}


func _mount(path: String, packs_root: String):
	var scene: Node = (load(path) as PackedScene).instantiate()
	get_root().add_child(scene)
	await process_frame
	if packs_root != "":
		if not scene.has_method("qa_set_sources"):
			_assert(false, "%s root missing qa_set_sources (piece C4-E1 not attached yet)" % path)
			scene.queue_free()
			return null
		scene.qa_set_sources(packs_root, "")
		await process_frame
	return scene


func _run_tests() -> void:
	# Positive control for the hard-coded-text detector: a tree that holds legacy text must be caught.
	var ctl := Control.new()
	var ctl_label := Label.new()
	ctl_label.text = "Legionary"
	ctl.add_child(ctl_label)
	_assert(_legacy_hits(ctl).size() == 1, "control: legacy-text scan failed to catch a planted 'Legionary' label")
	var ctl_prog := Label.new()
	ctl_prog.text = "Mastery 40%"
	ctl.add_child(ctl_prog)
	var ctl_bar := ProgressBar.new()
	ctl.add_child(ctl_bar)
	var ctl_hits := _progress_hits(ctl, {"eras": [{"id": "x", "tier_progress": 1}]})
	_assert(ctl_hits.size() == 3, "control: progress scan caught %s, expected a planted mastery label, ProgressBar and tier_progress key (3)" % [ctl_hits])
	ctl.free()

	# Fixture packs: two valid, one that fails validation (missing the required key "materials").
	_write_pack("zz_dunes", _manifest("zz_dunes", "The Fixture Dunes", "#aa5500",
		{"alpha": _unit("line"), "beta": _unit("strike"), "gamma": _unit("siege")}))
	_write_pack("zz_tide", _manifest("zz_tide", "The Fixture Tide", "#0055aa", {"delta": _unit("line")}))
	var broken := _manifest("zz_broken", "Broken Fixture Pack", "#111111", {"eps": _unit("line")})
	broken.erase("materials")
	_write_pack("zz_broken", broken)

	# --- Library over the fixture packs (R-110-05, R-110-07) ---
	var lib = await _mount(LIB, FIX_ROOT)
	if lib == null:
		return
	for m in ["qa_set_sources", "qa_state"]:
		_assert(lib.has_method(m), "era_library root missing method: " + m)
	var st: Dictionary = lib.qa_state()
	_assert(JSON.stringify(st) != "", "era_library qa_state() did not survive JSON.stringify")
	var eras: Array = st.get("eras", [])
	var ids := []
	for e in eras:
		ids.append(e.get("id", ""))
	ids.sort()
	_assert(ids == ["zz_dunes", "zz_tide"], "R-110-05: library over fixture packs lists %s, expected exactly [zz_dunes, zz_tide] (invalid pack hidden, nothing hard-coded)" % [ids])
	_assert(int(st.get("era_count", -1)) == eras.size(), "era_count %s != eras.size() %d" % [st.get("era_count"), eras.size()])
	var dunes := _entry(eras, "zz_dunes")
	_assert(dunes.get("name", "") == "The Fixture Dunes", "R-110-05: card name '%s' is not the manifest's era_display_name" % dunes.get("name", ""))
	_assert(bool(dunes.get("owned", false)) and bool(_entry(eras, "zz_tide").get("owned", false)),
		"R-110-07: in a dev build every installed era is owned, got %s" % [eras])
	var phits := _progress_hits(lib, st)
	_assert(phits.is_empty(), "R-110-07/A51: library shows mastery or tier progress, it must be removed entirely: %s" % [phits])
	var texts := _texts(lib, [])
	_assert("The Fixture Dunes" in texts, "R-110-05: no label on the library screen shows the manifest name 'The Fixture Dunes'")
	var hits := _legacy_hits(lib)
	_assert(hits.is_empty(), "R-110-06: hard-coded legacy text still on the library screen: %s" % [hits])

	# Positive control for the validation filter: repair the broken pack, it must now be listed.
	_write_pack("zz_broken", _manifest("zz_broken", "Broken Fixture Pack", "#111111", {"eps": _unit("line")}))
	lib.qa_set_sources(FIX_ROOT, "")
	await process_frame
	var ids2 := []
	for e in lib.qa_state().get("eras", []):
		ids2.append(e.get("id", ""))
	_assert("zz_broken" in ids2, "control: a repaired pack must appear once it passes validation, got %s" % [ids2])
	lib.queue_free()
	await process_frame

	# --- Library over the live packs (default path) ---
	var live = await _mount(LIB, "")
	var live_ids := []
	for e in live.qa_state().get("eras", []):
		live_ids.append(e.get("id", ""))
	_assert("settled_reach" in live_ids and "greek_placeholder" in live_ids,
		"R-110-05: live library must list the installed packs settled_reach and greek_placeholder, got %s" % [live_ids])
	for gone in ["roman", "1980s"]:
		_assert(not (gone in live_ids), "R-110-06: '%s' has no pack under assets/eras/ yet is listed (hard-coded era)" % gone)
	for id in live_ids:
		_assert(FileAccess.file_exists("%s/%s/manifest.json" % [REAL_PACKS, id]), "listed era '%s' has no installed pack manifest" % id)
	live.queue_free()
	await process_frame

	# --- Detail (R-110-06, R-110-07) ---
	var det = await _mount(DETAIL, FIX_ROOT)
	if det == null:
		return
	det.setup({"era_id": "zz_dunes"})
	await process_frame
	var ds: Dictionary = det.qa_state() if det.has_method("qa_state") else {}
	_assert(JSON.stringify(ds) != "", "era_detail qa_state() did not survive JSON.stringify")
	_assert(ds.get("era_id", "") == "zz_dunes" and ds.get("name", "") == "The Fixture Dunes",
		"R-110-06: detail identity %s/%s, expected zz_dunes / The Fixture Dunes" % [ds.get("era_id"), ds.get("name")])
	_assert(bool(ds.get("owned", false)), "R-110-07: dev build, detail must report owned")
	var tiers := []
	for t in ds.get("tiers", []):
		tiers.append(int(t))
	tiers.sort()
	_assert(tiers == [1, 2, 3], "R-110-06: detail tiers %s, expected [1, 2, 3] from the manifest" % [tiers])
	var roster := {}
	for r in ds.get("roster", []):
		roster[r.get("abstract_type", "")] = r.get("category", "")
	_assert(roster == {"alpha": "line", "beta": "strike", "gamma": "siege"},
		"R-110-06: detail roster %s, expected exactly the manifest units alpha/beta/gamma with their categories" % [roster])
	var dphits := _progress_hits(det, ds)
	_assert(dphits.is_empty(), "R-110-07/A51: detail shows mastery or tier progress, it must be removed entirely: %s" % [dphits])
	var dtexts := _texts(det, [])
	_assert("The Fixture Dunes" in dtexts, "R-110-06: detail screen shows no label with the manifest name")
	var dhits := _legacy_hits(det)
	_assert(dhits.is_empty(), "R-110-06: hard-coded legacy text still on the detail screen: %s" % [dhits])
	det.queue_free()
	await process_frame

	_completed = true
