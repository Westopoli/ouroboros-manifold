# Open Design Questions — INDEX

> **LEGACY MONETIZATION CONTEXT — 2026-05-09**
>
> Several working docs in this folder (notably `era_selection_design.md`,
> `visual_identity_design.md`, `era_mechanical_axes.md`) were drafted under the
> prior subscription/external-checkout monetization model, which has been **scrapped**.
> Current model: buy-once base game + paid Steam DLC expansions, no subscription.
> See `docs/bible_history/game_bible_1_23.md (formerly bible_monetization.md, folded into the hub 2026-05-31)` "Current Monetization Model" section.
> Individual docs in this folder carry their own legacy banners where applicable.

> **Folder purpose.** `docs/design_questions/` is the staging area for
> open design questions — those actively being worked but not yet ready
> for the bible (`docs/bible/`) or a stage spec (`docs/stage_specs/`).
> Each file here is transient: a working doc that bridges chats and holds
> in-progress design discussion until its questions resolve.
>
> **Governance rules — apply to every file in this folder:**
>
> 1. **Governance header required.** Every working doc must start with a
>    header identifying (a) the topic/scope, (b) its transient status,
>    (c) the intended capture target — which bible spoke or stage spec
>    will absorb the resolved content.
> 2. **Capture, then delete from here.** When a question resolves, write
>    the answer into its canonical home (bible hub, spoke, or a stage
>    spec) with a "supersedes" note pointing at any content it replaces.
>    Do not leave a resolution only in the staging doc.
> 3. **Fully captured = deleted.** Once all questions in a doc are
>    captured, delete the doc and remove its entry from this INDEX. If
>    you are an AI session and you see a file here whose questions are
>    all answered, flag it for Westley — do not silently delete.
>
> **If you are an AI session:** read this INDEX first before opening
> anything else in this folder. It tells you what is open, what is
> captured but not yet deleted, and what was archived out of this folder.

---

## Currently Open

### `era_mechanical_axes.md`
**Topic.** Per-era mechanical identity via a mix-and-match dial system
(tempo, information warfare, attrition, layer access, force scale,
terrain expressiveness, environmental events, cross-layer engagement).
8-axis × 3-era matrix positioning Roman / 1980s / Settled Reach with
per-cell rationale.

**Status.** Batches 1–3 complete (governance, per-axis detail, the matrix
with commentary). Batch 4 (Branch DNA vs. hallmark-exclusive annotations)
and Batch 5 (rejected axes + experimental stretch axes including temporal
distortion, supply-line tactics, civilian presence, reinforcement topology)
pending.

**Capture target.** `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) (Branch System extension),
`docs/bible_history/bible_2_00_combat.md` (per-era parameterization flags from Session 6),
`docs/bible_history/bible_2_00_world.md` (map generation gradient consequences).

### `visual_identity_design.md`
**Topic.** Brand visual identity — master shield logo, wordmark, era
variant system, production pipeline (Recraft V4), and the monetization
redesign that branched off it.

**Status.** Mixed. Locked/captured sections document completed work
(master shield four-quarter heraldic design, wordmark custom-ligature
treatment, Recraft V4 pipeline, monetization v3.00 Session 6 decisions).
Q3–Q7 explicitly `[OPEN]`: era card template, Steam page hierarchy,
reference research pass, Canva asset kit, in-game store layout. Deferred
post-launch but not resolved.

**Capture target.** `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) (primary), `docs/bible_history/bible_2_00_combat.md`
(pending edits flagged in Session 6), `game_bible.md` hub.

**Associated assets.** `visual_identity_reference_shield.png` (+ `.import`)
— canonical master-shield reference image, supports Q3–Q7 design work.

### `world_view_disclosure_design.md`
**Topic.** Macro-layer visual and interaction system for the world view
between missions — faction territory visualization (constellation + shell
hybrid), zoom-driven disclosure (Overview / Regional / Local bands),
hover/focus interactions, time-jump animation dynamics.

**Status.** Session 1 done. Q1 (core territory metaphor), Q2 (zoom
disclosure mechanism), Q2.5a (Regional plateau look) answered but not
yet captured. Q2.5b (Overview plateau look), Q2.5c (Local plateau look),
Q3 (hover/focus), Q4 (time-jump animation dynamics) open. Estimated 3–5
more sessions before capture.

**Capture target.** `docs/bible_history/bible_2_00_world.md` (supersedes the projected-Voronoi
paragraph, lines 399–403). Implementation lives in
`scenes/shared/world_view/world_view_structure.gd` and the associated
shader pipeline. Possibly a follow-up to the Stage 11 amendment.

---

## Recently Archived Out Of This Folder (2026-04-21)

The following were removed in a triage pass because their questions were
fully captured and the docs were stale. They are not deleted from history —
they live in `docs/random/` for reference.

- `combat_visual_polish_design.md` → `docs/random/deleted/` — all 9
  questions captured into `docs/bible_history/bible_2_00_combat.md`; Stage 12.5 spec shipped.
- `stage_7_8_design.md` → `docs/random/deleted/` — all S7 / S7.5 / S8
  questions captured into the respective stage specs and bible.
- `Immortal-Gates-of-Pyre-*.jpg` (+ imports) → `docs/random/` — HUD
  reference material for the completed Stage 8 HUD design.
- `igop_hud_reference_README.md` → `docs/random/` — admin scaffolding
  for the Stage 8 HUD design phase.
