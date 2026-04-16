## Draws all units each frame using dead-reckoned positions from TacticalBridge.
## Units are faction-colored circles with layer indicator rings.
## HP ratio dims the fill; selection-eligible (player) units get a white outline.
extends Node2D

const UNIT_RADIUS := 40.0   # world units

# Layer indicator ring sits just outside the unit circle
const RING_GAP    := 8.0    # gap between unit edge and ring centre
const RING_WIDTH  := 5.0

# Faction → fill color
const FACTION_COLORS: Array[Color] = [
	Color(0.25, 0.60, 1.00),  # 0 — player (blue)
	Color(1.00, 0.28, 0.22),  # 1 — enemy  (red)
	Color(0.25, 0.90, 0.40),  # 2 — ally   (green)
	Color(1.00, 0.80, 0.20),  # 3 — neutral (yellow)
]
const FACTION_DEFAULT := Color(0.7, 0.7, 0.7)

# Layer → ring color. Layer 0 → no ring.
const LAYER_COLORS: Array[Color] = [
	Color.TRANSPARENT,        # 0 — ground (no ring)
	Color(0.00, 1.00, 1.00),  # 1 — cyan
	Color(1.00, 1.00, 0.00),  # 2 — yellow
	Color(1.00, 0.55, 0.00),  # 3 — orange
	Color(0.75, 0.20, 1.00),  # 4 — magenta
]


func _process(_delta: float) -> void:
	queue_redraw()


func _draw() -> void:
	for uid: int in TacticalBridge.display_positions:
		var pos_arr: Array = TacticalBridge.display_positions[uid]
		var pos := Vector2(float(pos_arr[0]), float(pos_arr[1]))

		var unit: Dictionary = TacticalBridge.units.get(uid, {})
		var faction: int = unit.get("faction", 0)
		var layer: int   = unit.get("layer", 0)
		var hp: float    = float(unit.get("hp", 100))
		var max_hp: float = float(unit.get("max_hp", 100))

		# Layer ring (drawn first so it appears behind the unit)
		if layer > 0 and layer < LAYER_COLORS.size():
			var ring_col: Color = LAYER_COLORS[layer]
			if ring_col.a > 0.0:
				draw_arc(pos, UNIT_RADIUS + RING_GAP, 0.0, TAU, 36, ring_col, RING_WIDTH)

		# Unit fill — hp-based alpha
		var hp_ratio: float = hp / max_hp if max_hp > 0.0 else 1.0
		var base_col: Color = FACTION_COLORS[faction] if faction < FACTION_COLORS.size() else FACTION_DEFAULT
		var fill_col := Color(base_col.r, base_col.g, base_col.b, lerpf(0.35, 1.0, hp_ratio))
		draw_circle(pos, UNIT_RADIUS, fill_col)

		# Player-selectable units: thin white outline
		if unit.get("selection_eligible", false):
			draw_arc(pos, UNIT_RADIUS, 0.0, TAU, 36, Color.WHITE, 2.0)
