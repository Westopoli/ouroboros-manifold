extends Node
# Steam bootstrap (W3, docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md).
# App id 5402100 (Westley's Steam app id, 2026-10-06).

const APP_ID := 5402100

var steam_ready := false


func _ready() -> void:
	init_steam(APP_ID)


func init_steam(app_id: int = APP_ID) -> void:
	steam_ready = false
	if not Engine.has_singleton("Steam"):
		return
	var steam = Engine.get_singleton("Steam")
	var r = steam.steamInitEx(app_id)
	if typeof(r) != TYPE_DICTIONARY or int(r.get("status", 1)) != 0:
		return
	steam.initRelayNetworkAccess()
	steam_ready = true
