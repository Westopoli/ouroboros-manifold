# Control group depth: options

Three ways a player reaches into a control group that spans layers, without a select-all. All three keep the flat-digit, exclusive-membership bind as written, differing only in how a player narrows from "the whole army" to "just this layer."

## Option A — Recall and Narrow

Nothing new to learn. Bind each army as any control group: select, Ctrl plus a digit. The group holds whatever mix of layers it had at bind time, and the digit recalls all of it regardless of layer. To work one layer, recall the group, then tap that layer's hotkey; the selection narrows, and the strip's focus never moves because of it. A group is a group, a narrow is a narrow, and the two compose.

**Play vignette.** Army 2's strike wing rides layer 4 over a line force on layer 2, and the wing needs to peel off for a flank. You tap 2 — the whole army answers. You tap the layer-4 hotkey; the selection collapses to the raiders, the line force dropping from the panel. You right-click a spot northeast; the raiders move on their own layer, the line untouched. You tap Ctrl plus 4 to bind them to a fresh slot. At army 3, you double-tap 3; the camera snaps to your siege line under fire, and ring colors show who dropped to cover a lower approach.

| Action | Input |
|---|---|
| Bind | Select units, Ctrl plus digit |
| Recall | Digit |
| Narrow to a layer slice | Digit, then the layer's hotkey |
| Select a set inside a group | Recall, then box or Shift-click; or narrow first, then box or Shift-click |
| Move a selection to another layer | With a manual selection active, issue a hard layer transfer |
| Split | Select the subset, Ctrl plus a new digit; exclusive membership pulls it from the old group |
| Merge | Recall X, Shift-recall Y, Ctrl plus either digit folds both into one |
| Center camera | Double-tap the digit |

**Exclusive membership.** One unit, one group; layer has no bearing on it. Narrow army 2 to layer 4 and bind it to a new digit, and those units leave army 2's group the instant the bind lands — its tab count drops at once.

**HUD group tabs.** Each tab shows one icon and one count, as today — a mixed-layer army reads "38 units," no per-layer breakdown, until a player narrows and checks the strip.

**Honors:** R-105-01 to R-105-06, R-104-07, Alt-layer-preference, right-click-keeps-layer, deliberate-layer-change, slowest-pace-with-split, focus-never-filters-orders.
**Strains:** reaching one of nine slices costs two keypresses every time, with no memory of it unless a player spends a group slot on it.

**Prior art.** SC2 subgroup Tab-cycling — VERIFIED, Blizzard's "Simplified Controls" guide; it cycles by unit type, not layer, so the resemblance is structural only. Halo Wars' Ctrl-plus-number bind — REPORTED, converging community sources; no official cite found for double-tap-to-center in the original.

**Tradeoffs.** No new gesture, HUD unchanged. Cost lands on memory: every fast slice needs its own bind, competing for the same ten scarce slots as everything else.

Diagram: diagrams/option-a.svg

## Option B — Layer Sub-Tabs

The top-level bind is unchanged. The instant a bound group holds units on more than one layer, its tab grows a second row: one chip per layer present, ring color and live count. A player reaches one slice by holding the digit and tapping the layer number while held — one chord, not two taps — or clicking the chip. The bare digit still recalls the whole army.

**Play vignette.** Army 1 holds a ridge, Bastions on layer 2, Vanguards screening on layer 3. Two chips sit under the "1": a dim green "2" reading 14, a bright blue "3" reading 6. You hold 1 and tap 3; only the six Vanguards highlight. You right-click behind the ridge; they walk there on layer 3, Bastions untouched. Army 2 shows one chip — its force sits on layer 4 — so a plain tap of 2 is enough. Army 3 grows a third chip mid-fight as a flanking group climbs, and your line has split three ways before you've ordered anything.

| Action | Input |
|---|---|
| Bind | Select units, Ctrl plus digit |
| Recall (whole group) | Digit |
| Narrow to a layer slice | Hold digit, tap the layer number; or click the chip |
| Select a set inside a group | Narrow to a chip, then box or Shift-click within it |
| Move a selection to another layer | With the chip's selection active, issue a hard layer transfer |
| Split | Select via chip or hand-pick, Ctrl plus a new digit; the old chip shrinks or disappears |
| Merge | Recall X, Shift-recall Y, Ctrl plus either digit; chips recompute from the combined mix |
| Center camera | Double-tap the digit (whole group); double-tap a chip (that slice) |

