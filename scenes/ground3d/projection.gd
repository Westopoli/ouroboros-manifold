extends RefCounted

# World (x, y) wu <-> screen px through a Camera3D over the height field (S-236, S-207 R-207-06).
# See also: ground_pick.gd, which holds the height sampler and the ray march.

const GroundPick := preload("res://scenes/ground3d/ground_pick.gd")


static func to_screen(cam: Camera3D, terrain: Dictionary, wx: float, wy: float) -> Vector2:
	return cam.unproject_position(GroundPick.world_to_3d(terrain, wx, wy))


static func to_world(cam: Camera3D, terrain: Dictionary, screen: Vector2) -> Variant:
	return GroundPick.pick(terrain, cam.project_ray_origin(screen), cam.project_ray_normal(screen))
