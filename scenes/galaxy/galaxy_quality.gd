extends RefCounted

# Galaxy quality tier (ruling A54/A60): 0 full-resolution field shells (stand-in under the Compatibility renderer), 1 half-resolution stand-in shells, 2 quarter-resolution stand-in shells and a thinned ambient field.
# The tier is the player's setting; the renderer is never switched by frame time or by the rendering method.
const RES_DIVISORS := [1, 2, 4]


static func tier_from_settings(settings: Dictionary) -> int:
	return clampi(int(settings.get("galaxy_quality", 0)), 0, 2)


static func res_divisor_for_tier(tier: int) -> int:
	return RES_DIVISORS[clampi(tier, 0, 2)]


static func apply(shell: Object, settings: Dictionary) -> int:
	var tier := tier_from_settings(settings)
	shell.res_divisor = res_divisor_for_tier(tier)
	shell.set("stand_in_mode", -1 if tier == 0 else 1)
	return tier


static func read_tier() -> int:
	var bus = Engine.get_main_loop().root.get_node_or_null("UIDataBus")
	return tier_from_settings(bus.get_settings() if bus != null else {})
