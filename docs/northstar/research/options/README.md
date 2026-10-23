# Options pass: design options for TBD features

Opened 2026-09-22. Eleven features have a high-level idea in the bible but no defined player-facing behavior. This folder holds, per feature, a perception brief (what the docs say, what Westley said, what is fixed, what is contradictory) and, once Westley confirms the brief, a set of 2 to 4 design options with a diagram each. Options describe the "what" from the player's chair. No implementation, no recommendation. Westley picks; a pick becomes a flag answer and a rule rewrite through the Design Lane.

Precedent for this shape: `../landscape_design/README.md`, the P2 design phase. Nothing here is bible text. `docs/bible/**` and `docs/northstar/ambiguity_register.md` do not change in this pass.

## Method

1. Perception brief per feature (this chat): documented goal, Westley's verbatim words, fixed constraints, prior art, contradictions as questions.
2. Westley confirms or corrects each brief in three chat batches; his answers land verbatim in the brief's "Westley confirms" block.
3. One sub-agent per feature writes `options.md` and one SVG per option against the confirmed brief. Sub-agents research and enumerate; they never decide, recommend, or rank.
4. Review against the checklist below, then one HTML atlas for side-by-side reading.
5. Optional Blue Ocean fusion pass on features Westley names (ERRC grid, strategy canvas, fused options).

## Folder shape

```
<slug>/brief.md                 perception brief, Westley's confirmation, sub-agent brief
<slug>/options.md               2 to 4 options, A to D
<slug>/diagrams/<option>.svg    one diagram per option
```

`.gdignore` keeps Godot from generating `.import` files for the SVGs.

## Atlas

All eleven option sets, side by side with their diagrams, on one page: https://claude.ai/artifact/6571aySFhmoQ1i4XswDhNm (private to Westley). Rebuilt from the files here whenever an options.md changes.

## Decisions (2026-09-23)

Westley read the atlas and answered per feature; his words are verbatim in each brief's section 10, and every pick is folded into the bible with its flag id.

| Feature | Outcome | Decision |
|---|---|---|
| camera | picked | Angle Rack and Layer Peel both, Layer Peel as a player option, plus a 180-degree flip key; control specifics later (Q-103-03, Q-103-04). |
| map-view | prototype | Sand Table is the candidate, prototype before commitment (block-resolution table with a grain-size dial, plus a 45° view with layers separated); more layer-mark ideas beyond pins wanted (Q-103-05, Q-103-06; E-16 S-161). |
| control-groups | picked | Recall and Narrow as the default for groups and multi-layer movement, the Comb for moving individual layers within a group (Q-105-02). |
| layer-system | picked | Terrace Reading combined with Floor Spindle, both subdued; an occlusion indicator for hidden units is open (Q-E01-08 closed, Q-009-02). |
| era-transitions | picked | The Long Horizon (Q-148-01 closed; the reach measure is Q-148-05). |
| era-feel | picked | The Climate of War (Q-151-01). The Long Look is not an era-feel strategy; its idea became a decision that loading screens carry interesting information (E-16 R-110-04, Q-110-03). |
| paired-economy | second pass | None yet. The Works is good but not unique; the Two Clocks needs concrete player actions; the Commons is too broad and not about emotions. Second pass: building and designing efficient pathways and systems as the economy player's task. |
| city-spectacle | second pass | None. New direction: static architecture expands outward on its own as the city grows; small settlements crop up at production facilities and resource objectives and can grow into cities around a critical resource; trade moves visibly between cities; the home base has a resource reason to exist but is not the only source; people go where money and resources are. Second pass with a couple of ideas on this. |
| unit-traits | picked | Unlockable trait cards (Dead by Daylight, Age of Empires 3 register) under a core rule: cards and abilities never outrank positioning, layer damage weighs more, cross-layer-vision cards minimized. Decided, no second pass (Q-083-02, Q-083-03). |
| complications | picked | Crossed Signals (Q-080-02). |
| difficulty-knobs | picked | Neither. Difficulty scales the enemy's economic prosperity and its multi-layer intelligence; a costly seer unit is a desired piece of the layer system (Q-125-02, Q-125-03, Q-E12-01). |

