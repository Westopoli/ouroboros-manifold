extends RefCounted

## H-023 unit-scale scene: the numbers, the stage layout, the metrics and the values-file read/write.
## Every number not cited is a named DRAFT (docs/stories/H-023.md "Drafts for Westley"); the stage is shown on screen.

const VALUES_PATH := "res://data/unit_scale.toml"
const ROLES: Array[String] = ["Raider", "Interceptor", "Vanguard", "Warden", "Bombard", "Bastion"]

# Walk speed in world units per second: OM_ROSTER_*_SPEED, csrc/om_constants.h:484 (Bastion), :491 (Bombard), :497 (Interceptor),
# :503 (Raider), :509 (Vanguard), :515 (Warden); Raider 150 and Bastion 40 also at docs/bible/epics/E-01-layer-system.md:91.
const WALK_SPEED := {"Raider": 150.0, "Interceptor": 130.0, "Vanguard": 80.0, "Warden": 70.0, "Bombard": 50.0, "Bastion": 40.0}

const BASE_RADIUS := 15.0  # DRAFT-start-radius: OM_UNIT_COLLISION_RADIUS, csrc/om_constants.h:581
const START_VISUAL_SCALE := 1.0  # DRAFT-start-visual-scale
const SCALE_MIN := 0.25  # DRAFT-slider-min
const SCALE_MAX := 2.0  # DRAFT-slider-max
# DRAFT-slider-ties-radius: the slider moves visual_scale and sets radius = BASE_RADIUS * visual_scale; the file may hold any pair.

const STAGE_W := 4000.0  # DRAFT-stage-width, world units
const STAGE_H := 2200.0  # DRAFT-stage-height, world units
const WU_PER_METRE := 10.0  # DRAFT-wu-per-metre: 1 m = 10 wu, so the 1.8 m human is 18 wu
const HUMAN_HEIGHT_M := 1.8  # DRAFT-human-height
const HUMAN_SHOULDER_M := 0.5  # DRAFT-human-shoulder-width
const CHOKE_CENTRE := Vector2(1750.0, 1100.0)
const CHOKE_WIDTH := 200.0  # DRAFT-choke-gap-width, the narrowest choke on stage, world units
const CITY_CENTRE := Vector2(3300.0, 1500.0)
const CITY_RADIUS := 400.0  # DRAFT-city-footprint-radius, world units
const LAYER_STEP_WU := 150.0  # scenes/ground3d/slope_view.gd LAYER_STEP_WU (named draft there): height of one band step
const SLOPE_LENGTH := 600.0  # R-004-07 (600 wu slope)
# Influence radii in play (docs/bible/algorithms.md ALG-71, ALG-75): chokepoint 600, vantage 700, hazard anchor 500, capture 300.
const CHOKE_RADIUS := 600.0
const VANTAGE_RADIUS := 700.0
const HAZARD_RADIUS := 500.0
const CAPTURE_RADIUS := 300.0

# E-17 node kinds on land plus cover, slope with height bands, city footprint. x, y in stage world units (DRAFT layout).
const POSITIONS: Array = [
	{"kind": "objective", "x": 3300.0, "y": 1500.0, "radius": 300.0},
	{"kind": "staging", "x": 400.0, "y": 1100.0, "radius": 250.0},
	{"kind": "transit", "x": 1000.0, "y": 1100.0, "radius": 0.0},
	{"kind": "chokepoint", "x": 1750.0, "y": 1100.0, "radius": 600.0},
	{"kind": "flank_route", "x": 1500.0, "y": 1950.0, "radius": 0.0},
	{"kind": "vantage", "x": 2200.0, "y": 450.0, "radius": 700.0},
	{"kind": "hazard_anchor", "x": 2500.0, "y": 1700.0, "radius": 500.0},
	{"kind": "cover_obstacle", "x": 2200.0, "y": 1100.0, "radius": 0.0},
	{"kind": "slope", "x": 3000.0, "y": 300.0, "radius": 0.0},
	{"kind": "height_bands", "x": 3000.0, "y": 300.0, "radius": 0.0},
	{"kind": "city_footprint", "x": 3300.0, "y": 1500.0, "radius": 400.0},
]


static func defaults() -> Dictionary:
	var out := {}
	for r in ROLES:
		out[r] = {"radius": BASE_RADIUS, "visual_scale": START_VISUAL_SCALE}
	return out


## Reads the values file; a missing file or key keeps the DRAFT start value.
static func load_values() -> Dictionary:
	var out := defaults()
	if not FileAccess.file_exists(VALUES_PATH):
		return out
	var f := FileAccess.open(VALUES_PATH, FileAccess.READ)
	if f == null:
		return out
	var table := ""
	while not f.eof_reached():
		var line := f.get_line().strip_edges()
		if line == "" or line.begins_with("#"):
			continue
		if line.begins_with("[") and line.ends_with("]"):
			table = line.substr(1, line.length() - 2).strip_edges()
			continue
		var eq := line.find("=")
		if eq < 0 or not out.has(table):
			continue
		var key := line.substr(0, eq).strip_edges()
		var val := line.substr(eq + 1).strip_edges()
		if (key == "radius" or key == "visual_scale") and val.is_valid_float():
			out[table][key] = float(val)
	return out


static func save_values(values: Dictionary) -> bool:
	var f := FileAccess.open(VALUES_PATH, FileAccess.WRITE)
	if f == null:
		return false
	f.store_line("# H-023 unit-scale values file (DRAFT path). radius: collision radius, world units. visual_scale: look multiplier.")
	f.store_line("# Written by scenes/proto/unit_scale/unit_scale.tscn on every slider change. The sim does not read it yet.")
	for r in ROLES:
		f.store_line("")
		f.store_line("[%s]" % r)
		f.store_line("radius = %.3f" % float(values[r]["radius"]))
		f.store_line("visual_scale = %.3f" % float(values[r]["visual_scale"]))
	return true


## The four metrics of the story's metrics panel for one role.
static func metrics(role: String, radius: float) -> Dictionary:
	var diameter := 2.0 * radius
	return {
		"radius_world_units": radius,
		"units_abreast": int(floor(CHOKE_WIDTH / diameter)),
		"units_to_ring_city": int(ceil(TAU * (CITY_RADIUS + radius) / diameter)),
		"seconds_to_cross_stage": STAGE_W / float(WALK_SPEED[role]),
	}


static func human_height_wu() -> float:
	return HUMAN_HEIGHT_M * WU_PER_METRE


static func human_shoulder_wu() -> float:
	return HUMAN_SHOULDER_M * WU_PER_METRE
