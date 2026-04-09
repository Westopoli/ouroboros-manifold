shader_type canvas_item;

uniform float density : hint_range(20.0, 200.0) = 80.0;
uniform float drift_speed : hint_range(0.001, 0.02) = 0.005;
uniform float twinkle_speed : hint_range(0.5, 4.0) = 1.5;
uniform vec3 tint_color = vec3(0.29, 0.62, 0.72);

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float hash2(vec2 p) {
	return fract(sin(dot(p, vec2(269.5, 183.3))) * 43758.5453);
}

void fragment() {
	vec4 result = vec4(0.0);

	for (float layer = 0.0; layer < 3.0; layer++) {
		float layer_density = density * (0.5 + layer * 0.3);
		float layer_drift = drift_speed * (1.0 + layer * 0.5);
		float layer_brightness = 0.3 + layer * 0.25;
		float layer_size = 0.0015 + layer * 0.001;

		for (float i = 0.0; i < 200.0; i++) {
			if (i >= layer_density) break;

			float seed = hash(vec2(i + layer * 1000.0, layer * 37.0));
			float seed2 = hash2(vec2(i + layer * 1000.0, layer * 37.0));

			vec2 star_pos = vec2(
				fract(seed + TIME * layer_drift * (seed2 - 0.5)),
				fract(seed2 + TIME * layer_drift * 0.3 * (seed - 0.5))
			);

			float dist = length(UV - star_pos);
			float star = smoothstep(layer_size, 0.0, dist);

			// Twinkle
			float twinkle_phase = seed * 6.28;
			float twinkle = 0.5 + 0.5 * sin(TIME * twinkle_speed * (0.8 + seed * 0.4) + twinkle_phase);

			float brightness = star * twinkle * layer_brightness;
			result.rgb += mix(vec3(1.0), tint_color, 0.4) * brightness;
		}
	}

	result.a = max(result.r, max(result.g, result.b));
	COLOR = result;
}
