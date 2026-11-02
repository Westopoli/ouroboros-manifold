# Parts and whole: the lab's decomposition idea

Status: DECIDED as a plan, 2026-11-02, from Westley's answers to the proposal's section 7. It is built only after the simulation lab is finished (his words: "how we'll do that is a decision for a later time when we're actually building this (post simulation lab creation)"). Nothing in the lab's order of work changes for it: the staircase, the batches and the stories in flight run as they are. The proposal and its history are in `docs/northstar/story_reviews/westley/2026-11-02-piecemeal-then-whole-proposal.md`.

## 1. The idea, in his words

Westley, 2026-11-02, after the stage 2 pictures: "only testing *all* the variables might not be as informative as what we're doing now. Maybe a single simulation lab run of a single configuration should not only run *all* of them in a single fight, but specific layouts like what we're doing now, maybe individual segments (like role interactions) might not pass (lines don't cross), but when all the variables are included the lines do cross. What exactly that means I do not yet know, but I think the simulation lab would provide better data if we ran things piecemeal, and then all together, for each configuration, instead of only together."

This is the lab's original search made concrete, not a new principle: `research/layer_dynamics/README.md` section 8, step 7 already says the search for every region of settings where the conditions hold runs "two ways side by side: all settings at once, and step by step" ("start the prototype with 2 variables, tune them until the expected behavior is exhibited, and then just keep iteratively adding and tuning"). Decomposition applies that to one configuration at a time: the parts alone, then the whole.

## 2. Preconditions it must keep (from the strategic-depth documents)

The decomposition is worthless if it turns strategic depth into a pass mark. These are the standing rules it inherits, each with its source.

1. The goal. "players with better understanding of the landscape, unit formation, layer awareness/intentionality, and the other players current position can defeat a much larger force" (Westley, 2026-10-01; `research/layer_dynamics/README.md` section 1; bible principle 4, skill ceiling as the design target). The lab's purpose is to find strategic depth around where the lines cross.
2. The lines cross in more than one place. "The *lines* can cross in multiple locations, there may be configurations where health/range/vision/ping distance is much higher/lower but the expected behavior is exhibited." (2026-10-01) and "the whole point of the simulation lab is to find *multiple* points where the *lines cross*, not just one configuration" (2026-10-15). So a part has no single headcount, no single ratio and no single pass mark: each part reports where its own lines cross (the break-even headcount as a function of the setting), may show several crossing regions, and may show none inside the scanned range. A report that names one number per part is incomplete.
3. Depth is not a number. "it depends on the number of units that can get shots, not a basic ratio ... That will indicate the quality of the choke, not just that they should do *1.3x* better because it's not as simple as that." (README section 2). On the weak edge of the category triangle (Strike against Line): "it does not have a headcount, this can vary where the lines cross. Strategic depth can't be diluted to a specific number as simple as that" (Westley, 2026-11-02). The yardstick stays the number of units able to fire and for how long, with the category multiplier weighting each shot ("not just unit values but their type as well").
4. Soft counters, never hard. Bible principle 5: "Decisions have counters, counters have counters, and none is dominant. Soft rock-paper-scissors, never hard." The category triangle sets which way an advantage points, not a fixed multiple of headcount. The one numeric rule he has stated is L-0102's: "siege is designed to beat line, even double the force of line shouldn't beat siege" (2026-11-02), and he added that a lopsided result at equal counts and roles is a flag, "only a signal, not a conclusion" (L-0104).
5. Same units, same values on both sides. A skilled play differs from a naive one only in arrangement, orders and which roster types stand where (README section 4, ruling of 2026-10-13). Parts are built the same way: a part changes one thing and nothing is rescaled in its favour.
6. The control. With everything identical the larger force wins; it is a control, not a scenario (README section 2). Every arm keeps its mirror control.
7. Findings are never smoothed over, and thresholds are his. A part that fails where the whole crosses (his case) is a finding with its picture; the lab reports data, and pass marks are Westley's to set (README section 4 and section 5).

## 3. The arms (a first draft that is expected to grow)

For each configuration the lab runs the same configuration in several arms and shows them side by side. The whole arm is what the lab runs today.

| Arm | What is on | What it reports |
|---|---|---|
| R: role pairs | two roles only, flat field, mirrored positions, no features, one orders rule | for every ordered role pair, where the lines cross as the headcount of each side varies (the lab's scan: break-even headcount, margin, units firing), as a curve or a map, with every crossing region it shows. It does NOT test fixed ratios such as 1:1, 2:1 and 1:2 as pass or fail. |
| F: one factor | the whole force, one factor at a time off its neutral setting | what each factor does to the firing count and to the crossings alone. The first list is: positioning (arc, surround), formation (block, interleaved), terrain features, sight, height bands, orders. |
| P: factor pairs | two factors together where a stage suspects an interaction | whether two factors that fail alone cross together |
| W: whole | everything on, the layout as authored | the result the lab reports today |

The factor list for arm F is provisional on purpose (Westley, 2026-11-02: when it is time to specify, "very concretely and specifically, all the different variables, we may want to expand this list"). When that specification is written it will also take in the other variables the lab already names: the three layer actions (ping, going dark, reach by unit type), the firing arc and the cone, area damage, emitting, abilities, speed and cover, and anything the staircase adds. The list is never a closed set.

Four readings are named on the page for each configuration: all pass; the parts pass and the whole fails; a part fails and the whole crosses; all fail. A flag is a signal, never a verdict; a configuration is invalid only by a rule Westley states (today only the L-0102 sentence in section 2).

Era configuration check (the L-0102 rule made mechanical, later): arm R over a roster prints, per role pair, the crossing it finds and flags a pair that contradicts a rule he has stated. A roster with such a flag goes back to him, not to a release.

## 4. What is decided and what is not

Decided (Westley, 2026-11-02, answering the proposal's section 7): (1) no additional rules are needed beyond the triangle and his L-0102 sentence; (2) the weak edge has no required headcount, where the lines cross can vary, there may be several headcounts at which depth is induced, and the documents must say so; (3) the arm F list is a first draft to be expanded when the variables are specified concretely, and the documents must say so; (4) a failing pair is flagged; whether a flag ever blocks a configuration from later batches is decided when this is built.

Not decided: the final arm F list; how arm R scans (one ratio, or each side's headcount varied independently over 8 to 256); how a failing part is shown beside a crossing whole; the story ids and their order; the place relative to the stage 6 scan. These are specified after the lab is finished.

## 5. When

After the simulation lab is finished (`docs/northstar/plans/2026-10-27-lab-plan-of-record.md` section 1: the crossings documented extensively for every knob family and every skill, and read by Westley). Until then the staircase continues unchanged; the stage 3 control strip (with and without the ground) is this idea in miniature and is not generalised before then. No story exists for it; the role-pair deliverable proposed as H-064 is parked here.

## 6. Sources read for this document

`research/layer_dynamics/README.md` (sections 1 to 8), `research/layer_dynamics/heuristics.md`, `plans/2026-10-27-lab-plan-of-record.md`, `research/layer_dynamics/audits/2026-10-04_rules_against_strategic_depth.md`, `research/map_design/prior_art_strategic_depth.md`, `docs/bible/game_bible.md` principles 4 and 5, `docs/bible/epics/E-01-layer-system.md` (the end-state paragraph), `docs/northstar/story_reviews/westley/crossings.md`.
