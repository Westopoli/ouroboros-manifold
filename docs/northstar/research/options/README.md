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

## Status

| Feature | Slug | Batch | Brief | Confirmed | Options |
|---|---|---|---|---|---|
| Multi-perspective camera | `camera` | 1 | written | 2026-09-22 | |
| Map view zoom band | `map-view` | 1 | written | 2026-09-22 | |
| Control group depth | `control-groups` | 1 | written | 2026-09-22 | |
| Layer system look and feel | `layer-system` | 1 | written | 2026-09-22 | |
| Era transitions | `era-transitions` | 2 | written | 2026-09-22 | |
| Era feel differentiation | `era-feel` | 2 | written | 2026-09-22 | |
| Paired economy multiplayer mode | `paired-economy` | 2 | written | 2026-09-22 | |
| Self-running city spectacle | `city-spectacle` | 2 | written | 2026-09-22 | |
| Unit passive traits | `unit-traits` | 3 | written | | |
| Mission complications | `complications` | 3 | written | | |
| Enemy macro difficulty knobs | `difficulty-knobs` | 3 | written | | |

## Review checklist for an options.md

- Option count matches the brief; the required wild options are present.
- Each option has: a name, one paragraph from the player's chair, a 30 to 60 second second-person vignette, the brief constraints it honors and the ones it strains, prior art with a confidence tag or "none", player-side tradeoffs, one SVG.
- No implementation language. No recommendation or ranking language.
- SVG renders on GitHub: plain SVG 1.1, real labels, no scripts, no external images.
