# Per-epic MVP cuts

Status: Round 1 cut set by Westley's answer to `Q-MVP-01` on 2026-09-14: every major feature is in Round 1 in the most minimal capacity possible, including a prototype camera, a prototype two-layer layer system, and a prototype map generator. Rounds 2 and 3 are still proposals. One block per epic. A cut names which stories are in which round; everything not named is "later." Cuts are by omission: a story in a round keeps every rule and every test. A stand-in is a prototype story under Stage 4's prototype rule, marked `S-P##`, replaced (not extended) when the real story is Ready. Story texts are in `../../bible/stories.md`; the round assignments here are the only new information. Rewritten, not annotated, after each gap review.

Round 1 in one sentence: one thin chapter loop with every system present at its smallest, on the C sim and a new Godot client, packaged by Agora: a real galaxy, a real chronicle, a real commander rotation, one small real-time mission on a generated two-layer map with six units and fog, and everything a tester needs to send feedback back.

Where a story a round needs carries an open flag, Westley answers it or a prototype story stands in. Track L never guesses to hit a round.

## Build order inside Round 1

The sim ladder builds and T1-tests first (E-02, E-03, E-04, E-05, E-06, E-07, E-08, E-09, E-10, E-21), then the tactical sim (E-11, E-13, E-12, E-17, E-14, E-15, E-01 prototype), then the client (E-16, E-18, E-22), which waits on probes H and I. While the tactical slice is unbuilt, `S-P01` resolves missions so the macro loop can be tested end to end early; it is removed the day the tactical slice is Built.

## Sim core

### E-02 Region fields and drift
- Round 1: S-012 to S-020 (all nine; Ready, tests red in `tests/csim/`).
- Validates: the ground truth under H1.

### E-03 World generation
- Round 1: S-021, S-022, S-025 (Q-021-01, Q-021-03, Q-021-04, Q-021-05 answered).
- Round 2: S-023, S-024.
- Round 1 default: every edge carries both armies and trade until S-023.

### E-04 Events and chains
- Round 1: S-026, S-027, S-030.
- Round 2: S-028, S-029, S-031 (Q-031-01).
- Validates: H1 and H3 (entries have causes to cite).

### E-05 Faction agents and conflict
- Round 1: S-032, S-035, S-037, S-038, S-036 (telegraphed versus surprise, because missions come from telegraphed attacks).
- Round 2: S-033, S-034, S-039.
- Later: S-040, S-041 (open flags).
- Round 1 default: one shared personality profile until S-034.

### E-06 Diplomacy and technology
- Round 1: S-043 (neutral neighbors drift to cooperation), S-045 (one tech level per faction). Stances exist through S-043's rules; S-042 itself waits on Q-042-01.
- Round 2: S-042, S-046, S-047, S-048.
- Round 3: S-044.
- Validates: H1 (peace and war visibly shift between chapters).

### E-07 Civilizational lifecycle
- Round 1: S-049, S-052, S-053 (phase label; it drives the five feelings the hub names), and E-08 S-062 (Q-062-01 answered) so a fallen civilization hands the player to a survivor instead of ending the campaign.
- Round 2: S-050, S-051.
- Deferred: S-054.

## Generational and narrative

### E-08 Generational structure
- Round 1: S-055, S-056 (Q-056-01 answered: uniform 20 to 100), S-058, S-059, S-062, S-064, S-063 in minimal form (pick a difficulty; mission preferences wait).
- Round 2: S-057 (Q-057-01), S-060, S-061.
- Validates: H2.

### E-09 Chronicle
- Round 1: S-065 (Q-065-02 open; answer or the opening order is fixed as mission, family, age with no exceptions), S-066, S-068, S-069 in minimal form (galaxy on one side, scroll on the other, no animation choreography), S-071.
- Round 2: S-067 (Q-067-01), S-070.
- Library for Round 1: the existing corpus in `simulation/library/chronicle/fragments.json`, passed through E-21's validator. No new prose generation before Round 1.
- Validates: H3, H8.

### E-10 Missions
- Round 1: S-073, S-075 (one primary objective, no secondaries), S-077, S-078, S-079 in minimal form (three-part orders as plain text, no voice, no art).
- Round 2: S-072 (Q-072-01), S-076 (Q-076-01).
- Round 3: S-074 (Q-074-01), S-080 (Q-080-01).
- Stand-in `S-P01`, per `Q-MVP-02`: an auto-resolved card. The briefing states the situation; the outcome resolver's band math takes force parity and one seeded roll and returns a band on S-077's spectrum; the card shows the band and casualties. No player choice, exactly as the real game gives no choice about orders. Used only while the Round 1 tactical slice is unbuilt, then deleted.
- Validates: H2, H9.

## Tactical

### E-11 Units, abilities, and damage
- Round 1: S-082 (six units), S-084 (damage), S-085 (fights last long enough to read), S-087 (flinch, obey, shoot the nearest). Abilities off.
- Round 2: S-081 (Q-081-01), S-086, S-083 (Q-083-01).
- Round 3: S-088.
- Validates: H4, H6, H5.

### E-13 Movement, pathing, and command
- Round 1: S-096 (four commands; ability is a no-op until S-086), S-097, S-100, S-102.
- Round 2: S-095 (Q-095-01), S-098, S-099.
- Round 3: S-101.
- Validates: H6; first real target for the R4 stuck, rubber-band, and backwards-walk detectors.

### E-12 Fog and sensors
- Round 1: S-089, S-092, S-093.
- Round 2: S-090 (Q-090-01), S-091 (Q-092-01).
- Round 3: S-094.
- Validates: H6.

