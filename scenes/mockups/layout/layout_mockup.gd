extends Control
# Layout prototype pass 1: flat diagram of a generated layout. Throwaway; never loaded by the game.
# Spec: docs/northstar/plans/2026-10-04-layout-prototype-pass1-spec.md.
# Keys: A archetype, Left/Right seed, S sides switch, G growth, V view, Tab map/sheet, [ ] replay, L labels, H help.
# Screenshot: -- --shot out.png --archetype assault --seed 4 --view map|sheet|replay [--step n] [--sym mirror|rotate|separate]
#             [--growth 0] [--labels] [--hover x,y] [--size 1600x900]
# See also: layout_gen.gd (data), layout_view.gd (drawing).

const Gen := preload("res://scenes/mockups/layout/layout_gen.gd")
const Checks := preload("res://scenes/mockups/layout/layout_checks.gd")
const View := preload("res://scenes/mockups/layout/layout_view.gd")
const VIEWS := ["map", "sheet", "replay"]

var gen
var view
var arch_i := 0
var seed_ := 1
var sym_i := 0
var growth := true
var view_i := 0
var step := 0
var cache := {}
var shot := ""


func _ready() -> void:
	DisplayServer.window_set_title("Layout mockup")
	gen = Gen.new()
	view = View.new()
	view.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(view)
	view.opened.connect(_on_opened)
	_args()
	_refresh()
	if shot != "":
		await get_tree().process_frame
		await get_tree().process_frame
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(shot)
		print("saved ", shot, "  default text area: %.2f%% of window" % (100.0 * view.text_px / (view.size.x * view.size.y)))
		get_tree().quit()


func _args() -> void:
	var a := OS.get_cmdline_user_args()
	var i := 0
	while i < a.size():
		match a[i]:
			"--shot":
				i += 1
				shot = a[i]
				var win := get_window()
				win.size = Vector2i(1600, 900)
			"--archetype":
				i += 1
				arch_i = maxi(Gen.ARCHETYPES.find(a[i]), 0)
			"--seed":
				i += 1
				seed_ = int(a[i])
			"--view":
				i += 1
				view_i = maxi(VIEWS.find(a[i]), 0)
			"--step":
				i += 1
				step = int(a[i])
			"--sym":
				i += 1
				sym_i = maxi(Gen.SYM_MODES.find(a[i]), 0)
			"--growth":
				i += 1
				growth = a[i] != "0"
			"--labels":
				view.labels_on = true
			"--hover":
				i += 1
				var xy := a[i].split(",")
				view.mouse = Vector2(float(xy[0]), float(xy[1]))
				view.pinned = true
			"--size":
				i += 1
				var wh := a[i].split("x")
				get_window().size = Vector2i(int(wh[0]), int(wh[1]))
		i += 1


func _sheet() -> Array:
	var key := "%s|%s|%s" % [Gen.ARCHETYPES[arch_i], Gen.SYM_MODES[sym_i], growth]
	if not cache.has(key):
		var maps := []
		var sigs := []
		for sd in range(1, 13):
			var m: Dictionary = gen.make(Gen.ARCHETYPES[arch_i], sd, {"sym": Gen.SYM_MODES[sym_i], "growth": growth, "recent": sigs})
			sigs.append(m["signature"])
			maps.append(m)
		cache[key] = maps
	return cache[key]


func _refresh() -> void:
	var maps := _sheet()
	view.sheet = maps
	var dists := []
	for i in maps.size():
		var d := INF
		for j in maps.size():
			if i != j:
				d = minf(d, Checks.sig_distance(maps[i]["signature"], maps[j]["signature"]))
		dists.append(d)
	view.sheet_dist = dists
	if seed_ >= 1 and seed_ <= 12:
		view.map = maps[seed_ - 1]
	else:
		view.map = gen.make(Gen.ARCHETYPES[arch_i], seed_, {"sym": Gen.SYM_MODES[sym_i], "growth": growth})
	var steps: Array = view.map["steps"]
	step = clampi(step, 0, steps.size() - 1)
	view.mode = VIEWS[view_i]
	view.step = step
	var h := "%s · seed %d · sides: %s · growth %s · view: %s" % [view.map["title"], seed_, Gen.SYM_MODES[sym_i], "on" if growth else "off", VIEWS[view_i]]
	if view_i == 2:
		h += " · step %d/%d · %s" % [step + 1, steps.size(), steps[step]["text"]]
	elif view_i == 0:
		h += " · H help"
	view.header = h
	view.queue_redraw()


func _on_opened(i: int) -> void:
	seed_ = i + 1
	view_i = 0
	_refresh()


func _unhandled_key_input(ev: InputEvent) -> void:
	if not (ev is InputEventKey) or not ev.pressed or ev.echo:
		return
	match (ev as InputEventKey).keycode:
		KEY_A:
			arch_i = (arch_i + 1) % Gen.ARCHETYPES.size()
		KEY_LEFT:
			seed_ = maxi(1, seed_ - 1)
		KEY_RIGHT:
			seed_ += 1
		KEY_S:
			sym_i = (sym_i + 1) % Gen.SYM_MODES.size()
		KEY_G:
			growth = not growth
		KEY_V:
			view_i = (view_i + 1) % VIEWS.size()
			step = 0
		KEY_TAB:
			view_i = 1 if view_i != 1 else 0
		KEY_BRACKETLEFT:
			step -= 1
			view_i = 2
		KEY_BRACKETRIGHT:
			step += 1
			view_i = 2
		KEY_L:
			view.labels_on = not view.labels_on
		KEY_H:
			view.help_on = not view.help_on
		KEY_ESCAPE:
			view.help_on = false
		_:
			return
	_refresh()
