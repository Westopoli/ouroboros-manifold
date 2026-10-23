extends Control

var _scroll_panel: Node
var _queued_ids: Array[String] = []
var _print_index: int = 0

const MOCK_ENTRIES := [
	{
		"entry_id": "e_01",
		"base_form": "In the decades that followed the fall of Korrath Station, the Settled Reach entered a period of uneasy calm. Trade routes solidified along the Outer Spiral, and the frontier garrisons reported fewer incursions than any generation could remember.",
		"expanded_form": "In the decades that followed the fall of Korrath Station, the Settled Reach entered a period of uneasy calm. Trade routes solidified along the Outer Spiral, and the frontier garrisons reported fewer incursions than any generation could remember. Commander Vasek of the Third Expeditionary maintained a watchful presence along the border, though some whispered his caution bordered on timidity. The economy recovered slowly, buoyed by mineral extraction from the newly charted Pellian Belt.",
	},
	{
		"entry_id": "e_02",
		"base_form": "The Herath Dominion pressed westward without warning, their fleets materializing along supply corridors thought secure. Three border stations fell before word reached the capital.",
		"expanded_form": "The Herath Dominion pressed westward without warning, their fleets materializing along supply corridors thought secure. Three border stations fell before word reached the capital. The offensive bore the hallmarks of Admiral Torek's doctrine — overwhelming force concentrated on logistical chokepoints rather than population centers. By the time the Reach's reserve fleet mobilized, the Dominion had already fortified their gains.",
	},
	{
		"entry_id": "e_03",
		"base_form": "A generation passed. The children born during the Herath offensive grew to serve in a military that remembered the cost of complacency. The Vasek line endured, though diminished.",
		"expanded_form": "A generation passed. The children born during the Herath offensive grew to serve in a military that remembered the cost of complacency. The Vasek line endured, though diminished — three of the commander's grandchildren took commissions in the frontier guard, following a tradition that had become less a choice than an inheritance. The family name still carried weight in the officer corps, though the weight had shifted from pride to obligation.",
	},
]


func _ready() -> void:
	_build_ui()


func _build_ui() -> void:
	var bg := ColorRect.new()
	bg.color = ThemeConstants.BASE
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)

	var left := VBoxContainer.new()
	left.set_anchors_preset(Control.PRESET_LEFT_WIDE)
	left.anchor_right = 0.3
	left.offset_left = 20
	left.offset_top = 20
	left.offset_right = -10
	left.add_theme_constant_override("separation", 8)
	add_child(left)

	var title := Label.new()
	title.text = "Chronicle Scroll Test"
	title.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	title.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	title.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	left.add_child(title)

	var subtitle := Label.new()
	subtitle.text = "3 mock entries, word-by-word fade"
	subtitle.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	subtitle.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
	subtitle.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	left.add_child(subtitle)

	_add_button(left, "1. Begin time jump", _on_begin)
	_add_button(left, "2. Queue all entries", _on_queue_all)
	_add_button(left, "3. Print next entry", _on_print_next)
	_add_button(left, "Pause", _on_pause)
	_add_button(left, "Resume", _on_resume)
	_add_button(left, "End time jump", _on_end)

	var spacer := Control.new()
	spacer.custom_minimum_size.y = 20
	left.add_child(spacer)

	_add_button(left, "Slide panel in", _on_slide_in)
	_add_button(left, "Slide panel out", _on_slide_out)

	var panel_scene := load("res://scenes/world/chronicle_scroll_panel.tscn")
	_scroll_panel = panel_scene.instantiate()
	_scroll_panel.set_anchors_preset(Control.PRESET_RIGHT_WIDE)
	_scroll_panel.anchor_left = 1.0 - 0.38
	add_child(_scroll_panel)

	_scroll_panel.entry_finished_printing.connect(func(id: String):
		print("[chronicle] Entry finished printing: ", id)
	)
	_scroll_panel.entry_expansion_opened.connect(func(id: String):
		print("[chronicle] Expansion opened: ", id)
	)
	_scroll_panel.entry_expansion_closed.connect(func(id: String):
		print("[chronicle] Expansion closed: ", id)
	)
	_scroll_panel.all_entries_finished.connect(func():
		print("[chronicle] All entries finished!")
	)


func _add_button(parent: Control, text: String, callback: Callable) -> void:
	var btn := Button.new()
	btn.text = text
	btn.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	btn.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
	btn.pressed.connect(callback)
	parent.add_child(btn)


func _on_begin() -> void:
	_queued_ids.clear()
	_print_index = 0
	_scroll_panel.begin_time_jump(MOCK_ENTRIES.size())
	print("[chronicle] Time jump begun, expecting %d entries" % MOCK_ENTRIES.size())


func _on_queue_all() -> void:
	for entry in MOCK_ENTRIES:
		_scroll_panel.queue_entry(entry)
		_queued_ids.append(entry["entry_id"])
	print("[chronicle] Queued %d entries" % MOCK_ENTRIES.size())


func _on_print_next() -> void:
	if _print_index < _queued_ids.size():
		var id := _queued_ids[_print_index]
		_scroll_panel.start_printing(id)
		_print_index += 1
		print("[chronicle] Started printing: ", id)
	else:
		print("[chronicle] No more entries to print")


func _on_pause() -> void:
	_scroll_panel.pause()
	print("[chronicle] Paused")


func _on_resume() -> void:
	_scroll_panel.resume()
	print("[chronicle] Resumed")


func _on_end() -> void:
	_scroll_panel.end_time_jump()
	print("[chronicle] Time jump ended")


func _on_slide_in() -> void:
	_scroll_panel.slide_in()


func _on_slide_out() -> void:
	_scroll_panel.slide_out()
