# LAB stage 5 plan (2026-11-26, overnight run)

**Staircase: the simulation LAB. File: `docs/northstar/story_reviews/westley/lab-staircase.md`. Stage title, quoted: "Stage 5: facing, arcs and height bands". This is not beta B5.**

Westley, 2026-11-26: "NEW OVERNIGHT RUN, fully autonomous ... Target: LAB stage 5, 'facing, arcs and height bands' in lab-staircase.md, NOT the beta ... Build lab stage 5 to its done-when: he can see a flank hit a side, and the climb slow the attacker ... choose the least risky assumption for each dependency, log it, and keep stage 5 easy to change when stage 4 settles."

Branch `s/lab-stage5`, worktree `~/Projects/om-wt/lab5`, cut from `origin/main` `caa79b7ff`. Nothing is merged to main or pushed. The beta B5 branch and worktree are not touched. Decisions made alone: `decisions-log.md` beside this file. Report: `docs/reports/2026-11-26-lab-stage5-overnight.md`. Story: `docs/stories/H-091.md`.

## 1. What lab stage 5 is (the staircase's words)

"Units have fronts; fire cones matter; a height band is a slower climb and a longer sight." Adds: `set_cone` arcs from the layout (`facing` is already in the schema), `transition_progress` shown while climbing, band changes in the frame (`layer`). Layouts: flank_route (the ridge), slope top versus foot, objective ring. Done when: he sees a flank hit a side and the climb slow the attacker.

## 2. What the scouts found (pre-flight, read and measured on this tree)

- **Facing is cosmetic today.** The fire pass never reads it. Eight Vanguards attacked from the front, the side and the rear give the same fight; with the arc parameter at 90 or 360 every output is byte-identical. A flank does nothing.
- **The firing-arc rule is drafted and unbuilt.** E-13 R-100-04 (his words 2026-10-13: "add a firing-arc rule to the game"; per category, Strike wide, Line medium, Siege narrow). The parameter `OM_TP_FIRING_ARC_DEG` exists, is saved, defaults to 360 and is read by nothing.
- **`set_cone` is a different rule**, the area-damage cone (R-082-10), also a stub. The staircase's "set_cone arcs" names the wrong function for "units have fronts".
- **The lab cannot set a unit's facing at spawn** (`om_unit_set_facing` is not bound; every unit starts facing east).
- **The climb slows a walker by 5 percent** over a 600 wu ramp (`OM_TP_SLOPE_UP_DIV` 1.1): 269 ticks against 256 on flat. At 2.0 it is 52 percent.
- **The engine's climb progress reads 0 for walkers**; position along the slope has no getter. The lab can compute it.
- **High ground sees down and low ground does not see up** (17 ticks of head start in the best case); the sight radius itself is not longer. A longer fire range from height is a parameter nobody has set.
- **Layouts.** His flank layouts L-0067 to L-0072 run, but the attackers never walk a flank route. His slope layout L-0084 runs. No objective-ring layout exists; his words for it are recorded ("2 groups of units come at two different angles, surrounding blue. Red would be expected to win 80%").
- **The replay** draws a facing tick and the range rings; it draws no arc, no hit marks, no climb and no per-unit band.

## 3. What is built tonight

| Id | Piece | Tests first | Depends on |
|---|---|---|---|
| E1 | Engine: the firing arc, E-13 R-100-04, read from `OM_TP_FIRING_ARC_DEG`; at 360 nothing changes | `tests/csim/` per tick | none |
| L1 | Lab runner: a `--facing on` switch beside `--sight`; facing applied at spawn; the arc set per fight; fight file gains the arc, `climbing` per unit and a `hits` list with front, side or rear | `tests/skilllab/arena/` | E1 |
| L2 | Lab measures and the arc check: hits by front, side and rear, the delay before a flanked unit answers, the climb's slowdown; no shot outside the arc | `tests/skilllab/arena/` | L1 |
| P1 | Probe scenes and layouts: front, side and rear against the same block; flat against slope; a drafted objective ring; his L-0067 and L-0084 run with facing on | a test that each passes the lab's preflight | L1's schema |
| R1 | Replay: arc wedges, hit marks coloured front, side, rear, a climb bar, a band mark per unit, legend rows | `tests/qa/test_fight_replay_stage5.py` | the fight file fields in the story |
| V1 | Clips, one or more per requirement, with facts; the page; the checks | data checks, then the Architect looks at frames (his instruction) | all |

