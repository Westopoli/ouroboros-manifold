shader_type canvas_item;

uniform sampler2D system_data : filter_nearest;
uniform sampler2D faction_colors : filter_nearest;
uniform sampler2D faction_borders : filter_nearest;
uniform int system_count = 0;

uniform float influence_radius : hint_range(0.05, 0.35) = 0.17;
uniform float threshold : hint_range(0.05, 0.80) = 0.66;

// Tube outline — symmetric glow centered on the threshold isoline
uniform float tube_width : hint_range(0.01, 0.15) = 0.04;
uniform float tube_alpha : hint_range(0.1, 1.0) = 0.95;

uniform float fill_opacity : hint_range(0.0, 0.60) = 0.16;
uniform float fill_fade_depth : hint_range(0.1, 2.0) = 0.8;

uniform float gap_margin : hint_range(0.0, 0.40) = 0.30;

void fragment() {
	float faction_fields[8];
	for (int fi = 0; fi < 8; fi++) {
		faction_fields[fi] = 0.0;
	}

	for (int i = 0; i < system_count; i++) {
		float u = (float(i) + 0.5) / 128.0;
		vec4 sys = texture(system_data, vec2(u, 0.5));
		vec2 sys_pos = sys.rg;
		float sys_faction_norm = sys.b;
		float sys_sig = sys.a;

		int fi = int(round(sys_faction_norm * 8.0)) - 1;
		if (fi >= 0 && fi < 8) {
			float d = distance(UV, sys_pos);
			float r = influence_radius * (0.6 + sys_sig * 0.4);
			float influence = (r * r) / (d * d + r * r);
			faction_fields[fi] += influence;
		}
	}

	int best_faction = -1;
	float best_field = 0.0;
	float second_field = 0.0;
	for (int fi = 0; fi < 8; fi++) {
		if (faction_fields[fi] > best_field) {
			second_field = best_field;
			best_field = faction_fields[fi];
			best_faction = fi;
		} else if (faction_fields[fi] > second_field) {
			second_field = faction_fields[fi];
		}
	}

	if (best_faction < 0) {
		COLOR = vec4(0.0);
	} else {
		bool rival_present = second_field > threshold * 0.15;
		bool in_gap = rival_present && (best_field - second_field) < gap_margin;

		float fc_u = (float(best_faction) + 0.5) / 8.0;
		vec3 fill_color = texture(faction_colors, vec2(fc_u, 0.5)).rgb;
		vec3 border_color = texture(faction_borders, vec2(fc_u, 0.5)).rgb;

		// Signed distance from the effective boundary (positive = inside, negative = outside)
		float field_above = best_field - threshold;
		float effective_dist = field_above;
		if (rival_present) {
			float gap_above = best_field - (second_field + gap_margin);
			effective_dist = min(field_above, gap_above);
		}

		// Tube outline: symmetric gaussian centered on the boundary
		float tube_t = effective_dist / tube_width;
		float tube_strength = exp(-tube_t * tube_t * 3.0);
		float tube_a = tube_strength * tube_alpha;

		bool inside = effective_dist >= 0.0 && !in_gap;

		if (inside) {
			// Interior fill: fades from outline toward center
			float fill_depth = max(effective_dist - tube_width, 0.0);
			float fill_t = max(0.0, 1.0 - fill_depth / fill_fade_depth);
			float fill_smooth = fill_t * fill_t;
			float fill_a = fill_opacity * fill_smooth;

			// Blend: tube outline overrides fill near boundary
			float alpha = max(fill_a, tube_a);
			vec3 out_color = mix(fill_color, border_color, tube_strength);
			COLOR = vec4(out_color, alpha);
		} else {
			// Outside: only the tube glow is visible
			if (tube_a > 0.01) {
				COLOR = vec4(border_color, tube_a);
			} else {
				COLOR = vec4(0.0);
			}
		}
	}
}
