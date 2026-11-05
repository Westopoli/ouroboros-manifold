# Lab stage 3: the ground pushes back (finished run, 2026-11-05)

Replaces the first run of the same day (seed 1 only, run before the stage 3 fixes: its control fights flew over the ground, the replay drew every layout flat, and the slope was the old L-0045). Its four window captures are removed from here; they stay in git history (`65a4dd4a`).

Four fights, 20 seeds each, every one beside the same fight without the ground. Run on main after the engage-on-sight engine (H-057). The page with every strip is `docs/northstar/research/layer_dynamics/arena/stage3/index.html`.

Watch one: on the Mac `scripts/replay.sh docs/northstar/research/layer_dynamics/arena/stage3/L-0055-s10.fight.json`, on Linux `OM_FIGHT=$PWD/<that file> scripts/play.sh --scene res://scenes/proto/fight_replay/fight_replay.tscn`. Space steps forward. The controls are in `arena/stage3/control/`.

What the numbers say (the same in all 20 seeds of each fight; the seed changes nothing in the arena today, so a rate is 0% or 100%):

| Fight | With the ground | Same fight without it | Your guess |
|---|---|---|---|
| Chokepoint L-0055 | Blue wins, 21 left against 0, 3394 ticks; 6 unit-frames held by the walls. | Blue wins, 23 left, 2196 ticks. | Blue 98%: agrees. |
| City L-0073 | Blue wins, 17 left against 0, 6175 ticks; no unit held. | Blue wins, 22 left, 2156 ticks. | Blue 75%: agrees. |
| Slope L-0084 (redrawn: blue in an arc on the top, 40 against 56) | Red wins, 0 against 6 left, 2268 ticks; 6 unit-frames held. | A stand-off at tick 820, nobody dead. | Blue 60%: red wins every time. |
| Cover L-0039 (as you drew it, red expected 75%) | A draw at the 600 s cap, 8 against 8. From tick 800 both sides sit about 290 wu apart with targets and nobody loses any hit points. | Blue wins, 3 left, 2606 ticks. | Red 75%: a draw. |

Checked exactly on the fight files (not by eye): in every frame of the four real fights no unit stands inside a wall, building or box, and no red unit is on the slope's cliff; in the city control 38 unit rows stand inside buildings and in the slope control 54 rows are on the cliff, as they should without the ground.

Open for you: the cover draw (no damage at all for ten minutes looks wrong, cause not investigated) and the slope result are yours to call: a story, or fine as it is.

| What to look at | What to expect | Approve means | Deny means |
|---|---|---|---|
| Chokepoint, then its control | Red queues at the gap, nobody inside a wall; without walls red spreads and reaches the arc at once. | The walls stop red units and the queue is the thing I see. | A red unit stands in a wall, or no queue forms; name the frame. |
| Slope, then its control | Red climbs the ribbon one file at a time; the cliff is not crossed. | The climb is slower than the control and the cliff holds. | Red crosses the cliff or stalls at the foot; name the frame. |
| City, cover (as you like) | Units go round buildings and boxes. | Units respect the ground. | A unit crosses a building or box. |
