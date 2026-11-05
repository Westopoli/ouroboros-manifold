# Lab stage 4: sight (H-088, run 2026-11-05)

Four fights, 20 seeds each, every one beside the same fight with targeting by sight off. Sight is on: a unit fires only at what its side sees; high ground sees down and fires down, low ground never sees up (reach 0 up, 1 down is a lab setting, DEC-stage4-vantage-reach); the holder of a `hold:` layout is on guard. The page with every strip is `index.html` in this directory; its frames (`L-0061-s10/` and so on, each fight with its `-control-s10/`) sit beside it. Seed 10 is the median seed the page shows. All 20 seeds of each fight come out the same today (the seed changes nothing in the arena), so a rate is 0% or 100%.

Watch one: on the Mac `scripts/replay.sh docs/northstar/research/layer_dynamics/arena/stage4/L-0061-s10.fight.json`, on Linux `OM_FIGHT=$PWD/docs/northstar/research/layer_dynamics/arena/stage4/L-0061-s10.fight.json scripts/play.sh --scene res://scenes/proto/fight_replay/fight_replay.tscn`. Space steps forward; V switches the faint sight discs between one per role and one per unit; a hollow unit is one the other side does not see. The control fight (`.../stage4/control/L-0061-control-s10.fight.json`) is the same fight with targeting by sight off.

What the numbers say (seed 10; the same in every seed):

| Fight | With sight | Same fight, targeting by sight off | Your guess |
|---|---|---|---|
| Vantage L-0061 (24 against 24, blue in an arc on the hill) | Blue wins, 24 left against 0, 1399 ticks. Blue sees red at tick 0, red never sees blue (blue is a band up). | Blue wins, 24 left, 1399 ticks (the same result). | Blue 98%: agrees. |
| Trap L-0080 (16 against 32) | A draw at the 600 s cap, 8 against 29 left. Both sides see each other at tick 0 (first seen: blue 0, red 0). Red is held by the walls (116 unit-frames), nobody can fire from where they stand. | The same draw, 8 against 29, the same positions. | Blue 75%: a draw. |
| Trap L-0083 (24 against 48) | A draw at the cap, 15 against 46 left. First seen: blue 0, red 0. Red held 85 unit-frames. | The same draw (71 unit-frames held). | Blue 75%: a draw. |
| Cover L-0039 (as you drew it, red expected 75%) | A draw at the cap, 8 against 8. Neither side ever sees the other: 861 pair-frames of units within sight range with a box between them are hidden, none seen through a box. | A draw at the cap, 8 against 8 (stage 3 drew this one too). | Red 75%: a draw. |

Checked exactly on the fight files (not by eye): in every frame of L-0061 (all 20 seeds) no red unit lists a blue unit standing on the band above; in every stage 4 fight, all seeds, blue's first-seen tick is not after red's (the traps tie at 0; in the cover fight neither side ever sees); in the cover fight no pair is seen through a box (the spec asked for a hidden pair at frame 0; the sides start 1250 wu apart, out of sight range, so the first hidden pairs appear later, in 15 of 16 frames). The stage 3 fights reproduce byte for byte under `--sight off`, and a second run of L-0061 and L-0080 gives byte-identical files.

Open for you (findings, nothing fixed here):
- The two traps do not show who sees first: both sides see each other at tick 0 and the fight stops as a stand-off at the walls, identical with sight off. The done-when asks you to agree who saw whom first; the vantage fight answers it (blue, from tick 0), the traps tie. A trap whose red force is seen from the hills before it sees them needs a redraw, or a story.
- The cover fight and both traps end as draws at the cap with nobody firing (stage 3 drew the cover one too, cause not investigated).
- R-164-01: as written the game's reach table gives a Line type its own layer only, so a Line arc on a hill could not fire down. The lab fires one band down for this stage; whether the game does is yours to rule as a game story.

| What to look at | What to expect | Approve means | Deny means |
|---|---|---|---|
| Vantage, then its control | Blue on the rim sees red from the start and fires first; red walks in blind (hollow) until it is on the band. | The high ground sees first and fires first, so the vantage works as sight. | Red sees blue first, or hits blue unseen; name the frame. |
| Traps, then their controls | Red is seen from the hills before it sees anyone. | The trap works as sight. | Both sides see each other at once, as the files show; say so. |
| Cover (as you like) | Boxes hide units; hollow marks sit behind the boxes. | The boxes hide units. | A unit is hollow with a clear line, or fires through a box. |