**Exclusive membership.** Still one unit, one group; chips are a display and shortcut, not a second grouping layer. Membership changes redraw the chip row at once — no separately-bound "layer group" can go stale.

**HUD group tabs.** A single-layer group shows a plain tab. A multi-layer group grows a chip per layer present, with color and live count; a layer with zero units shows no chip, so the row's width shows how spread out that army is.

**Honors:** R-105-01 to R-105-06 (narrow works as a fallback), R-104-07, Alt-layer-preference, right-click-keeps-layer, deliberate-layer-change, slowest-pace-with-split.
**Strains:** adds HUD surface and a chorded input the base rules don't describe.

**Prior art.** Supreme Commander's flat Ctrl-plus-number bind — VERIFIED, convergent community guides; its own groups are flat and non-exclusive, so the resemblance holds only for the base bind. Live per-layer HUD chips on a tab — AMBIGUOUS, no located precedent.

**Tradeoffs.** A slice reachable in near one motion, a HUD that shows spread at a glance. Cost is a chord to learn and a HUD element that comes and goes as a fight develops.

Diagram: diagrams/option-b.svg

## Option C — The Comb (wild)

No cycling, no chord. Holding a digit still recalls the whole army. While held, the layer strip blooms: every layer that army occupies lights up as a bar sized to its unit count there. Dragging across one, two, or three bars and releasing makes those layers the live selection; the rest drops out, and letting go collapses the strip to five thin rings. One gesture, hold-drag-release, picks any layer combination without a second key.

**Play vignette.** Army 3 has scattered chasing a broken line: Wardens on layer 2, Vanguards on layer 3, a Bombard on layer 4, Raiders regrouping on layer 5. Everyone below the Bombard needs to disengage while the rest presses on. You hold 3; the strip blooms into four bars. You drag layer 2 through layer 3 and release — Wardens and Vanguards become your selection, the rest untouched. You right-click a rally point and they disengage, each still on its own layer. You release 3, hold again, drag layer 4 through 5, and push the rest forward. Two gestures, four layers sorted.

| Action | Input |
|---|---|
| Bind | Select units, Ctrl plus digit |
| Recall (whole group) | Digit |
| Narrow to a layer slice | Hold digit; drag across one bar on the bloomed strip; release |
| Select a set inside a group | Hold digit, drag across the bars wanted, then Shift-click or box within the result |
| Move a selection to another layer | With the dragged selection active, issue a hard layer transfer |
| Split | Comb out a slice, Ctrl plus a new digit; the bar shrinks or vanishes from the bloom |
| Merge | Recall X, Shift-recall Y, Ctrl plus either digit; the bloom reflects the combined spread next hold |
| Center camera | Double-tap the digit |

**Exclusive membership.** One unit, one group, unaffected by the comb; the bloom reads the group's current spread fresh each hold, never a stored substructure. A unit combed out and rebound leaves the old bloom immediately.

**HUD group tabs.** The tab stays exactly as specified, one icon and one count, at rest; the bloom exists only while its digit is held, so no group carries permanent clutter.

**Honors:** R-105-01 to R-105-06 (plain narrow still works), R-104-07, focus-never-filters-orders (the bloom is transient), Alt-layer-preference, right-click-keeps-layer, deliberate-layer-change.
**Strains:** loads tap-to-recall, double-tap-to-center, and hold-drag-to-comb onto one digit, three behaviors the base rules never specify together; a mistimed drag has no fixed resolution.

**Prior art.** None located. No shipped RTS exposes a live per-layer bar chart on key-hold with a gestural drag to slice a selection from a bound group.

**Tradeoffs.** Any layer combination in one motion, with a HUD that shows the bloom only on request. Cost is a gesture nothing else teaches, one key carrying three timing-dependent meanings, and a harder recovery from a fumbled drag.

Diagram: diagrams/option-c.svg

## Findings

None of the fixed constraints in sections 4 and 8 go unhonored — R-105-01 through R-105-06, R-104-07, Alt-layer-preference, right-click-keeps-layer, deliberate-layer-change, and the select-all ban hold in all three, not one apiece. The one shared tension: a flat digit plus no select-all leaves no uncontested one-tap route to a slice smaller than "whole army." Each option pays for slice-level reach with a second input — a second tap in A, a held chord in B, a held drag in C — because that is the only room the fixed rules leave open.
