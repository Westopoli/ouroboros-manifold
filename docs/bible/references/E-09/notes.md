# E-09 Chronicle — Look and behavior references

**Reuse existing, not an external pull.** The galaxy view already built in the game has good animation for the "watching history happen" map, and Westley wants to reuse what exists rather than reference another game.

## Status (Westley, 2026-09-13)

- **Source is the existing in-game galaxy view.** Its map animation is the target for S-069.
- **Screenshots pending a build fix.** The game currently does not run — a build error (`tactical_bridge.gd`: `Identifier "WsClient" not declared`, in `privacy_modal.tscn` load) blocks it. Westley will capture the galaxy-view references once the build errors are solved. See the project note recorded this session.

## Slots to fill once the build runs

| # | Story | Shot subject | Aspect — the example | Proves / contrast |
|---|---|---|---|---|
| 01 | S-069 | The existing galaxy-view map animation, clip | the pace and legibility of the map replaying events | reuse this, do not redesign it |
| 02 | S-065, S-069 | Split view: streaming text beside the animated map | narrated history and moving map read together | — |
| 03 | S-067 | One chronicle entry's typography | reads as a fragment of history, not a log line | — |
