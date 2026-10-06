# Ouroboros Manifold: private beta tester guide

DRAFT for Westley's edit. Sources: the bible hub, the Steam multiplayer wiring spec (rev 5), E-16 S-245. Anything the sources do not settle is marked [TBD: ...].

## What this beta is, and is not

You are one of 2 to 4 friends playing a match together. Ouroboros Manifold is a real-time strategy game set in a living galaxy: you are a commander handed a task force and a deadline, and the world moves on its own. A match is co-op: your team shares one mission and one civilization (versus is not in the game yet). Combat is full real-time and a multiplayer match never pauses, not even when you open the menu.

This is an unfinished build. It is private (Developer Comp keys), it has two eras (a space era and a placeholder ground era), and it will break. Your job is to break it and tell us how. Everything here is a target, not a promise.

## Redeeming your key

1. Open the Steam client and sign in.
2. Games menu > Activate a Product on Steam.
3. Enter the key we sent you. The game appears in your library; install it (Linux, Windows or macOS) [TBD: which platforms the first build ships].
4. Launch it from Steam, not from a file. The invite overlay only works when Steam launches the game.

## First launch

The main menu has an era toggle: space or ground. Space is the Settled Reach, the sci-fi era. Ground is a placeholder era with the same units and rules and a different landscape; expect it to look rough. Everyone in a match must pick the same era [TBD: whether the lobby sets it or each player must match by hand].

## Hosting and joining a match

1. Host: choose MULTIPLAYER, then host. A friends-only lobby opens (up to 4 players).
2. Invite a friend from the Steam overlay (Shift+Tab, friends list, invite). They can also join from their friends list.
3. For the very first test, the lobby screen has a paste-lobby-id field: the host reads out the lobby id, guests paste it and join.
4. The host's build and yours must be the same version; a different version refuses to start.
5. When everyone has loaded, every player is marked ready and the match starts together at tick 0.

The match does not support late join: nobody can enter once it has started.

## When a friend stalls or drops

- Stall: if a peer stops sending for about a second, your HUD shows "waiting for NAME (s)" and the match holds for them. Nothing is lost; it resumes when they catch up.
- Drop: if a peer is gone for about 60 seconds they are dropped and the match goes on without them [TBD: confirm what happens to their units; Q-NET-02 is open]. Leaving yourself (End Mission) leaves the lobby and ends your side of the match.
- Desync: every machine runs the same simulation and compares checksums. If they ever disagree you get an error screen reading "Desync at tick N, section NAME", with only a main-menu button and no retry. This is the most valuable bug you can find: press F12 before you leave the screen if you can, and send the report.

## Reporting a bug: F12

Press F12 in any scene, including the desync screen. The game writes a report containing:

- your words (a text box: say what you did and what you expected; the box is a new addition for this beta);
- the scene name and camera;
- a capture of the last 10 seconds of the simulation (a save state from before the press plus the commands since), so we can replay exactly what you saw;
- a screenshot, mission metrics, and the tail of the client log (and the crash log, if the game crashed).

It is saved as a zip under your game's logs folder (reports) and a copy goes to your Downloads folder, and the game tells you where it went and copies the path [TBD: confirm the clipboard copy and popup behave this way in the beta build]. Paste or drag the zip into the Discord channel [TBD: channel name and link]. Say which match and who else was in it.

## Known gaps

- The tactical view is 2D; the 3D view is not built.
- The ground era is a placeholder: same units and rules, rough visuals, no seer-type units beyond a simple scout.
- No late join, no rejoin, no resync after a desync.
- The ping (the space-era way to see across layers) works in the space era only; ground eras do not have it.
- Co-op only, 2 to 4 players. No versus, no spectators, no dedicated servers.
- Economy seat for a second player in a pair [TBD: in the beta or not].
- A hung simulation can freeze your screen for up to 5 seconds before the error panel appears.
- The first real Steam test uses a test app id (Spacewar 480) until the real one exists [TBD: app id and store name shown to testers].

## Privacy: what the report zip holds

Simulation snapshots and the command log of the last 10 seconds, a screenshot of the game window, mission metrics, a client log tail, the scene name, and your OS name. No account name, email, files from your machine or chat is collected [TBD: Westley to confirm the Steam id of match peers is not in the log]. Reports go only where you send them: you choose to post the zip. Nothing is uploaded automatically in this beta.
