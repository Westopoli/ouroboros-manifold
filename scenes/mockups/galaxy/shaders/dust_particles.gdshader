shader_type particles;

uniform float sphere_radius = 60.0;
uniform float drift_speed = 0.3;
uniform float blue_fraction = 0.5;
uniform vec4 gold_color : source_color = vec4(1.0, 0.88, 0.5, 0.3);
uniform vec4 blue_color : source_color = vec4(0.6, 0.7, 1.0, 0.2);

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

	if (hash(id + 300u) < blue_fraction) {
		COLOR = blue_color;
	} else {
		COLOR = gold_color;
	}
}

void process() {
	uint id = uint(INDEX);
	float dx = (hash(id + 400u) - 0.5) * drift_speed;
	float dy = (hash(id + 500u) - 0.5) * drift_speed;
	float dz = (hash(id + 600u) - 0.5) * drift_speed;

	TRANSFORM[3].xyz += vec3(dx, dy, dz) * DELTA;

	float dist = length(TRANSFORM[3].xyz);
	if (dist > sphere_radius) {
		TRANSFORM[3].xyz *= sphere_radius / dist;
	}

	float twinkle = 0.7 + 0.3 * sin(TIME * 1.5 + float(INDEX) * 0.7);
	COLOR.a *= twinkle;
}
