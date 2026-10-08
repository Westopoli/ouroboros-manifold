extends RefCounted
# The game's 80-region galaxy as field input (B0 pre-check, lane B of
# docs/northstar/plans/2026-10-07-visible-game-spec.md): positions from the
# game's scenes/galaxy/galaxy_gen.gd layout (the same call galaxy_view makes,
# seed 1), owner and tier from the checked-in C snapshot, significance from the
# adapter's tier table. Entries match the field branch's Galaxy.systems shape:
# {pos, significance, owner}.

const SNAPSHOT_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const LAYOUT_SEED := 1


static func systems() -> Array:
	var snap = JSON.parse_string(FileAccess.get_file_as_string(SNAPSHOT_PATH))
	var regions: Array = snap["regions"]
	var ids: Array = []
	for r in regions:
		ids.append(int(r["i"]))
	var positions: Dictionary = load("res://scenes/galaxy/galaxy_gen.gd").new().layout(ids, LAYOUT_SEED)
	var sig_by_tier: Array = load("res://scenes/galaxy/galaxy_adapter.gd").SIGNIFICANCE_BY_TIER
	var out: Array = []
	for r in regions:
		var i := int(r["i"])
		var tier := clampi(int(r.get("tier", 0)), 0, sig_by_tier.size() - 1)
		out.append({"pos": positions[i], "significance": float(sig_by_tier[tier]), "owner": int(r.get("owner", -1))})
	return out
