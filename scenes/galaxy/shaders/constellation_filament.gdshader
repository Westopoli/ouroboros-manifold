shader_type spatial;
render_mode unshaded, blend_add, cull_disabled;

uniform vec4 filament_color : source_color = vec4(0.3, 0.6, 1.0, 0.8);
uniform float emission_energy = 3.0;
uniform float shimmer_speed = 0.3;
uniform float shimmer_strength = 0.4;
uniform float alpha_multiplier = 1.0;
uniform bool is_trade = false;
uniform float dash_frequency = 8.0;
// pass-2 addition: pass 1's faction-list hover/pin dim-and-brighten, layered
// on top of alpha_multiplier (owned exclusively by legacy_constellation_
// renderer.gd's band blend) so the two writers never fight over one uniform.
// See also: scenes/mockups/galaxy/galaxy_view.gd update_view().
uniform float emphasis_multiplier = 1.0;

void fragment() {
	float shimmer = sin(UV.x * 12.0 - TIME * shimmer_speed * 6.28) * 0.5 + 0.5;
	float shimmer_mod = 1.0 + shimmer * shimmer_strength;

	float alpha = filament_color.a * alpha_multiplier * emphasis_multiplier;

	if (is_trade) {
		float dash = step(0.5, fract(UV.x * dash_frequency));
		alpha *= dash;
	}

	ALBEDO = filament_color.rgb * shimmer_mod;
	EMISSION = filament_color.rgb * emission_energy * shimmer_mod;
	ALPHA = alpha;
}
