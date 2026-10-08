extends "res://scenes/galaxy/legacy_world_view_data.gd"

# Snapshot-to-renderer adapter (piece C5-G2, R-106-02). Fills the inherited
# regions / connections / territories dictionaries from a live snapshot so
# legacy_shell_renderer.gd and legacy_constellation_renderer.gd draw the
# galaxy. Region ids are str(i); one faction_id per owner groups a faction's
# systems into one shell. Every edge becomes a filament: border and both-edges
# (t 0, 2) are solid and take their owner's colour when both ends share an
# owner, trade (t 1) is thinner, and a cross-faction edge is dimmed. The
# prototype (scenes/mockups/galaxy/galaxy_adapter.gd) draws all edges too.

const TRADE_DIM := Color(0.42, 0.44, 0.5, 0.5)
const EDGE_TRADE := 1
const POINT_BASE_RADIUS := 1.4
const SIGNIFICANCE_BY_TIER := [0.3, 0.6, 1.0]


func apply(snap_regions: Array, snap_edges: Array, positions: Dictionary, colours: Dictionary) -> void:
	clear_all()
	var owners := {}
	for r in snap_regions:
		var i := int(r.get("i", -1))
		if not positions.has(i):
			continue
		var owner := int(r.get("owner", -1))
		owners[i] = owner
		var tier := clampi(int(r.get("tier", 0)), 0, SIGNIFICANCE_BY_TIER.size() - 1)
		var sig: float = SIGNIFICANCE_BY_TIER[tier]
		var colour: Color = colours.get(i, Color.WHITE)
		var key := str(i)
		add_region(key, positions[i], 2.0 * POINT_BASE_RADIUS * (0.6 + 1.4 * sig), colour, _faction_id(owner))
		if owner >= 0:
			set_territory(key, positions[i], sig, colour)
	for e in snap_edges:
		var a := int(e.get("a", -1))
		var b := int(e.get("b", -1))
		if not (owners.has(a) and owners.has(b)):
			continue
		var same_faction: bool = owners[a] >= 0 and owners[a] == owners[b]
		var is_trade := int(e.get("t", 0)) == EDGE_TRADE
		var colour: Color = (regions[str(a)]["color"] as Color) if same_faction and not is_trade else TRADE_DIM
		add_connection(str(a), str(b), "trade" if is_trade else "border", colour)


func _faction_id(owner: int) -> String:
	return "neutral" if owner < 0 else "faction_%d" % owner
