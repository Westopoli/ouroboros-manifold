extends Control

# Wave 2 visual check — runs the two Wave 2 UI changes through a paced sequence
# so Westley can read + verify each step before it advances.
#
# Pacing model:
#   - Each step prints a banner to console explaining what's being shown.
#   - Each step waits a fixed duration AND waits for Westley to press SPACE/ENTER
#     before advancing. Whichever happens first.
#   - Final state holds until Westley closes the window manually.
#
# Sequence:
#   Step 1  Briefing scene loaded with mock data (objective_primary has detail).
#   Step 2  Primary objective [+] toggle programmatically pressed → detail expands.
#   Step 3  Briefing torn down; tactical-ish dim backdrop swaps in.
#   Step 4  tutorial_overlay.show_beat("TUT_001") — anchor=center, card at bottom-center.
#   Step 5  tutorial_overlay.show_beat("TUT_004") — anchor=objective_hud, card tweens to bottom-left.
#   Step 6  HOLD — sequence done. Press SPACE to quit.

const STEP_TIMEOUT := 12.0  # seconds per step before auto-advance

var _briefing: Control = null
var _overlay: Control = null
var _backdrop: ColorRect = null
var _advance := false
var _hud: Label = null


func _ready() -> void:
	_build_hud()
	_run_sequence()


func _build_hud() -> void:
	_hud = Label.new()
	_hud.text = ""
	_hud.add_theme_color_override("font_color", Color(1, 1, 1, 1))
	_hud.add_theme_color_override("font_outline_color", Color(0, 0, 0, 1))
	_hud.add_theme_constant_override("outline_size", 6)
	_hud.position = Vector2(20, 20)
	_hud.z_index = 1000
	_hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_hud)


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_SPACE or event.keycode == KEY_ENTER:
			_advance = true


func _set_hud(text: String) -> void:
	if _hud != null:
		_hud.text = text


func _wait_step(label: String) -> void:
	print("\n=== ", label, " ===")
	print("(press SPACE/ENTER to advance, or wait ", STEP_TIMEOUT, "s)")
	_set_hud("%s\n[SPACE/ENTER to advance | auto in %ds]" % [label, int(STEP_TIMEOUT)])
	_advance = false
	var elapsed := 0.0
	var tick := 0.1
	while elapsed < STEP_TIMEOUT and not _advance:
		await get_tree().create_timer(tick).timeout
		elapsed += tick


func _run_sequence() -> void:
	_show_briefing()
	await _wait_step("Step 1/5 — Briefing scene loaded (look for objective text + [+] toggle)")

	_click_briefing_expand_toggle()
	await _wait_step("Step 2/5 — Briefing [+] toggle programmatically pressed (detail should be expanded)")

	_teardown_briefing()
	_setup_backdrop()
	await _wait_step("Step 3/5 — Briefing torn down, dim backdrop in (next: tutorial overlay)")

	_show_overlay_beat("TUT_001")
	await _wait_step("Step 4/5 — tutorial_overlay show_beat('TUT_001') — anchor=center, card at bottom-center")

	_show_overlay_beat("TUT_004")
	await _wait_step("Step 5/5 — show_beat('TUT_004') — anchor=objective_hud, card tweens to bottom-left")

	_set_hud("Done. Press SPACE to quit.")
	print("\n=== Sequence complete. Press SPACE to quit. ===")
	_advance = false
	while not _advance:
		await get_tree().create_timer(0.1).timeout

	print("wave2_visual_check: quitting.")
	get_tree().quit()


func _show_briefing() -> void:
	var scene := load("res://scenes/mission_briefing/mission_briefing.tscn")
	_briefing = scene.instantiate()
	_briefing.set_anchors_preset(Control.PRESET_FULL_RECT)
	if _briefing.has_method("setup"):
		_briefing.setup({"mission_id": "mock_001"})
	add_child(_briefing)
	move_child(_briefing, 0)  # behind HUD
	print("wave2_visual_check: briefing rendered (children=%d)" % _briefing.get_child_count())


func _click_briefing_expand_toggle() -> void:
	if _briefing == null:
		return
	var btn := _find_expand_toggle(_briefing)
	if btn == null:
		print("wave2_visual_check: WARN — expand toggle button not found on briefing card.")
		print("  Dumping all Button nodes in briefing tree for debug:")
		_dump_buttons(_briefing, 0)
		return
	btn.emit_signal("pressed")
	print("wave2_visual_check: briefing toggle button pressed (text='%s')" % btn.text)


func _dump_buttons(node: Node, depth: int) -> void:
	if node is Button:
		var btn := node as Button
		print("  %s- Button text='%s' visible=%s" % [
			"  ".repeat(depth), btn.text.replace("\n", "\\n"), str(btn.visible)
		])
	for child in node.get_children():
		_dump_buttons(child, depth + 1)


func _find_expand_toggle(node: Node) -> Button:
	if node is Button:
		var btn := node as Button
		var t := btn.text.strip_edges()
		# Accept "[+]" or "[-]" or "+" or "-" (defensive against Agent E's exact glyph choice).
		if t == "[+]" or t == "[-]" or t == "+" or t == "-":
			return btn
	for child in node.get_children():
		var found := _find_expand_toggle(child)
		if found != null:
			return found
	return null


func _teardown_briefing() -> void:
	if _briefing != null:
		_briefing.queue_free()
		_briefing = null


func _setup_backdrop() -> void:
	_backdrop = ColorRect.new()
	_backdrop.color = Color(0.05, 0.07, 0.10, 1.0)
	_backdrop.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_backdrop)
	move_child(_backdrop, 0)  # behind HUD


func _show_overlay_beat(beat_id: String) -> void:
	if _overlay == null:
		var scene := load("res://scenes/tutorial/tutorial_overlay.tscn")
		_overlay = scene.instantiate()
		_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
		add_child(_overlay)
	if _overlay.has_method("show_beat"):
		_overlay.show_beat(beat_id)
		print("wave2_visual_check: overlay show_beat('%s')" % beat_id)
	else:
		print("wave2_visual_check: WARN — overlay has no show_beat method.")
