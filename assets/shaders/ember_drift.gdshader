shader_type canvas_item;

uniform float particle_count : hint_range(5.0, 50.0) = 20.0;
uniform float rise_speed : hint_range(0.01, 0.2) = 0.05;
uniform vec3 ember_color = vec3(0.788, 0.659, 0.298);

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	vec4 result = vec4(0.0);

	// Warm base gradient at bottom
	float gradient = smoothstep(1.0, 0.8, UV.y) * 0.04;
	result.rgb += ember_color * gradient;

	// Ember particles
	for (float i = 0.0; i < 50.0; i++) {
		if (i >= particle_count) break;

		float seed = hash(vec2(i, i * 7.31));
		float x = hash(vec2(i * 3.17, seed));
		float phase = hash(vec2(seed, i * 13.37));

		// Rising motion with wrap
		float y = fract(1.0 - (TIME * rise_speed * (0.5 + seed * 0.5) + phase));

		// Horizontal sway
		x += sin(TIME * 0.8 + phase * 6.28) * 0.03;

		vec2 particle_pos = vec2(x, y);
		float dist = length(UV - particle_pos);

		// Soft circle
		float size = 0.003 + seed * 0.004;
		float brightness = smoothstep(size, size * 0.2, dist);

		// Fade in at bottom, fade out at top
		float fade = smoothstep(0.95, 0.8, y) * smoothstep(0.05, 0.2, y);

		result.rgb += ember_color * brightness * fade * 0.4;
	}

	result.a = max(result.r + result.g + result.b, gradient);
	COLOR = result;
}
