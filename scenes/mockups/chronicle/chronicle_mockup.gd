extends Control

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")
const TICKS_PER_SEC := 20.0
const FADE_TICKS := 4
const KEYFRAME_FLASH_COLOR := Color(1.0, 0.85, 0.3)

const PLANTS: Array[String] = [
	"order-shuffled",
	"expand-noop",
	"no-pause",
	"entries-duplicate",
	"morph-instant",
	"cadence-wallclock",
]

var _jump: ChronicleJump
var _tick: int = 0
var _tick_accum: float = 0.0
var _phase: String = "idle"
var _expanded_id: String = ""
var _current_seed: int = 11
var _map_fraction: float = 1.0
var _regen_count: int = 0
var _load_ms: float = 0.0
var _fired_keyframes: Dictionary = {}

var _map_viewport: SubViewportContainer
var _galaxy_view: Node3D
var _orbit_camera: Node3D
var _scroll
var _hud


func _ready() -> void:
	_map_viewport = get_node("MapViewport")
	_galaxy_view = get_node("MapViewport/SubViewport/World/GalaxyView")
	_orbit_camera = get_node("MapViewport/SubViewport/OrbitCamera")
	_orbit_camera.set_galaxy_view(_galaxy_view)
	_galaxy_view.attach_camera(_orbit_camera)
	_scroll = get_node("Scroll")
	_hud = get_node("HUD")
	_scroll.setup(self)
	_start_jump(11)


func _process(delta: float) -> void:
	var advancing := _phase == "narrating" or (_phase == "paused" and QaPlants.is_active("no-pause"))
	if advancing:
		_tick_accum += delta * TICKS_PER_SEC
		while _tick_accum >= 1.0:
			_tick_accum -= 1.0
			_tick += 1
			_apply_due_keyframes()
			if _all_entries_printed():
				_finish()
	_sync_view()


func _sync_view() -> void:
	_galaxy_view.update_view(_orbit_camera.get_distance(), _orbit_camera.get_focused(), -1, -1)
	_scroll.render(_render_rows(), _expanded_id)
	_hud.refresh(qa_state())


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_S:
			_on_skip()
		elif event.keycode == KEY_ENTER or event.keycode == KEY_KP_ENTER:
			_on_proceed()
		elif event.keycode == KEY_R:
			_on_reset()
		elif event.keycode == KEY_ESCAPE:
			qa_dismiss()


func _on_skip() -> void:
	qa_set("skip", true)


func _on_reset() -> void:
	_start_jump(_current_seed)


func _on_proceed() -> void:
	pass


func _start_jump(seed_n: int) -> void:
	var t0 := Time.get_ticks_usec()
	_jump = ChronicleJump.new()
	_current_seed = seed_n
	_jump.load_file("res://scenes/mockups/chronicle/fixtures/jump_seed%d.json" % seed_n)
	_tick = 0
	_tick_accum = 0.0
	_phase = "narrating"
	_expanded_id = ""
	_fired_keyframes.clear()
	_map_fraction = 0.62
	_apply_map_fraction()
	var galaxy: Galaxy = GalaxyGen.new().generate(seed_n)
	_galaxy_view.build(galaxy)
	_scroll.begin()
	_regen_count += 1
	_load_ms = (Time.get_ticks_usec() - t0) / 1000.0
	_sync_view()


# Every keyframe (not only the ones that change ownership) drives set_owner
# plus a flash, the same recolour-plus-flash mechanism galaxy_mockup's own
# replay uses (hud.gd's _advance_replay()) — a keyframe whose owner already
# matches is a harmless no-op recolour, still worth the flash as a "this
# system matters right now" narrative beat. Fired once per keyframe (keyed
# by tick+system_id, not just tick, since two keyframes can share a tick),
# not once per frame, and in a way that survives a Skip landing on the final
# tick in one jump (see _do_skip()).
func _apply_due_keyframes() -> void:
	var g: Galaxy = _galaxy_view.get_galaxy()
	if g == null:
		return
	for kf in _jump.keyframes:
		var kt := int(kf.get("tick", -1))
		if _tick < kt:
			continue
		var kid := String(kf.get("system_id", ""))
		var key := "%d:%s" % [kt, kid]
		if _fired_keyframes.has(key):
			continue
		_fired_keyframes[key] = true
		var sid := int(kid)
		if sid < 0 or sid >= g.systems.size():
			continue
		_galaxy_view.flash(sid, KEYFRAME_FLASH_COLOR)
		_galaxy_view.set_system_owner(sid, int(kf.get("owner", -1)))


func _apply_map_fraction() -> void:
	_map_viewport.anchor_right = _map_fraction
	_scroll.anchor_left = _map_fraction
	_scroll.visible = _map_fraction < 0.999


func _all_entries_printed() -> bool:
	if _jump.entries.is_empty():
		return false
	for e in _jump.entries:
		if _printed_words_for(e, _tick) < _word_count(e):
			return false
	return true


