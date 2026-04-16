shader_type particles;

uniform float radius_min = 12.0;
uniform float radius_max = 16.0;
uniform float speed_min = 0.15;
uniform float speed_max = 0.25;
uniform float disc_thickness = 2.0;
uniform int total_particles = 800;
uniform float blue_fraction = 0.15;
uniform vec4 gold_color : source_color = vec4(1.0, 0.88, 0.5, 0.85);
uniform vec4 blue_color : source_color = vec4(0.7, 0.8, 1.0, 0.7);
uniform float tilt_x = 0.0;
uniform float tilt_z = 0.0;

float hash(uint n) {
	n = (n << 13u) ^ n;
	n = n * (n * n * 15731u + 789221u) + 1376312589u;
	return float(n & 0x7fffffffu) / float(0x7fffffff);
}

vec3 rotate_point(vec3 p) {
	float cx = cos(tilt_x); float sx = sin(tilt_x);
	float cz = cos(tilt_z); float sz = sin(tilt_z);
	// Rotate around X axis
	vec3 r = vec3(p.x, p.y * cx - p.z * sx, p.y * sx + p.z * cx);
	// Rotate around Z axis
	return vec3(r.x * cz - r.y * sz, r.x * sz + r.y * cz, r.z);
}

void start() {
	uint id = uint(INDEX);
	float h_radius = hash(id);
	float orbit_radius = radius_min + h_radius * (radius_max - radius_min);
	float h_speed = hash(id + 1000u);
	float orbit_speed = speed_min + h_speed * (speed_max - speed_min);
	float angle_offset = float(INDEX) / float(total_particles) * TAU;
	float angle = angle_offset + TIME * orbit_speed;
	float y_offset = (hash(id + 2000u) - 0.5) * disc_thickness * 2.0;

	vec3 pos = vec3(cos(angle) * orbit_radius, y_offset, sin(angle) * orbit_radius);
	TRANSFORM[3].xyz = rotate_point(pos);

	float color_roll = hash(id + 3000u);
	if (color_roll < blue_fraction) {
		COLOR = blue_color;
	} else {
		COLOR = gold_color;
	}
}

void process() {
	uint id = uint(INDEX);
	float h_radius = hash(id);
	float orbit_radius = radius_min + h_radius * (radius_max - radius_min);
	float h_speed = hash(id + 1000u);
	float orbit_speed = speed_min + h_speed * (speed_max - speed_min);
	float angle_offset = float(INDEX) / float(total_particles) * TAU;
	float angle = angle_offset + TIME * orbit_speed;
	float y_offset = (hash(id + 2000u) - 0.5) * disc_thickness * 2.0;

	vec3 pos = vec3(cos(angle) * orbit_radius, y_offset, sin(angle) * orbit_radius);
	TRANSFORM[3].xyz = rotate_point(pos);
}
