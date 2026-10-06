# Steam P2P (SDR) and beta submission: research, 2026-10-06

Status: research only, no design. Facts marked (unconfirmed) were not found in Valve docs and need a check in the Steamworks partner site.

## 1. GodotSteam for Godot 4.6

- Two install routes, same Steam functionality; do not mix: GDExtension plugin (stock Godot templates; ship extra libs) or pre-compiled editor plus custom export templates. https://godotsteam.com/getting_started/introduction/
- Versions: Godot 4.6/4.6.1 = GodotSteam 4.17.1 (Steamworks 1.63); 4.6.2 = 4.18.1; 4.6.3 = 4.19.1 (May 2026, Steamworks 1.64). Later GodotSteam (4.21 to 4.23, 5 Oct 2026) says "Godot 4.x" and is the newest. The GitHub repo was archived 2026-10-05; releases now live at https://codeberg.org/godotsteam/godotsteam. https://github.com/GodotSteam/GodotSteam/releases (verify which release the project's exact 4.6.x needs before downloading).
- Init: `Steam.steamInitEx(app_id)` (status 0 ok, 1 fail, 2 Steam not running, 3 outdated), then `Steam.run_callbacks()` every frame from an unpausable node. App ID via Project Settings > Steam > Initialization (4.14+), argument, env vars, or `steam_appid.txt` in the project root. 480 (Spacewar) works for testing. https://godotsteam.com/tutorials/initializing/
- Networking messages API (GodotSteam class `networking_messages`): `sendMessageToUser`, `receiveMessagesOnChannel` (pull, call every frame), `acceptSessionWithUser`, `closeSessionWithUser`, `closeChannelWithUser`, `getSessionConnectionInfo`; signals `network_messages_session_request`, `network_messages_session_failed`; flags `NETWORKING_SEND_RELIABLE`, `..._AUTORESTART_BROKEN_SESSION` (unreliable is the default flag 0). Sending implicitly accepts an incoming session from that peer. https://godotsteam.com/classes/networking_messages/
- Sockets API (`networking_sockets`: `createListenSocketP2P`, `connectP2P`, poll groups) also exposed. https://godotsteam.com/classes/networking_sockets/ . GodotSteam also ships a ready MultiplayerPeer (not needed for lockstep): https://godotsteam.com/tutorials/multiplayer_peer/
- SDR: Valve: "All P2P connections are automatically relayed over the Valve backbone when appropriate." https://partner.steamgames.com/doc/features/multiplayer/networking . Call `Steam.initRelayNetworkAccess()` (class networking_utils) at startup; it takes a few seconds, else first use is delayed. https://godotsteam.com/classes/networking_utils/ . SDR doc says the game must be "shipping on Steam" for the full feature set (dedicated-server context); P2P needs no app-side relay setting that I found (unconfirmed for an unreleased app; test with 480 first). https://partner.steamgames.com/doc/features/multiplayer/steamdatagramrelay
- Lobbies (ISteamMatchmaking): `createLobby(type, max)`, `joinLobby`, `setLobbyData`, `leaveLobby`, `activateGameOverlayInviteDialog(lobby_id)`; signals `lobby_created`, `lobby_joined`, `lobby_chat_update`, `join_requested` (invite accepted). Types: private, friends-only, public, invisible. https://godotsteam.com/tutorials/lobbies/ . Overlay needs launch through the Steam client (or a non-Steam-game shortcut); it generally does not attach inside the Godot editor (unconfirmed in docs, common experience).
- Export: GDExtension uses stock templates. Linux: `libgodotsteam.linuxbsd.template_release.x86_64.so` + `libsteam_api.so` in `addons/godotsteam/linux64`. Mac: `libgodotsteam.macos...universal.dylib`/framework + `libsteam_api.dylib` in `addons/godotsteam/osx`; for notarization codesign the framework with a Developer ID, then let Godot notarize; Mac extension crashes are reported in https://github.com/GodotSteam/GodotSteam/discussions/529 and /532. `steam_appid.txt` only for runs outside Steam; do not ship it. https://godotsteam.com/tutorials/exporting_shipping/ , https://godotsteam.com/tutorials/mac_export/

## 2. Testing P2P with the accounts he has

- The developer account is an ordinary Steam account in the partner group; it auto-owns the app through the Developer Comp package. A second account gets the app by redeeming a Developer Comp key (also removes the new-account "limited" status so it can friend), or a Beta Testing / release-override key. https://partner.steamgames.com/doc/store/testing , https://partner.steamgames.com/doc/features/keys
- So his two accounts can play each other once the second one holds a key; "ordinary" account must be given the app that way (or Playtest access). Unreleased apps are owned only by the partner group and key holders, so a live build does not reach customers.
- Two machines, one Steam client each, logged into different accounts: required (Steam allows one logged-in session per account; two clients on one OS user are not supported). Mac + Linux box is the clean pairing; the VM works if Steam runs in it and has networking, but a second Steam client on the same OS user as the first does not. Same LAN or tailnet is not special: SDR relays regardless (Valve docs do not address LAN case; behaviour unconfirmed, harmless either way).
- Needs from Steamworks app config for P2P: nothing found beyond the app existing, depots uploaded, and the testers owning it. Dev Comp must include any new depot IDs (`licenses_for_app <appid>` in the Steam console to check). Today, before any fee: Spacewar 480 with two accounts that own it (everyone can add it) tests the whole transport.

