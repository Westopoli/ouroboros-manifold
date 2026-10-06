extends Node
# Steam bootstrap (W3, docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md).
# App id 480 (Spacewar) until the real app id exists.

const SPACEWAR_APP_ID := 480

var steam_ready := false


func _ready() -> void:
	init_steam(SPACEWAR_APP_ID)


func init_steam(app_id: int = SPACEWAR_APP_ID) -> void:
	steam_ready = false
	if not Engine.has_singleton("Steam"):
		return
	var steam = Engine.get_singleton("Steam")
	var r = steam.steamInitEx(app_id)
	if typeof(r) != TYPE_DICTIONARY or int(r.get("status", 1)) != 0:
		return
	steam.initRelayNetworkAccess()
	steam_ready = true
