# R4 — RTS Bug Catalog

The bugs players hate in tactical and RTS games, each with a signature, a detector tier, the evidence to capture, and a positive control. Every entry is mapped to at least one epic in Stage 3 or marked not applicable. Feeds Stage 0 probe C, Stage 3 watch-fors, and Stage 5 T1 and T2 scenarios.

## Detector tiers

- **T1 (state trace).** A rule over the sim trace with no rendering. Deterministic, fast, preferred wherever the bug is visible in state.
- **T2 (visual).** A check over screenshots or video of the real Godot window, compared to state read over the debug port. Used only where the bug is invisible in state.

## Catalog (to be filled)

| # | Bug | Player sees | Signature | Tier | Evidence | Positive control |
|---|---|---|---|---|---|---|
| 1 | Rubber-banding | Unit jumps back along its path | Position delta between ticks exceeds speed times dt in the reverse direction of velocity | T1 | Trace window, seed, command log | Planted build that snaps position back every K ticks |
| 2 | Stuck unit | Unit has an order but does not move | Path active, zero displacement over N ticks, no blocking unit in contact | T1 | Trace window, navmesh cell, path | Planted build that zeroes velocity when path length exceeds M |
| 3 | Backwards walking | Unit slides in reverse | Velocity dot facing below zero for more than N ticks | T1 | Trace window | Planted build that inverts facing update |
| 4 | Dropped or delayed order | Click does nothing, or acts seconds later | Command acknowledged in log, no state change within N ticks | T1 | Command log, trace | Planted build that drops every Kth command |
| 5 | Path oscillation | Unit shuffles between two routes | Alternating path recomputation with no progress | T1 | Path history | |
| 6 | Unit overlap and clumping | Units stack on one spot | Pairwise distance below radius sum for more than N ticks | T1 | Positions | |
| 7 | Formation break | Group move scatters | Group centroid spread exceeds threshold during move | T1 | Positions | |
| 8 | Selection miss | Click on a unit selects nothing | Selection set unchanged after click on a visible unit's screen rect | T2 | Screenshot, selection state | |
| 9 | Box-select failure | Drag selects wrong set | Selected set differs from units inside the rect | T2 | Screenshot, selection state | |
| 10 | Control-group loss | Group recall returns fewer units | Group membership shrinks without deaths | T1 | Group state, death log | |
| 11 | Camera jitter | View shakes or snaps | Camera position delta spikes with no input | T2 | Video window, input log | |
| 12 | Fog pop-in | Areas flash visible then hidden | Visible set toggles for the same unit across consecutive ticks | T1 | Visibility sets | |
| 13 | LOS wrong through cover | Unit fires through an asteroid | Attack event with a blocking cover between attacker and target | T1 | Attack log, cover geometry | |
| 14 | Projectile miss or desync | Shot lands away from target | Impact position far from target position at impact tick | T2 | Video, attack log | |
| 15 | HP desync between sim and HUD | HUD shows wrong health | HUD value differs from state at the same tick | T2 | Screenshot, state | |
| 16 | HUD stale after delta | Objective or count not updated | HUD text unchanged N ticks after a state change | T2 | Screenshot, state | |
| 17 | Pause desync | Units move while paused | Any position delta while paused flag set | T1 | Trace | |
| 18 | Save and load drift | Reloaded mission differs | Trace after load differs from trace before save at the same tick | T1 | Two traces | |
| 19 | Rewind divergence beyond design | Rewind reproduces or fails to reproduce as specified | Post-rewind trace matches design rule (fresh stochastic outcomes) | T1 | Two traces | |
| 20 | Frame hitches at scale | Stutter with many units | Frame time spikes above budget at N units | T2 | Perf log, video | |
| 21 | Layer elevation not applied | Unit does not move when layer changes | World z unchanged N ticks after a layer command | T1 and T2 | Trace, screenshot | |
| 22 | Layer vision identical | No visibility difference by layer | Visible sets equal across layer changes with the same geometry | T1 | Visibility sets | |

## Findings

(empty until the Research Lane fills it: detector rules with numbers, evidence formats, which entries are not applicable)
