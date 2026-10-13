extends SceneTree

# Piece VG-B B5 tests (docs/northstar/plans/2026-10-07-visible-game-spec.md,
# lane B; preflight 3-galaxy-field.md; bible E-16 S-106/R-106-02: territory
# follows ownership). REFILL mechanics on the product galaxy scene:
#   res://scenes/galaxy/galaxy_view.tscn has a child "ShellRenderer" with
#   get_territory_field() -> TerritoryField (B1, signal-fed through
#   bind_world_view; API: is_dirty(), refill(), fill_count, last_refill_ms,
#   field_texture, id_texture). Owner changes are fed the way tests/test_vg_b_b1.gd
#   does: set_territory() on the world-view data (the view's "GalaxyAdapter" node),
#   a different faction colour being a different owner. (Architect ruling 2026-10-08,
#   TD-VG-B-3: the field has no set_system_owner.)
# Proves (a) a changed owner in a snapshot given to the view dirties the field,
# (b) refill() clears dirty and rebuilds the field and id textures, (c) the
# refill time is measured and printed. The 12 ms threshold is Westley's and
# lives in tests/test_vg_b_b5_park_refill.gd. The rule here is the flip itself.
# Needs a real renderer: run under xvfb with Vulkan (forward_plus), not
# --headless (the dummy renderer cannot bake the field).

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const SAMPLES := 14
const WARMUP := 2

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== VG-B B5 Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count > 0:
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


# Give territory `key` the colour of another faction (alternating by n): an owner change as the field sees it.
func _flip(adapter: Node, key: String, n: int) -> void:
	var t: Dictionary = adapter.territories[key]
	var c: Color = Color.from_hsv(0.13 + 0.31 * float(1 + (n % 2)), 0.7, 0.9)
	adapter.set_territory(key, t["center"], t["radius"], c)


func _run_tests() -> void:
	var snap = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_PATH))
	_assert(snap is Dictionary and not (snap as Dictionary).get("regions", []).is_empty(), "fixture snapshot missing or has no regions: " + FIXTURE_PATH)
	if not (snap is Dictionary):
		return
	var packed = load(SCENE_PATH)
	_assert(packed is PackedScene, "cannot load " + SCENE_PATH)
	if not (packed is PackedScene):
		return
	var view: Node = (packed as PackedScene).instantiate()
	get_root().add_child(view)
	await process_frame
	view.set_snapshot(snap)
	await process_frame
	await process_frame

	var shell: Node = view.get_node_or_null("ShellRenderer")
	_assert(shell != null, "REFILL: galaxy_view has no child node ShellRenderer (B1..B4 field not wired in)")
	if shell == null:
		return
	_assert(shell.has_method("get_territory_field"), "REFILL: ShellRenderer has no get_territory_field()")
	if not shell.has_method("get_territory_field"):
		return
	var field: Node = shell.get_territory_field()
	_assert(field != null, "REFILL: get_territory_field() returned null")
	if field == null:
		return
	for m in ["is_dirty", "refill", "bind_world_view"]:
		_assert(field.has_method(m), "REFILL: TerritoryField missing method " + m)
		if not field.has_method(m):
			return
	_assert(DisplayServer.get_name() != "headless", "REFILL: running headless, the field cannot bake; run under xvfb with Vulkan")
	if DisplayServer.get_name() == "headless":
		return

	await process_frame
	await process_frame
	_assert(not field.is_dirty(), "REFILL: field still dirty after the first frames (refill never ran)")
	var tex_before = field.get("field_texture")
	_assert(tex_before != null and field.get("id_texture") != null, "REFILL: field/id textures not built after first refill")

	var adapter: Node = view.get_node_or_null("GalaxyAdapter")
	_assert(adapter != null and not adapter.territories.is_empty(), "REFILL: galaxy_view has no GalaxyAdapter with territories after set_snapshot")
	if adapter == null or adapter.territories.is_empty():
		return
	var key: String = str(adapter.territories.keys()[0])

	# (a) wiring: an owner flip in a snapshot dirties the field.
	var regions: Array = snap["regions"]
	var idx := 0
	var old_owner: int = int(regions[idx]["owner"])
	var flipped: Dictionary = (snap as Dictionary).duplicate(true)
	flipped["regions"][idx]["owner"] = (old_owner + 1) % 4
	view.set_snapshot(flipped)
	_assert(field.is_dirty(), "REFILL: owner flip via GalaxyView.set_snapshot did not mark the field dirty (territory would not follow conquest)")

	# (b) refill clears dirty; the next frame leaves it clean and the textures live.
	field.refill()
	_assert(not field.is_dirty(), "REFILL: refill() left the field dirty")
	_assert(field.get("field_texture") != null and field.get("id_texture") != null, "REFILL: textures missing after refill()")
	var fills_a = field.get("fill_count")
	_flip(adapter, key, 0)
	_assert(field.is_dirty(), "REFILL: a territory colour change on the world-view data did not dirty the field")
	field.refill()
	_assert(field.get("fill_count") == fills_a + 1, "REFILL: fill_count did not advance by one per refill (got %s after %s)" % [str(field.get("fill_count")), str(fills_a)])

	# (c) measure: owner flip then refill, as the park test does; printed only.
	var times: Array = []
	for i in SAMPLES:
		_flip(adapter, key, i)
		var t0 := Time.get_ticks_usec()
		field.refill()
		var ms := (Time.get_ticks_usec() - t0) / 1000.0
		if i >= WARMUP:
			times.append(ms)
		await process_frame
	times.sort()
	print("REFILL median %.2f ms (n=%d) on %s" % [times[times.size() / 2], times.size(), RenderingServer.get_video_adapter_name()])
	_assert(times.size() == SAMPLES - WARMUP, "REFILL: sampling loop did not complete")
	view.queue_free()
