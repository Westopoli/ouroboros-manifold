shader_type spatial;
render_mode blend_add, unshaded, depth_draw_never, fog_disabled, cull_disabled;

// VG-B25 wash: a dim glow that depends on the view direction only. The sphere mesh is built
// once in ambient_rig.gd with the additive colour in CUSTOM0; this shader pins every vertex
// to a fixed distance in front of the camera, so the wash never changes with position.
const float DISTANCE = 1000.0;

varying vec3 wash;

void vertex() {
	wash = CUSTOM0.rgb;
	vec3 cam = INV_VIEW_MATRIX[3].xyz;
	POSITION = PROJECTION_MATRIX * VIEW_MATRIX * vec4(cam + normalize(VERTEX) * DISTANCE, 1.0);
}

void fragment() {
	ALBEDO = wash;
	ALPHA = 1.0;
}
