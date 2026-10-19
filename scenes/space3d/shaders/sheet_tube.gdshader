shader_type spatial;
// VG-D-VIEW unit 1: the one material of every asteroid slab and cell square of SpaceSheets (d-view spec "Vision tube").
// A sheet above the focus sheet is see-through inside the tube (world x/z cylinder test) and shows a rim line at the tube edge in
// its layer colour. Vertex COLOR.r < 0.5 marks a mass slab (kit "mass" colour); anything else is a sheet slab or cell square.
// depth_prepass_alpha: the opaque parts of a sheet still write depth while the faded parts blend.
render_mode cull_disabled, depth_prepass_alpha;

uniform bool tube_on = false;
uniform vec2 tube_center = vec2(0.0);   // world x, z
uniform float tube_radius = 1500.0;     // DRAFT-tube-radius, set by SpaceSheets.set_tube
uniform float focus_y = 0.0;            // world y of the focus sheet, set by SpaceSheets.set_tube
uniform float tube_alpha = 0.15;        // DRAFT-tube-alpha
uniform float rim_wu = 10.0;            // DRAFT-tube-rim
uniform float rim_min_px = 3.0;         // DRAFT-ring-px: the rim reads at least this many pixels at any camera height
uniform float rim_period_s = 1.5;       // spec: the rim alpha pulses 0.6 to 1.0 over 1.5 s
uniform float layer_gap = 1000.0;       // DRAFT-space-layer-gap, set by SpaceSheets
uniform vec4 layer_colours[5];          // LayerView.LAYER_COLOURS: the rim colour of each sheet
uniform vec4 sheet_colours[5];          // kit "layers", dimmed on the non-focus sheets (DRAFT-sheet-dim), set by SpaceSheets
uniform vec4 mass_colours[5];           // kit "mass", dimmed the same way

varying vec3 world_pos;

vec3 to_linear(vec3 c) {
	return mix(c / 12.92, pow((c + vec3(0.055)) / 1.055, vec3(2.4)), step(vec3(0.04045), c));
}

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	int layer = clamp(int(floor(world_pos.y / layer_gap + 0.5)), 0, 4);
	vec3 base = COLOR.r < 0.5 ? mass_colours[layer].rgb : sheet_colours[layer].rgb;
	ALBEDO = to_linear(base);
	ROUGHNESS = 1.0;
	bool faded_sheet = tube_on && float(layer) * layer_gap > focus_y + 0.5 * layer_gap;
	if (faded_sheet) {
		float px_wu = -VERTEX.z * 2.0 / (PROJECTION_MATRIX[1][1] * VIEWPORT_SIZE.y);
		float rim_w = max(rim_wu, rim_min_px * px_wu);
		float d = distance(world_pos.xz, tube_center);
		if (abs(d - tube_radius) < 0.5 * rim_w) {
			vec3 rim = to_linear(layer_colours[layer].rgb);
			ALBEDO = rim;
			EMISSION = rim;
			ALPHA = 0.8 + 0.2 * sin(TIME * TAU / rim_period_s);  // 0.8 +- 0.2 = the spec's 0.6 to 1.0
		} else if (d < tube_radius) {
			ALPHA = tube_alpha;
		}
	}
}
