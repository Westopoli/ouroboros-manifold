shader_type canvas_item;

uniform float opacity : hint_range(0.0, 0.1) = 0.03;

void fragment() {
	float line = mod(SCREEN_UV.y * (1.0 / SCREEN_PIXEL_SIZE.y), 4.0);
	float scanline_alpha = step(2.0, line) * opacity;
	COLOR = vec4(0.0, 0.0, 0.0, scanline_alpha);
}
