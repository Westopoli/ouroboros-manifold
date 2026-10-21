shader_type spatial;
render_mode blend_add, unshaded, depth_draw_never, fog_disabled, cull_disabled;

// VG-B25 camera dust: billboard motes; the per-instance colour carries the tint and the fade
// toward the box faces in its alpha. TIME drives the twinkle only.
const float ENERGY = 1.5;

varying float twinkle;

void vertex() {
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
	twinkle = 0.7 + 0.3 * sin(TIME * 1.5 + float(INSTANCE_ID) * 0.7);
}

void fragment() {
	ALBEDO = COLOR.rgb * ENERGY;
	ALPHA = COLOR.a * twinkle;
}