### E-17 Map generation
- Round 1: S-113 (nine place types) and prototype `S-P06`: a seeded generator that lays a spine of waypoints from one layout family, places two chokepoints and one flank, assigns place types, and marks which cells are blocked on layer 2. No gradient flavoring, no fairness gate, no blending. Replaced by S-112, S-114, S-117, S-119 when their flags are answered.
- Round 2: S-112 (Q-112-01), S-117 (Q-113-01), S-116 (Q-118-01).
- Round 3: S-114, S-115, S-118, S-119.
- Validates: H6, and whether a generated map reads as intentional at all.

### E-14 Enemy macro behavior
- Round 1: S-123 (replays exactly) and prototype `S-P07`: an enemy that advances toward the objective and holds when it has the numbers; nothing else. Replaced by S-120 when Q-120-01 is answered.
- Round 2: S-120, S-121, S-125.
- Round 3: S-122, S-124.
- Validates: H4.

### E-15 Reinforcement, supply, and hazards
- Round 1: S-126 (Q-126-01 answered 2026-09-14: code values, no cost, no trickle) and S-127 (capture by holding unopposed); no convoys, no hazards, no drift.
- Round 2: S-128, S-130.
- Round 3: S-129, S-131.
- Validates: H5.

### E-01 Layer system
- Round 1: prototype `S-P10`, the two-layer prototype (README decision, revised 2026-09-14): exactly two layers; a selected unit can be ordered to the other layer and visibly rises or drops to it over a per-type duration; terrain marks some cells blocked on layer 2; a unit sees the other layer at a shorter range than its own; the HUD shows each unit's layer and which layer the player is focused on. Drawn from S-002, S-004, S-005, S-009, S-010 at their smallest, without claiming any of them Ready. This prototype is the first option in the layer design phase; testers' reactions feed that phase. Replaced by E-01's stories once the design phase picks an option.
- Round 2: further design-phase options on the same prototype.
- Round 3: E-01's stories proper, with the chosen option.
- Validates: H7 (measure only in Round 1).

## Client and cross-cutting

### E-16 Camera, HUD, world view, and screens
- Round 1: S-106 and S-107 in minimal form (regions as points, edges as lines, owner as color, pan, zoom, click to inspect; the existing in-game galaxy animation is the reference), S-110 in minimal form (title, new campaign, continue, quit), S-111 (autosave at chapter boundaries; Q-111-01 answered or one slot), S-103 (fixed top-down interim, Q-103-01 answered 2026-09-14), S-105 (click, box-select across every layer, layer hotkeys narrow, control groups with exclusive membership; Q-105-01 answered 2026-09-14), and one prototype: `S-P12` HUD (selection panel, one objective line with progress, layer indicator, mission clock; the lean-HUD reference wait is for S-104 proper).
- Round 2: S-104 replacing `S-P12`; S-109.
- Round 3: S-108.
- Validates: every hypothesis needs these surfaces; the UI-bounce metrics live here.
- Gate: every Round 1 client card waits on probe H.

### E-18 Visual style and combat visuals
- Round 1: S-132 and S-138 in minimal form: six distinct silhouettes, one palette, faction color, no combat effects beyond a hit flash.
- Round 2: S-134 (Q-134-01), S-135, S-136 (Q-136-01).
- Round 3: S-133, S-137.
- Validates: H12.

### E-19 Multiplayer
- Later. S-139 is carried by E-02 S-020 and E-13 S-102.

### E-20 Multi-era and monetization
- Round 1: S-145 holds by construction and is tested by grep in E-02's suite.
- Round 3 (survey): S-149.
- Later: S-146, S-147, S-148, S-150.

### E-21 Offline AI pipeline
- Round 1: S-152, S-158, and the validator run on the existing chronicle corpus.
- Round 2: S-153 (Q-153-01), S-154 (Q-155-01).
- Round 3: S-155, S-156.

## Proposed epic E-22 Playtest delivery and telemetry

Not in the bible yet. Proposed here; the epic file and catalog rows are a follow-up PR through the normal Stage 2 gate. Story list in the commander's words:

- "I download one file, unzip it, double-click it, and I am at the main menu with nothing else installed." (Round 1; export preset and ZIP card; probe I is its proving-ground twin.)
- "The first screen tells me what is recorded on my machine and asks before recording anything." (Round 1; consent per `Q-MVP-03`.)
- "A session file on my machine records what I did, in plain text I can read, and never leaves my machine unless I send it." (Round 1.)
- "One key captures a bug report with logs and a screenshot and tells me where it went." (Round 1.)
- "A feedback form in the download asks me questions I can answer in ten minutes." (Round 1; the form is the metric list in `README.md`.)
- "A build I get from Discord tells me its version and which round it is." (Round 2.)
- "A weekly digest of what testers reported is written from the files, with no model reading my session." (Round 2; offline script.)
- "The Steam Playtest build asks the same questions in-game." (Round 3.)

Every one of these is an Agora card, gated on probes H and I.

## Prototype stories in Round 1

| Id | Stands in for | Removed when |
|---|---|---|
| S-P01 | the tactical mission, as an auto-resolved card | the Round 1 tactical slice is Built |
| S-P06 | E-17 generator stories | S-112, S-114, S-117, S-119 Built |
| S-P07 | E-14 S-120 behaviors | Q-120-01 answered and S-120 Built |
| S-P10 | E-01, two-layer prototype | the layer design phase picks an option and E-01's stories are Built |
| S-P12 | E-16 S-104 HUD | S-104's reference attached and Built |

## Stories cut from every round on purpose

S-040, S-041 (E-05 flags); S-054 (deferred); S-151 (deferred); S-157 (deferred); all of E-19; S-146, S-147, S-148, S-150 (E-20 pack mechanics). They stay Spec'd or Deferred in the catalog. A gap review may pull any of them forward; nothing here kills a story.
