shader_type particles;

uniform float sphere_radius = 80.0;
uniform float blue_fraction = 0.4;
uniform vec4 gold_color : source_color = vec4(1.0, 0.92, 0.7, 0.4);
uniform vec4 blue_color : source_color = vec4(0.7, 0.8, 1.0, 0.25);

float hash(uint n) {
	n = (n << 13u) ^ n;
	n = n * (n * n * 15731u + 789221u) + 1376312589u;
	return float(n & 0x7fffffffu) / float(0x7fffffff);
}

void start() {
	uint id = uint(INDEX);
	float theta = hash(id) * TAU;
	float phi = acos(2.0 * hash(id + 100u) - 1.0);
	float r = sphere_radius * pow(hash(id + 200u), 0.333);

	float x = r * sin(phi) * cos(theta);
	float y = r * sin(phi) * sin(theta);
	float z = r * cos(phi);

	TRANSFORM[3].xyz = vec3(x, y, z);

	float size_roll = hash(id + 400u);
	COLOR.a = mix(0.3, 0.8, size_roll * size_roll);

	if (hash(id + 300u) < blue_fraction) {
		COLOR.rgb = blue_color.rgb;
	} else {
		COLOR.rgb = gold_color.rgb;
	}
}

void process() {
	// Static — no movement
}
