extends RefCounted
# The game's 80-region galaxy as field input (B0 pre-check, lane B of
# docs/northstar/plans/2026-10-07-visible-game-spec.md): positions from the
# game's scenes/galaxy/galaxy_gen.gd layout (the same call galaxy_view makes,
# seed 1, fed the snapshot's edges, TD-VG-B-16: was layout(ids, seed) without edges), owner from the
# checked-in C snapshot, significance from the rank formula (TD-VG-B-16: was the adapter's tier table
# SIGNIFICANCE_BY_TIER; DRAFT-b24-sig, the same value galaxy_view qa_state reports). Entries match the field branch's Galaxy.systems shape:
# {pos, significance, owner}.

const SNAPSHOT_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const LAYOUT_SEED := 1


static func systems() -> Array:
	var snap = JSON.parse_string(FileAccess.get_file_as_string(SNAPSHOT_PATH))
	var regions: Array = snap["regions"]
	var ids: Array = []
	for r in regions:
		ids.append(int(r["i"]))
	# TD-VG-B-16: was `.layout(ids, LAYOUT_SEED)` (the random ball, G1: the edges parameter is the graph layout)
	var positions: Dictionary = load("res://scenes/galaxy/galaxy_gen.gd").new().layout(ids, LAYOUT_SEED, snap["edges"])
	# TD-VG-B-16: was `SIGNIFICANCE_BY_TIER[clampi(tier, 0, 2)]` (0.3 / 0.6 / 1.0). DRAFT-b24-sig: sig = 0.3 + 0.5 * rank / (n - 1),
	# rank ascending by capacity, ties by id (n of 1 gives 0.3). Computed here from the capacities; the brief's "shared rank
	# function" has no fixed name or path (GAP 3 names none), so this is the same formula, not a call to it.
	var rows: Array = []
	for r in regions:
		rows.append([float(r.get("capacity", 0.0)), int(r["i"])])
	rows.sort_custom(func(a, b): return a[0] < b[0] or (a[0] == b[0] and a[1] < b[1]))
	var sig_of := {}
	for rank in rows.size():
		sig_of[rows[rank][1]] = 0.3 + (0.5 * float(rank) / float(rows.size() - 1) if rows.size() > 1 else 0.0)
	var out: Array = []
	for r in regions:
		var i := int(r["i"])
		out.append({"pos": positions[i], "significance": float(sig_of[i]), "owner": int(r.get("owner", -1))})
	return out