Every piece: a test writer (Sonnet) writes failing tests from the story; a different engineer (Sonnet) builds; an independent checker verifies and mutates. Pieces build in lane worktrees and are merged into `s/lab-stage5` by the chat, `--no-ff`.

## 4. Tool

Tool: Workflow (the deciding question: this run has no Sonnet overlord chat to run a `/manager-mode` cascade, and two of the six pieces end in a frame). The six questions (`docs/northstar/plans/2026-10-21-tool-split-spec.md`):

1. One spec, contract and umbrella test? Yes: story H-091. Points to a cascade.
2. Every unit a failing test without a frame? E1, L1, L2, P1 yes; R1 and V1 need Godot. Mixed.
3. Three or more file-disjoint units? Yes (csrc; lab runner; measures; layouts; replay). Cascade.
4. Must the build stop for Westley? No: every number is a named DRAFT and he has said to log decisions.
5. Post-merge live verification? Yes: the clips. Workflow either way.
6. Frozen contracts? No header symbol, no pipe frame and no save field is added (the parameter already exists).

The sim-side pieces are cascade-shaped by the rule of thumb. A cascade needs a Sonnet Dispatcher chat as overlord; this chat is the Architect (Fable), cannot open or type into another chat, and may not act as a builder. So the Workflow is written to keep the cascade's safeguards: a separate test writer per piece, per-lane worktrees so one lane's green cannot come from another's edits, an independent checker that runs a mutation, and the chat reading each result before the next Workflow. Two Workflows: W1 builds E1 then L1 and L2 on top of it, with P1 and R1 in parallel; W2 records, measures and verifies the clips.

## 5. Lab stage 4 dependencies and the assumption taken for each

| Open on stage 4 | Assumption for stage 5 (least risky) | If it changes |
|---|---|---|
| Lock change (target leaves range, re-pick) | Not built; the lock is as on main. R-100-04 keeps the target while turning, which is the lock as written. | The 8 against 8 numbers move a little; the arc rule itself does not. Re-run the clips. |
| "Same exact spot" (slots or the point) | Group order with formation slots, as on main. Every stage 5 scene is hold against attack (order rule R2), so the two-points question does not arise. | Attackers pack differently; re-run. |
| Trap exceptions | No trap layout is used. | Nothing. |
| Q-087-12 idle firing-spot walk | Untouched. Probe scenes have no cover between the sides. | Nothing in the probes. |
| Q-087-14 return-fire pursuit | Untouched. The holders hold by having no order (stage 3 way) or by guard (stage 4 way, with sight on). | The answer delay of a flanked unit may change; the measure is recomputed. |
| Q-087-15 range against notice distance | Untouched. | First-shot ticks shift equally for front and side. |
| Keep walking (R-099-07) | Stands. Stage 5 adds no rule that moves a unit off its order: a unit outside its arc turns, it does not walk. | n/a |
| Stage 4 sign-off | Stage 5's flank and arc scenes run with sight off, so the unsigned sight rules cannot muddy them; only the height-band scene runs with sight on. | Only the height-band clip is re-made. |

Stage 5 is one switch (`--facing on`). With it off every stage 1 to 4 fight file is byte-identical to main; tests pin that.

## 6. Safety limits (his)

Own branch and worktrees; no force push, no `git rm`, no `reset --hard`, no branch deletion, no merge to main, no push. Beta B5 untouched. The one engine change is R-100-04, new behaviour that is off at the default; it is logged (decision L3).

## 7. Deliverables

- Branch `s/lab-stage5`: story H-091, tests, code, this plan, the decisions log, the report.
- A private artifact page with a clip per requirement (flank hit, side, front, arcs, climb, height bands), added to the artifact ledger.
- What was and was not verified, stated in the report and on the page.
