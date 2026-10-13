# Story reviews, lane V (sim viewer, tooling)

Tooling shots have no `S-###`; the story cell names the piece and the mode. No `qa_state` dump exists (the viewer is a pygame tool, not the Godot client).

| story | lane | run id | screenshot path | qa_state file | reviewer | reviewer verdict (yes/no/unclear + evidence) | Westley verdict (pending/approved/rejected) | date |
|---|---|---|---|---|---|---|---|---|
| SV-3 tick mode | V | 20261012-2005-d5799f5 | docs/northstar/story_reviews/shots/20261012-2005-d5799f5/tick_mode.png | n/a (tooling) | sonnet | yes. 1280x720, seed 1, 80 regions: faction hulls and region graph at tick 50, selected region 38 with six value bars and rings, 16-row faction list, event log (t50 region 46 template 13 chain 352), status line "TICK mode, tick 50, PAUSED"; not blank. | pending | 2026-10-12 |
| SV-3 mission mode | V | 20261012-2005-d5799f5 | docs/northstar/story_reviews/shots/20261012-2005-d5799f5/mission_mode.png | n/a (tooling) | sonnet | yes. Same map at tick 100, phase "debriefed": mission archetype 3 at region 57, pick 2 partial success matches sim band 2 partial success, region deltas shown, mission log two rows (t50 and t100) with picked equal to sim band; status line "MISSION mode, RETURN jumps 50 ticks". | pending | 2026-10-12 |
