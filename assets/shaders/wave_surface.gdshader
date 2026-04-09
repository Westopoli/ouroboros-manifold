shader_type canvas_item;

uniform float wave_count : hint_range(2.0, 8.0) = 4.0;
uniform float wave_speed : hint_range(0.2, 2.0) = 0.8;
uniform vec3 wave_color = vec3(0.545, 0.604, 0.235);

void fragment() {
	vec4 result = vec4(0.0);

	// Waves only in bottom third
	float wave_zone = smoothstep(0.6, 0.7, UV.y);

	for (float i = 0.0; i < 8.0; i++) {
		if (i >= wave_count) break;

		float freq = 3.0 + i * 1.8;
		float amp = 0.008 - i * 0.001;
		float speed_offset = wave_speed * (1.0 + i * 0.2);
		float y_offset = 0.68 + i * 0.06;

		float wave_y = y_offset + sin(UV.x * freq * 6.28 + TIME * speed_offset) * amp;
		wave_y += sin(UV.x * freq * 3.14 * 0.7 + TIME * speed_offset * 0.6 + i) * amp * 0.5;

		float dist = abs(UV.y - wave_y);
		float line = smoothstep(0.003, 0.0005, dist);

		float opacity = 0.3 - i * 0.04;
		result.rgb += wave_color * line * opacity;
	}

	result.rgb *= wave_zone;
	result.a = max(result.r, max(result.g, result.b));
	COLOR = result;
}
