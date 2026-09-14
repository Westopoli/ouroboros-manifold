# Per-epic MVP cuts

Status: proposal, 2026-09-14. One block per epic. A cut names which stories are in which round; everything not named is "later." Cuts are by omission: a story in a round keeps every rule and every test. A stand-in is a prototype story under Stage 4's prototype rule, marked `S-P##`, replaced (not extended) when the real story is Ready. Story texts are in `../../bible/stories.md`; the round assignments here are the only new information. Rewritten, not annotated, after each gap review.

Round 1 in one sentence: a chapter loop with a real galaxy, a real chronicle, a real commander rotation, and a stand-in mission, on the C sim and a minimal Godot client, packaged by Agora.

## Sim core

### E-02 Region fields and drift
- Round 1: S-012, S-013, S-014, S-015, S-016, S-017, S-018, S-019, S-020 (all nine; already Ready, tests red in `tests/csim/`).
- Validates: the ground truth under H1. Nothing player-facing on its own.
- Stand-in: none. Splits: none.

### E-03 World generation
- Round 1: S-021 (a galaxy to learn, blocked on Q-021-01), S-022 (home versus frontier), S-025 (nobody starts on my doorstep).
- Round 2: S-023 (edge types), S-024 (peace opens trade, conquest closes it).
- Validates: H1's "vast but learnable" feel through the galaxy view.
- Stand-in for Round 1: all edges carry both armies and trade (S-023's default), so S-024 has nothing to close.

### E-04 Events and chains
- Round 1: S-026 (every crisis has a cause), S-027 (follow-ups that may or may not come), S-030 (fixed authored set).
- Round 2: S-028 (same-day stacking), S-029 (revolt as a fever), S-031 (visibly changed on return, blocked on Q-031-01).
- Validates: H1 (change the player did not cause) and H3 (chronicle entries have causes to cite).
- Note: S-031 is the story closest to H1's wording, but its flag is open; Round 1 measures H1 through the interview question instead and S-031's rule is written from what testers actually report.

### E-05 Faction agents and conflict
- Round 1: S-032 (same loop, own personality), S-035 (attack only when the numbers say so), S-037 (outcome scales with decisiveness), S-038 (region changes hands).
- Round 2: S-033 (region pays for itself first), S-034 (conqueror versus fortifier), S-036 (telegraphed versus surprise), S-039 (multi-faction contests).
- Later: S-040, S-041 (open flags Q-040-01, Q-041-01).
- Validates: H1. Factions must visibly gain and lose regions across one jump or the galaxy reads as static.
- Stand-in for Round 1: one shared personality profile until S-034 lands; the loop still runs per faction.

### E-06 Diplomacy and technology
- Round 2: S-042 (stances, blocked on Q-042-01), S-043 (neutral neighbors drift to cooperation), S-045 (one tech level per faction).
- Round 3: S-044, S-046, S-047, S-048.
- Stand-in for Round 1: `S-P02` fixed stances (every pair hostile or neutral by a seeded table, never cooperative) and constant technology. Marked prototype; replaced by S-042 and S-045.
- Validates: nothing directly in Round 1. Deliberately excluded so Round 1's galaxy has fewer moving parts to attribute change to.

### E-07 Civilizational lifecycle
- Round 1: S-049 (a revolt creates a new faction), S-052 (my own civilization can fall).
- Round 2: S-050 (region returns to old owner), S-051 (absorption and disappearance), S-053 (phase label).
- Deferred: S-054 (Q-054-01).
- Validates: H1 at its strongest. A faction born or dead between chapters is the most legible "the world moved" signal available.
- Note: S-052 in Round 1 needs E-08 S-062's "keep playing in a surviving one" or the campaign ends. Round 1 takes the simpler path: the campaign ends with a final chronicle page and a "your line ended" screen. That is a stand-in for S-062 (`S-P03`) and is itself a test of H2's emotional weight.

## Generational and narrative

### E-08 Generational structure
- Round 1: S-055 (chapter order), S-058 (next commander is usually family), S-059 (descendants spread nearby), S-064 (world remembers, character starts fresh).
- Round 2: S-056 (the world decides how many decades, Q-056-01), S-057 (stay with a bloodline, Q-057-01), S-060 (named people are born, serve, age, die), S-061 (relative takes a fallen commander's place).
- Round 3: S-062 (Q-062-01), S-063 (onboarding preferences, needs reference).
- Stand-in for Round 1: `S-P04` fixed jump length (one value, seeded jitter of plus or minus 10 percent) until S-056's flag is answered. `S-P05` onboarding is one screen: pick a difficulty, nothing else.
- Validates: H2 directly. The commander rotation is the carry-forward mechanism.
- Splits: S-055 names six phases; the Round 1 rule set for S-055 covers briefing, resolution, time jump, and new commander, with "recon" and "mission" satisfied by the E-10 stand-in. Split in the epic file if the rules exceed one card.

### E-09 Chronicle
- Round 1: S-065 (opens with my mission, then my family, then the age; Q-065-02 open), S-066 (first contact always makes it, small events only if they snowballed), S-068 (reads like a passage from a real history), S-071 (never repeats a sentence).
- Round 2: S-067 (a chain is one entry; Q-067-01), S-069 (split-screen scroll, needs reference), S-070 (family deeds bubble up).
- Validates: H3 and H8. This epic is where "personality-load in the first 30 minutes" lives.
- Library source for Round 1: the existing corpus in `simulation/library/chronicle/fragments.json`, passed through E-21's validator, is the Round 1 library. No new prose generation before Round 1. If the validator rejects more than the batch threshold, that is a Round 0 finding, not a reason to generate.
- Stand-in for S-069 in Round 1: the scroll is a full-screen text page with the galaxy view reachable by one key. Split-screen waits for its reference.

### E-10 Missions
- Round 1: S-073 (a recognizable military situation with its own trigger and shape), S-077 (result is a spectrum), S-078 (outcome changes the region in proportion), plus stand-in `S-P01`.
- Round 2: S-072 (missions from real trouble, Q-072-01), S-075 (one primary, up to three secondary), S-076 (deadline as pressure, Q-076-01), S-079 (orders as a superior gives them, needs reference).
- Round 3: S-074 (force sizing, Q-074-01), S-080 (hard mode, Q-080-01).
- **Stand-in `S-P01`, the Round 1 mission.** The tactical engagement is replaced by one screen: the briefing states the situation and the force ratio; the player chooses commit, hold, or withdraw; the outcome resolver's band math takes the force parity, the choice's modifier, and one seeded roll, and returns a band on S-077's spectrum. The screen shows the band and the casualties. Shape options are `Q-MVP-02`. This is a prototype story: it exists so Round 1 can test H2 and H1 without tactical, and it is deleted when E-11, E-13, and E-12's Round 2 stories are Built.
- Validates: H2 (the outcome must change the region, S-078), H9 partially (S-073's shape and trigger are visible in the briefing).
- Deliberately does not validate: anything about how a mission feels to play. Testers are told this in the Round 1 README.

## Tactical

### E-11 Units, abilities, and damage
- Round 2: S-081 (soft rock-paper-scissors; Q-081-01 open), S-082 (six units, one job each), S-084 (damage is simple), S-085 (fights last long enough to read), S-087 (flinch, obey, shoot the nearest).
- Round 3: S-083 (Q-083-01), S-086 (one ability each), S-088 (needs reference).
- Validates: H4, H6, H5.
- Splits: S-087's three-check loop is one card; S-084's damage table is one card. Confirm against the 250-line sizing rule in Stage 3.

### E-13 Movement, pathing, and command
- Round 2: S-096 (four commands), S-097 (route around, flow around), S-100 (face what you shoot), S-102 (every peer computes the same movement).
- Round 3: S-095 (Q-095-01), S-098, S-099, S-101 (all flagged or need reference).
- Validates: H6, and the R4 catalog's stuck, rubber-band, and backwards-walk detectors get their first real target.
- Note: this epic carries five open flags today. Round 2 cannot open until the four Round 2 stories are Ready; the flagged ones are excluded rather than guessed.

### E-12 Fog and sensors
- Round 2: S-089 (revealed only around my units), S-092 (study the whole map, then lose it), S-093 (fog changes what I know, never what happens).
- Round 3: S-090 (Q-090-01), S-091 (Q-092-01), S-094 (needs reference).
- Validates: H6 (reading the field is a skill only if the field is partly hidden).

### E-17 Map generation
- Round 2: S-112 (hand-authored layouts; Q-112-01 open), S-113 (nine place types), S-117 (maps that do not cheat; Q-113-01 open).
- Round 3: S-114, S-115, S-116, S-118, S-119.
- Stand-in for Round 2 if S-112's flag stays open: `S-P06` one hand-authored layout, fixed, with seeded flavoring off. A fixed map is enough to test H6 on a scripted scenario and is arguably better for it.
- Validates: H6's "smaller force with a surround" needs a chokepoint and a flank that exist on purpose.

### E-14 Enemy macro behavior
- Round 2: S-120 restricted to advance and hold (Q-120-01 covers the full list), S-123 (replays exactly).
- Round 3: S-121, S-122, S-124, S-125.
- Stand-in for Round 2: the two-behavior enemy is `S-P07`, replaced when S-120's flag is answered and the full set lands.
- Validates: H4. A loss must have a cause the tester can see, which needs an enemy that does something legible.

### E-15 Reinforcement, supply, and hazards
- Round 2: S-127 (capture by holding unopposed).
- Round 3: S-126 (Q-126-01), S-128, S-129 (Q-129-01), S-130, S-131 (needs reference).
- Stand-in for Round 2: `S-P08` fixed starting force, no reinforcement structures beyond one capturable garrison for S-127.
- Validates: H5 (the garrison is the "no base, but something to take" answer).

### E-01 Layer system
- Round 3 only, with the option chosen in the design phase (README decision 2026-09-13). Single layer in Rounds 1 and 2.
- Validates: H7.
- Nothing from E-01 is cut here; the whole epic waits on its design phase, which is itself run as an experiment with Westley as the first tester.

## Client and cross-cutting

### E-16 Camera, HUD, world view, and screens
- Round 1: S-106 (star map where territory glows; needs reference, minimal form), S-107 (pan, zoom, focus), S-110 (main menu; Q-110-01 open, minimal form), S-111 (autosave at chapter boundaries; Q-111-01 open), plus the chronicle page and the `S-P01` decision screen as surfaces.
- Round 2: S-103 (free camera; Q-103-01), S-104 (lean HUD; needs reference), S-105 (click, box-select, groups; Q-105-01).
- Round 3: S-108 (mission pulls back into the galaxy without a cut), S-109 (screens read as orders and reports).
- Stand-in for Round 1: `S-P09` minimal galaxy view: regions as points, edges as lines, owner as color, pan and zoom, one click to inspect. The existing in-game galaxy animation is the reference (README decision 2026-09-13), not the code.
- Validates: H1 needs the galaxy to be looked at; H3 needs the chronicle to be read. Both are this epic's surfaces.
- Gate: every Round 1 story here is a client card and waits on probe H.

### E-18 Visual style and combat visuals
- Round 2: S-132 (a readable shape per unit type; needs reference), S-138 (one look, low-poly; needs reference), both in minimal form: six silhouettes, one palette, no combat effects.
- Round 3: S-133, S-134, S-135, S-136, S-137.
- Round 1: nothing. The galaxy view uses flat shapes.
- Validates: H12. Also H6 indirectly: testers cannot position what they cannot tell apart.

### E-19 Multiplayer
- Later. S-139 (every peer computes the same galaxy) is carried by E-02 S-020 and E-13 S-102; no separate Round work.

### E-20 Multi-era and monetization
- Round 1: S-145 (the engine never says starship) holds by construction and is tested by grep in E-02's suite.
- Round 3 (survey): S-149 (a fair price and earnable expansions) as a survey question only.
- Later: S-146, S-147, S-148, S-150.
- Validates: H10, survey only.

### E-21 Offline AI pipeline
- Round 1: S-152 (works with no network and no model), S-158 (Agora reads distilled rules).
- Round 2: S-153 (one pipeline for every text library; Q-153-01), S-154 (names that belong together; Q-155-01).
- Round 3: S-155, S-156.
- Round 1 uses the existing chronicle corpus (see E-09) and existing names; the pipeline's own stories wait.

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

## Stories cut from every round on purpose

S-040, S-041 (E-05 flags); S-054 (deferred); S-151 (deferred); S-157 (deferred); all of E-19; S-146, S-147, S-148, S-150 (E-20 pack mechanics). They stay Spec'd or Deferred in the catalog. A gap review may pull any of them forward; nothing here kills a story.
