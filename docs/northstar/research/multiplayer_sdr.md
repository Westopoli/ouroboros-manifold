# Multiplayer over Steam Datagram Relay — Findings (2026-09-10)

Question: is multiplayer conceivable using the Steam Datagram Relay (SDR) that comes with the Steam partner account? Answer: yes, as peer-to-peer lockstep. Multiplayer itself stays research-only per `docs/priority_queue.md`; the one consequence adopted now is the cross-platform determinism rule in `c_rewrite.md`.

## What SDR is

- Valve's private relay backbone for UDP between Steam clients. Encrypted, authenticated, rate-limited, hides player and server IPs. Free for Steam partners; no pricing or bandwidth cap is published in Valve's docs.
- It is a relay, not hosting. Valve's doc: "this doesn't necessarily mean that Valve is hosting the servers." Third parties who want a "hosted dedicated server" bring their own box in a data center Valve knows about and contact Valve to join the network.
- Two modes. P2P via `CreateListenSocketP2P` and `ConnectP2P`, no infrastructure. Hosted dedicated server via `CreateHostedDedicatedServerListenSocket` with relay tickets.
- Reliable and unreliable channels, fragmentation and reassembly, 512 KB max message, 256 KB/s default send-rate clamp (configurable).
- Godot side: GodotSteam (GDExtension, Godot 4) exposes `connectP2P` and the Networking Sockets and Messages interfaces with SDR.

## Fit for this game

- Lockstep P2P is the natural shape: every peer runs the deterministic C sim, peers exchange commands per turn over a reliable channel, no server. The sim already has a seeded RNG, a command stream, and a sim/renderer split.
- Pause-and-command tempo tolerates 100–200 ms command latency.
- Cheapest scope is the parked idea in the priority queue: per-mission co-op with 2–4 peers, host is a peer, macro layer stays single-player.

## Risks with evidence

- Latency is not always better. Valve's doc admits some players get worse ping when the route is far from a relay. Player reports: LAN 5–10 ms becoming about 100 ms under forced SDR (Enshrouded), 145–170 ms via a wrong relay (Dota 2). Keep a direct-connect fallback; the API negotiates one when appropriate.
- Connection handshake is 1–3 s slower than raw UDP.
- Determinism across machines is the hard part, not transport. One float divergence kills lockstep. Hence the rule in `c_rewrite.md`.

## Sources

- https://partner.steamgames.com/doc/features/multiplayer/steamdatagramrelay
- https://partner.steamgames.com/doc/features/multiplayer/networking
- https://partner.steamgames.com/doc/api/ISteamNetworkingSockets
- https://github.com/ValveSoftware/GameNetworkingSockets
- https://github.com/ValveSoftware/GameNetworkingSockets/blob/master/include/steam/steamnetworkingtypes.h
- https://godotsteam.com/classes/networking_sockets/
- https://enshrouded.featureupvote.com/suggestions/704248/forced-steam-datagram-relay-sdr-is-killing-performance-for-locallan-dedicated-se
- https://github.com/ValveSoftware/Dota2-Gameplay/issues/29232
- https://theindiestone.com/forums/topic/54229-steam-datagram-relay-option-for-dedicated-servers-often-causes-worse-latency-for-clients/