## 3. Steam beta submission, brand-new app

- App fee $100 per app. 21-day wait between paying and being allowed to release (Valve onboarding; some third parties say 30 days; use 21 per Valve, plan for 30). https://partner.steamgames.com/doc/gettingstarted/onboarding
- Before anything: sign NDA and distribution agreement, bank and tax info, identity verification. Tax verification may take 10 to 15 business days. Same page.
- Store page review about 3 to 5 business days (submit 7 days ahead); store page must be "Coming Soon" at least 2 weeks before release; build review has no stated time (community reports of weeks). https://partner.steamgames.com/doc/store/releasing
- Steam Playtest: free, a child appID; signup button lives on the main app's store page, so the main page must exist and be Coming Soon; its own review checklist is only capsule images and icons; access by limited or open signup, or keys (up to about 50k). https://partner.steamgames.com/doc/features/playtest . Whether the playtest can start before the main page's 3-5 day review passes: (unconfirmed).
- Beta branches: build assigned to a password-protected branch, testers opt in in Steam. https://partner.steamgames.com/doc/store/testing . Release-override keys (max 2,500) for NDA betas need a Coming Soon page. Dev Comp owners need no review at all to run any uploaded build, including a non-default branch (as far as the docs state).
- Hard dates fixed by Valve: 21 days after fee to release; 14 days Coming Soon before release; 3-5 business days store page review; 10-15 business days tax check (if not done already). A public Playtest is a release-like path; a Dev Comp key path is not.

Calendar against 14 days (D0 = 2026-10-06, assumes nothing is onboarded yet; skip rows already done):
- D0 to D1: pay Steamworks signup, sign agreements, bank, tax, identity (starts the 1-3 day and 10-15 business-day clocks). Pay $100 fee (starts 21-day clock: earliest release D21 = 2026-10-27).
- D0 now: GodotSteam on 480, two accounts, two machines (no Valve dependency).
- D1 to D3: create app, set depots, Linux and Mac launch options, upload first build to a private branch.
- D3 to D5: generate Dev Comp key, second account redeems it, P2P over SDR on the real AppID.
- D4 to D10: store page assets, submit for review (3-5 business days: lands about D9 to D11).
- D11 to D14: Coming Soon page live; Playtest signup possible; the 14-day Coming Soon rule ends D25 to D28, past the target, but only binds a full release, not Dev Comp testing.
- Not achievable in 14 days: a public store release. Achievable: a private beta via Dev Comp / beta keys. A public Playtest by D14 is possible only if tax, page review and capsule review all go fast (risky).

Verdict on the account question: YES. Developer account (auto-owns) plus the ordinary account (given a Dev Comp key) can play each other over SDR, on two machines each running its own Steam client. Without the $100 fee, 480 with two accounts proves the transport.

## 4. What the client must gain (inventory, from origin/main 2026-10-06)

Exists:
- `autoload/net/transport.gd` (16 lines): `attach(id)`, `send(from,to,data)`, `poll(id) -> [{from,data}]`, endpoints are small ints.
- `autoload/net/loopback_transport.gd` (78): test transport (delay, drop, reorder).
- `autoload/net/lockstep_session.gd` (181): `setup(local,peers,transport,sim,opts)`, `command`, `poll`, `is_stalled`, `live_peers`, `desync() -> Dictionary`; plain classes, unwired (only `tests/test_lockstep_session.gd` references them).
- Pipe verbs in `csrc/pipe/om_pipe.c` (`net_guard`, `net_ack_*`, `handle_net_reset`, net_submit/step/checksum). `autoload/c_bridge.gd` (688): no net verb wrapper found (grep for net_ returned nothing).
- `scenes/tactical_c/tactical_view.gd` (672): live load at line 133 via `bridge.load_tactical_live(bridge.live_seed(), ...)`, local seed only.
Does not exist:
- Steam transport (maps peer ids to SteamIDs, `sendMessageToUser`/`receiveMessagesOnChannel`, session accept, unreliable flag).
- Steam init autoload (`steamInitEx`, `run_callbacks`, `initRelayNetworkAccess`), GodotSteam addon in repo.
- Lobby scene and flow (create, invite overlay, join, ready, member list, start).
- c_bridge net_submit/net_step/net_checksum wrappers; session-to-sim adapter object.
- Host chooses seed and mission, sends it to peers; tactical_view takes seed from lobby and drives `session.poll()` per frame instead of local tick.
- Desync screen (consume `desync()`), stall/drop indicator.
- Linux and Mac export presets with Steam libs; depot and launch config.

## Three biggest risks
1. Valve onboarding clocks (tax verification 10-15 business days, identity, page review) are outside our control; a public beta in 14 days is not realistic, a Dev Comp private beta is.
2. Mac export/notarization with the GDExtension (reported crashes, codesigning of the framework) plus first-ever cross-platform lockstep: determinism across Linux/Mac is unproven on a live network (spec requires byte-identical traces; no fast-math).
3. Unwired client work is the whole schedule: transport, lobby, bridge wrappers, seed handoff, desync screen all absent, and the session was only proven on loopback; SDR packet behaviour (loss, reordering with the repeat-5 scheme at 20 ticks/s) is untested.