func _finish() -> void:
	if _phase == "done":
		return
	_phase = "done"
	_map_fraction = 1.0
	_apply_map_fraction()


func _word_count(e: Dictionary) -> int:
	return String(e.get("base_form", "")).split(" ", false).size()


func _printed_words_for(e: Dictionary, tick: int) -> int:
	var total := _word_count(e)
	if QaPlants.is_active("cadence-wallclock"):
		return clampi(int(Time.get_ticks_msec() / 80.0), 0, total)
	var start := int(e.get("tick_range_start", 0))
	if tick <= start:
		return 0
	return clampi(((tick - start) * 5) / 8, 0, total)


func _word_alphas_for(e: Dictionary, tick: int, total: int) -> PackedFloat32Array:
	var start := int(e.get("tick_range_start", 0))
	var out := PackedFloat32Array()
	out.resize(total)
	for i in range(total):
		var reveal := start + ((8 * (i + 1) + 4) / 5)
		out[i] = clampf(float(tick - reveal) / float(FADE_TICKS), 0.0, 1.0)
	return out


func _render_rows() -> Array:
	var rows: Array = []
	for e in _jump.entries:
		var start := int(e.get("tick_range_start", 0))
		if _tick < start:
			continue
		var total := _word_count(e)
		var printed := _printed_words_for(e, _tick)
		rows.append({
			"entry_id": e.get("entry_id", ""),
			"category": e.get("category", ""),
			"base_form": e.get("base_form", ""),
			"mentions": e.get("mentions", []),
			"printed_words": printed,
			"total_words": total,
			"alphas": _word_alphas_for(e, _tick, total),
			"expanded_text": _jump.expanded_text_for(e),
			"expanded_mentions": _jump.mentions_for(e, "expanded"),
		})
	return rows


func _owners_state() -> Dictionary:
	var out: Dictionary = {}
	var g: Galaxy = _galaxy_view.get_galaxy()
	if g == null:
		return out
	for sys in g.systems:
		out[sys.id] = sys.owner
	return out


func qa_state() -> Dictionary:
	var entries_state: Array = []
	for e in _jump.entries:
		var eid := String(e.get("entry_id", ""))
		var total := _word_count(e)
		var printed := _printed_words_for(e, _tick)
		entries_state.append({
			"entry_id": eid,
			"category": e.get("category", ""),
			"printed_words": printed,
			"total_words": total,
			"printed": printed >= total,
			"expanded": eid == _expanded_id,
		})
	return {
		"seed": _current_seed,
		"hash": _jump.hash(),
		"tick": _tick,
		"phase": _phase,
		"entries": entries_state,
		"expanded_id": _expanded_id,
		"owners": _owners_state(),
		"map_width_fraction": _map_fraction,
		"pace": {"word_interval_s": 0.08, "fade_s": 0.20},
		"dropped_entries": _jump.dropped_entries,
		"timing_ms": {"load": _load_ms},
		"regen_count": _regen_count,
	}


func qa_plant(id: String) -> bool:
	if not PLANTS.has(id):
		return false
	QaPlants.activate(id)
	_start_jump(_current_seed)
	return true


func qa_seed(n: int) -> void:
	_start_jump(n)


func qa_set(name: String, value) -> void:
	if name == "skip" and bool(value):
		_do_skip()


func qa_click_entry(entry) -> void:
	var target: Dictionary = {}
	if typeof(entry) == TYPE_INT or typeof(entry) == TYPE_FLOAT:
		var idx := int(entry)
		if idx >= 0 and idx < _jump.entries.size():
			target = _jump.entries[idx]
	else:
		var eid := String(entry)
		for e in _jump.entries:
			if String(e.get("entry_id", "")) == eid:
				target = e
				break
	if target.is_empty():
		return
	var printed := _printed_words_for(target, _tick)
	if printed < _word_count(target):
		return
	_expanded_id = String(target.get("entry_id", ""))
	_phase = "paused"
	_sync_view()


func qa_click_mention(kind: String, id: String) -> void:
	if kind == "region":
		var sid := int(id)
		_orbit_camera.focus_system(sid)


func qa_dismiss() -> void:
	if _expanded_id == "":
		return
	_expanded_id = ""
	if _phase == "paused":
		_phase = "narrating"
	_sync_view()


func qa_tick(n: int) -> void:
	var advancing := _phase == "narrating" or (_phase == "paused" and QaPlants.is_active("no-pause"))
	if advancing:
		for i in range(n):
			_tick += 1
			_apply_due_keyframes()
			if _all_entries_printed():
				_finish()
	_sync_view()


func _do_skip() -> void:
	_tick = max(_tick, _jump.total_span_ticks())
	_apply_due_keyframes()
	_expanded_id = ""
	_phase = "done"
	_map_fraction = 1.0
	_apply_map_fraction()
	_sync_view()
