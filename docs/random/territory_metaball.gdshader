shader_type canvas_item;

// Data textures — updated by GDScript when territory changes
uniform sampler2D system_data : filter_nearest;   // Nx1: RG=normalized XZ, B=faction/8, A=significance
uniform sampler2D faction_colors : filter_nearest; // 8x1: RGB=faction fill color
uniform sampler2D faction_borders : filter_nearest;// 8x1: RGB=faction bright border color
uniform int system_count = 0;

// Metaball field
uniform float influence_radius : hint_range(0.05, 0.35) = 0.17;
uniform float threshold : hint_range(0.05, 0.80) = 0.66;

// Outline (drawn at the threshold isoline using field value)
uniform float outline_band : hint_range(0.005, 0.08) = 0.025;
uniform float outline_alpha : hint_range(0.1, 1.0) = 0.95;

// Outer glow (just outside the threshold)
uniform float glow_band : hint_range(0.0, 0.12) = 0.05;
uniform float glow_alpha : hint_range(0.0, 0.5) = 0.25;

// Interior fill (bright near outline, fading to transparent at center)
uniform float fill_opacity : hint_range(0.0, 0.30) = 0.16;
uniform float fill_fade_depth : hint_range(0.1, 2.0) = 0.8;

// Faction gap (margin-of-victory: best must exceed second by this amount)
uniform float gap_margin : hint_range(0.0, 0.40) = 0.30;

void fragment() {
	int num_factions = 8;
	float faction_fields[8];
	for (int fi = 0; fi < 8; fi++) {
		faction_fields[fi] = 0.0;
	}

	// Accumulate metaball influence per faction
	for (int i = 0; i < system_count; i++) {
		float u = (float(i) + 0.5) / 128.0;
		vec4 sys = texture(system_data, vec2(u, 0.5));
		vec2 sys_pos = sys.rg;
		float sys_faction_norm = sys.b;
		float sys_sig = sys.a;

		int fi = int(round(sys_faction_norm * 8.0)) - 1;
		if (fi < 0 || fi >= 8) continue;

		float d = distance(UV, sys_pos);
		float r = influence_radius * (0.6 + sys_sig * 0.4);
		float influence = (r * r) / (d * d + r * r);
		faction_fields[fi] += influence;
	}

	// Find best and second-best faction
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
		return;
	}

	// Gap test: best must exceed second by gap_margin
	bool rival_present = second_field > threshold * 0.15;
	bool in_gap = rival_present && (best_field - second_field) < gap_margin;

	// Territory membership: above threshold AND not in gap
	bool inside = best_field >= threshold && !in_gap;

	// Look up colors
	float fc_u = (float(best_faction) + 0.5) / 8.0;
	vec3 fill_color = texture(faction_colors, vec2(fc_u, 0.5)).rgb;
	vec3 border_color = texture(faction_borders, vec2(fc_u, 0.5)).rgb;

	float field_above = best_field - threshold;

	if (!inside) {
		// --- OUTSIDE territory or in gap ---
		// Outer glow: render just below the threshold (or just below gap boundary)
		if (glow_band > 0.0 && best_field > threshold * 0.3) {
			float dist_below;
			if (in_gap) {
				// In gap zone: glow based on how close to the gap edge
				float gap_edge_field = second_field + gap_margin;
				dist_below = gap_edge_field - best_field;
				if (dist_below < 0.0) dist_below = threshold - best_field;
			} else {
				dist_below = threshold - best_field;
			}

			if (dist_below >= 0.0 && dist_below < glow_band) {
				float t = 1.0 - dist_below / glow_band;
				float glow_a = t * t * glow_alpha;
				COLOR = vec4(border_color, glow_a);
				return;
			}
		}
		COLOR = vec4(0.0);
		return;
	}

	// --- INSIDE territory ---
	// Distance above the effective boundary (threshold or gap edge)
	float effective_above = field_above;
	if (rival_present) {
		float gap_above = best_field - (second_field + gap_margin);
		effective_above = min(field_above, gap_above);
	}
	effective_above = max(effective_above, 0.0);

	vec3 out_color;
	float alpha;

	if (effective_above < outline_band) {
		// OUTLINE ZONE: bright border color
		float t = effective_above / outline_band; // 0 at boundary, 1 at inner edge
		float strength = 1.0 - t * t; // quadratic falloff inward
		out_color = border_color;
		alpha = strength * outline_alpha;
	} else {
		// FILL ZONE: faction color, fading to transparent deeper inside
		float fill_depth = effective_above - outline_band;
		float fill_t = max(0.0, 1.0 - fill_depth / fill_fade_depth);
		float fill_smooth = fill_t * fill_t;
		alpha = fill_opacity * fill_smooth;
		out_color = fill_color;

		// Blend border color near the outline for smooth transition
		float blend_dist = 0.05;
		if (fill_depth < blend_dist) {
			float edge_blend = 1.0 - fill_depth / blend_dist;
			out_color = mix(fill_color, border_color, edge_blend);
			alpha = max(alpha, edge_blend * 0.15);
		}
	}

	COLOR = vec4(out_color, alpha);
}