Cross-cutting from the same answers: cross-layer damage and vision are the game's most important undefined mechanic and get a research program with prototypes and humans in the loop (register Q-008-02, research queue Q76); a costly seer unit is a desired piece of the layer system (Q-E12-01); loading screens carry chronicle-register information (E-16 R-110-04); and before the MVP becomes the full game a C4 model of the system is drawn and kept beside the bible (CLAUDE.md).

Second pass owed: paired economy (building and efficient pathways as the task, concrete actions) and self-running city (settlements at resource sites, trade between cities, the home base as one source among many).

## Status

| Feature | Slug | Batch | Brief | Confirmed | Options |
|---|---|---|---|---|---|
| Multi-perspective camera | `camera` | 1 | written | 2026-09-22 | 4 options, reviewed 2026-09-22 |
| Map view zoom band | `map-view` | 1 | written | 2026-09-22 | 3 options, reviewed 2026-09-22 |
| Control group depth | `control-groups` | 1 | written | 2026-09-22 | 3 options, reviewed 2026-09-22 |
| Layer system look and feel | `layer-system` | 1 | written | 2026-09-22 | 4 options, reviewed 2026-09-22 |
| Era transitions | `era-transitions` | 2 | written | 2026-09-22 | 3 options, reviewed 2026-09-22 |
| Era feel differentiation | `era-feel` | 2 | written | 2026-09-22 (4 options) | 4 options, reviewed 2026-09-22 |
| Paired economy multiplayer mode | `paired-economy` | 2 | written | 2026-09-22 | 3 options, reviewed 2026-09-22 |
| Self-running city spectacle | `city-spectacle` | 2 | written | 2026-09-22 | 3 options, reviewed 2026-09-22 |
| Unit passive traits | `unit-traits` | 3 | written | 2026-09-22 | 2 options, reviewed 2026-09-22 |
| Mission complications | `complications` | 3 | written | 2026-09-22 (2 options, surface) | 2 options, reviewed 2026-09-22 |
| Enemy macro difficulty knobs | `difficulty-knobs` | 3 | written | 2026-09-22 | 3 options, reviewed 2026-09-22 |

## Sub-agent template

One agent per feature, launched only when Westley says so. The agent reads, in order: `docs/bible/game_bible.md`, the feature's epic file, its `brief.md` (sections 4 and 8 are the constraints; section 8 wins), and the prior research the brief names. Then it writes `options.md` and one SVG per option in `diagrams/`.

- Role: research and enumerate. Never decide, recommend, or rank. Player perspective only: what the player sees, does, feels, and learns. No implementation, no engine or data language, no file paths, no code.
- Options: the count and wild count in the brief's section 9, labeled A to D. A wild option is a shape no shipped game has and may have no precedent.
- Per option: a name; one paragraph on how it works from the player's chair; a 30 to 60 second play vignette in second person; the brief constraints it honors and the ones it strains, named; prior art with a confidence tag (VERIFIED, REPORTED, ESTIMATED, AMBIGUOUS) or "none"; player-side tradeoffs as consequences; one SVG diagram. Camera and control groups also carry a control table per option.
- Diagram: hand-authored SVG, 960 wide, either a screen wireframe (what the player sees at one moment, labeled regions) or a flow (states the player passes through). Real labels, no lorem, no external images, plain SVG 1.1 with no scripts and no foreignObject, so GitHub renders it.
- Research: WebSearch and WebFetch allowed; cite every prior-art claim; `docs/legacy/games/*.md` may be read.
- Write access: only `docs/northstar/research/options/<slug>/`. Never `docs/bible/**`, `docs/northstar/ambiguity_register.md`, `CLAUDE.md`, tests, code.
- Prose: normal prose in `options.md`; caveman only in the report back to the main agent.
- Length: 600 to 1,500 words plus tables unless the brief says otherwise; the required elements per option set the floor. Longer means the option is drifting into "how".

## Review checklist for an options.md

- Option count matches the brief; the required wild options are present.
- Each option has: a name, one paragraph from the player's chair, a 30 to 60 second second-person vignette, the brief constraints it honors and the ones it strains, prior art with a confidence tag or "none", player-side tradeoffs, one SVG.
- No implementation language. No recommendation or ranking language.
- SVG renders on GitHub: plain SVG 1.1, real labels, no scripts, no external images.
