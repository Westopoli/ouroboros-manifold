shader_type spatial;
render_mode blend_add, unshaded, depth_draw_never, fog_disabled, cull_disabled;

// VG-B25 star layer: one point per star, drawn static. The point grows with depth so a star
// stays between px_min and px_max pixels; the same formula is ambient_rig.gd star_pixel_size.
uniform float px_min = 1.0;
uniform float px_max = 3.0;
uniform float world_size = 0.1;

void vertex() {
	float d = max(length((MODELVIEW_MATRIX * vec4(VERTEX, 1.0)).xyz), 0.001);
	POINT_SIZE = clamp(world_size * VIEWPORT_SIZE.y * PROJECTION_MATRIX[1][1] / (2.0 * d), px_min, px_max);
}

void fragment() {
	ALBEDO = COLOR.rgb;
	ALPHA = COLOR.a;
}
