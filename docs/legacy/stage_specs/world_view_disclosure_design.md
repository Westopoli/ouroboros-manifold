# World View Disclosure System — Design Doc

> **Type:** Active design doc (transient, per `design_rules.md`)
> **Topic:** Faction territory visualization and zoom-driven disclosure for the world view.
> **Started:** 2026-04-21
> **Scope:** The macro-layer visual and interaction system for the world view between missions — specifically how faction territory, borders, and local detail are presented across camera distances and player intents.
>
> **Supersedes (when captured):** The "projected Voronoi influence field" paragraph in `docs/bible_history/bible_2_00_world.md` (lines 399–403) and the associated metaball/plane implementation in `world_view_structure.gd` (`_setup_territory_metaball`, the SubViewport + plane + `territory_voronoi.gdshader` pipeline, and the flat-plane "territory_plane" MeshInstance3D). Design intent ("colored regions with clearly defined borders," "territory being nibbled away," "color blooming into neutral space") is preserved and strengthened. Implementation technique changes from 2D plane projection to 3D constellation + shell hybrid with plateau-and-edge zoom disclosure.
>
> **Bible reconciliation:** The bible is append-only. When decisions in this doc are captured, the Voronoi paragraph gets an explicit "supersedes" note pointing to the new sections — not silently rewritten. Existing algorithmic insights (metaball field math, faction gap margin) survive into the new 3D shell implementation.

---

## Handoff Note (latest)

**Session 1 — 2026-04-21.** Locked the core territory metaphor, the zoom disclosure mechanism, and the Regional plateau look. Three design questions fully resolved. Open questions: Overview plateau look (Q2.5b), Local plateau look (Q2.5c), then hover/focus interactions (Q3), then time-jump animation dynamics (Q4). Estimated 3–5 more sessions to complete all remaining questions and capture to the bible + stage spec.

**Next chat should start with:** Reading this doc, confirming understanding of resolved decisions, and presenting Q2.5b (Overview plateau look).

---

## Resolved Decisions

### Q1 — Core Territory Metaphor [ANSWERED — not yet CAPTURED]

**Decision:** Constellation + shell hybrid. Both visual layers are always present in the world view. Neither is a "mode" that activates and deactivates — both exist at all times, with relative prominence modulated by zoom band (Q2) and hover/focus (Q3).

**The two layers:**

1. **Constellation (skeleton).** Bright faction-colored luminous filaments connecting every pair of adjacent same-faction systems. Derived from the existing connection graph in `WorldViewData` (border and trade edge types). Rendered as 3D curves/arcs between system nodes in the galactic volume, not as lines on a plane. Expresses topology — adjacency, supply routes, chokepoints, faction shape.

2. **Shell (skin).** A thin translucent 3D membrane wrapping each faction's influence volume. Same-faction systems share one continuous shell, computed as a 3D metaball isosurface (the 2D metaball math from the current `territory_voronoi.gdshader` generalizes to 3D). Rival shells maintain a visible gap (margin-of-victory style, matching the current shader's `gap_margin`). Expresses influence — sphere of influence, relative faction size and weight, the feeling of territory as a region of space.

**Rejected alternatives:**
- A (keep flat Voronoi plane + camera tilt fade) — 2D was ruled out by Westley.
- B (shell-only) — expresses area but not interaction; weaker on topology; occlusion-heavy.
- D (constellation + particle coherence) — poetic but prototype-risky and would need constellation to do legibility work anyway; flagged as a future aesthetic experiment if shell implementation proves unsatisfying.

**What this supersedes in the existing implementation:**
- `world_view_structure.gd:_setup_territory_metaball()` — the flat plane + SubViewport + Voronoi shader pipeline is replaced by a 3D constellation renderer and a 3D shell renderer.
- `territory_voronoi.gdshader` — the algorithmic core (metaball field summation, rival-faction gap margin, threshold isoline) survives into the new 3D shell shader. The 2D fragment shader is replaced by a 3D volumetric shader or a raymarched shell shader.
- The 2D plane MeshInstance3D (`_territory_plane`) is removed. The 3D shell is directly rendered into the world view scene.

**What stays:**
- System node rendering (emissive white sphere + colored halo shell in `_on_region_added`) — unchanged. These are the anchors the constellation and territory shell both layer onto.
- Connection data model in `WorldViewData` — unchanged. The constellation reads from the same connection data; border/trade distinction (C1 from the amendment) still applies as a filament visual.
- Conflict flashes (`_on_flash_conflict_requested`) — unchanged. They layer on top of the constellation and shells.

---

### Q2 — Zoom Disclosure Mechanism [ANSWERED — not yet CAPTURED]

**Decision:** Three-band plateau-and-edge disclosure ladder. The camera distance axis is divided into three bands (Overview / Regional / Local), each with a stable plateau interior where visual properties are locked, separated by edge blend zones where properties interpolate continuously.

**The three bands:**

- **Overview** — "Who controls what?" Player is surveying the whole world.
- **Regional** — "How do the factions interact?" Player is reading relationships, borders, topology. The default band; where the player spends most of their time during time-jump narration.
- **Local** — "What's happening at this system?" Player has pushed in on a specific region.

**The plateau-and-edge structure:**

```
 ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
 │  OVERVIEW   │ ↔ │  REGIONAL   │ ↔ │    LOCAL    │
 │   plateau   │   │   plateau   │   │   plateau   │
 └─────────────┘   └─────────────┘   └─────────────┘
         ↑blend zone↑       ↑blend zone↑
```

Inside a plateau, the visual is stable — the player can zoom in and out freely within the plateau range without triggering any visual shift. A "decent amount of zoom" happens within each band before the visual starts to change. Only when the camera crosses into a blend zone at the edge of a band does interpolation toward the adjacent band begin. Once fully across the blend zone, the visual locks to the next band's plateau. The transition is continuous, but *only at the borders between bands* — not a smooth gradient across the entire distance range. This is the key distinction from pure continuous modulation: each band is a stable "place," not a momentary sample on a curve.

**Why this over pure continuous modulation:**
- Player intent is stable inside a plateau — pan-and-zoom exploration within a band doesn't shift the visual under the player's feet.
- Art direction has three real target states to tune against, not three points on a blurry curve.
- The "no training" principle is preserved — transitions are still continuous at the edges, no gear-shift pop — but the bands feel like places rather than moments.
- Hover/focus interactions (Q3) get clean anchor states to react against.

**Tunable parameters:**
- Plateau interior range per band (where the visual is locked to the band's target state).
- Blend zone boundaries (where interpolation toward the adjacent band begins and where it completes).

**Preliminary distance sketch (numeric tuning-stage values, to be refined during playtest):**
- Overview plateau: dist ≥ ~75
- Overview → Regional blend: ~65 ≤ dist < ~75
- Regional plateau: ~40 ≤ dist < ~65 (widest plateau — default band)
- Regional → Local blend: ~25 ≤ dist < ~40
- Local plateau: dist < ~25

Plateau widths are deliberately unequal. Regional is the widest because the player spends the most time there (time-jump narration). Overview and Local are narrower because they're more specific-purpose.

**Rejected alternatives:**
- A (three-band, discrete switch with interpolation) — the gear-shift pop at band edges would be perceptible.
- B (two-band Strategic / Focused) — Strategic band would inherit the same information-overload problem this system exists to solve.
- C (continuous modulation, no bands) — no clear design targets to tune against; muddy middle zoom; hover/focus has no anchor states.

---

### Q2.5a — Regional Plateau Look [ANSWERED — not yet CAPTURED]

**Decision:** Constellation-dominant, shells subordinate, rival-shell border glow as the sharp accent.

At the Regional plateau, the visual hierarchy from most prominent to least is:

1. **Border glows** where rival faction shells meet or nearly meet — sharp bright luminous seams. This is the Regional plateau's signature effect; no other band has it at this intensity.
2. **Constellation filaments** — saturated faction-colored arcs connecting same-faction adjacent systems. Bright core, soft bloom halo, subtle slow pulse traveling along their length to suggest information flow. This is the primary read at Regional.
3. **System nodes** — bright points where filaments meet. Anchors, not subjects.
4. **Faction shells** — quiet tinted envelopes around each faction's system cluster. Very low opacity (roughly 8–15% — tuning value, to be refined). Soft gradient falloff at edges. Galaxy particles visible through them. Present but deeply subordinate; readable if the player looks for them, not competing for attention.
5. **Galaxy particles** — backdrop, always fully visible.

**Overall impression at Regional plateau:** four glowing webs of light, each a different color, where they touch each other they're sparking brightly. Topology is the primary information, influence area is the secondary information, border contestation is the focal accent.

**Visual characteristics (design intent, not tuning values):**
- Constellation filaments are gentle curves (not straight lines) that arc slightly through 3D space, so overlapping filaments between different systems don't visually collide.
- Constellation has a saturated core + soft bloom halo, with a slow traveling shimmer suggesting supply/information flow.
- **Border vs. trade filament distinction** (carries forward from Stage 11 amendment C1): `border` and `both` connections render as solid bright filaments; `trade` connections render as thinner, dimmer, or dashed filaments. The distinction is most readable at Regional where the constellation is dominant.
- Shells are atmospheric haze — present, shapes understanding of ownership, but does not assert.
- Border glow at rival-shell contact surfaces is a brighter, warmer glow band peaking exactly at the contact plane and falling off quickly on either side. When factions are not adjacent, no glow — just the soft dark gap between their shells.

**Rejected alternatives:**
- B (shell-dominant) — occlusion problem with 4+ faction shells at orbital camera angle; topology hard to extract.
- C (balanced both-at-full) — highest tuning risk; very likely to mud out with 8 factions; border glow tiebreaker has to be perfectly tuned.
- D (shells hover-activated only at Regional) — violates "both layers always present" from Q1 and requires player to learn the hover reveal.

**Migration path:** If playtesting shows Regional feels too sparse, shell opacity is a tuning value — can be turned up toward C's balance without redesigning. Moving in the opposite direction (from C back toward A) is a harder redesign, so A is the safer starting point.

---

## Open Questions

### Q2.5b — Overview Plateau Look [OPEN]

**What this question resolves:** What does the visual look like when the player is far out, surveying the whole world? The dominant player question at Overview is "who controls what?" — an area question, which suggests shells should lead. But the contrast with Regional (which is constellation-dominant) and Local (whatever we land on) matters for the ladder's coherence.

Candidate directions to explore:
- Shell-dominant with constellation simplified to faint glow (area-first, contrast with Regional's topology-first).
- Shells visible with faction sigils/names floating at each shell's center of mass.
- Whether border glow at rival-shell contacts stays strong at Overview or is unique to Regional.

**Blocking:** Not blocking, but natural next step.

### Q2.5c — Local Plateau Look [OPEN]

**What this question resolves:** What does the visual look like when the player has pushed in on a specific region? The dominant player question is "what's happening at this system?" The visual should foreground the focal system and its immediate context, demote global information.

Candidate directions to explore:
- Which "focal system" is chosen — nearest to camera? Geometric center of frame? A system the player is actively hovering?
- Whether distant factions fade out entirely or just recede.
- Whether labels/icons appear at Local or are hover-activated.
- How Local interacts with mission briefing / region selection (Local is likely the state the player enters before a mission).

**Blocking:** Not blocking.

### Q3 — Hover and Focus Interactions [OPEN]

**What this question resolves:** What does hovering (and clicking) do? The Q2 ladder gives us zoom-driven disclosure; Q3 adds intent-driven disclosure layered on top.

Candidate directions:
- Hover a system → highlights that system's constellation connections, dims other factions.
- Hover a faction shell → brings up that faction's name/sigil/stats, may dim others.
- Hover a border glow → shows what two factions are in contact and any active conflict.
- Click a system → center camera, zoom to Local band.
- Interactions that should work identically across all three plateaus versus interactions that only make sense in specific bands.

**Blocking:** Depends on Q2.5b and Q2.5c being resolved (hover anchors against plateau states).

### Q4 — Time-Jump Animation Dynamics [OPEN]

**What this question resolves:** How does territory animate during time jumps? The player watches history happen — territory shifts, flashes pulse, the scroll prints. The question is how territorial change (expansion, conquest, revolt, fragmentation) reads visually without overwhelming the scroll's narration.

Candidate directions:
- Keyframe-driven morphing of shells (current approach via `time_jump_keyframe` signal).
- Choreographed emphasis — the shell or constellation segment involved in the event brightens during that event's chronicle entry.
- How quickly shells morph vs. constellation updates (instant, tweened, quantized to keyframes).
- Whether event-specific visual treatments exist (conquest nibbles shell color, revolt fragments a shell, expansion blooms into neutral space).

**Blocking:** Depends on Q2.5b, Q2.5c, Q3.

---

## Known Tuning Values (deferred to implementation)

These are values we'll need to land concrete numbers for, but they're tuning-stage decisions informed by playtest — not design decisions for brainstorming:

- Plateau distance thresholds (rough sketch in Q2 above).
- Shell opacity at each plateau (Regional sketched at 8–15%).
- Constellation filament core width and halo width, per plateau.
- Constellation pulse/shimmer travel speed and intensity.
- Border glow width, intensity, and falloff distance.
- Shell gradient falloff distance (carries over from current shader's metaball math).
- Rival-shell gap margin (carries over from current shader's `gap_margin = 0.30`).

---

## Engineering Decisions (Claude defaults)

To be decided when moving to stage spec authoring, not in this design doc:

- Shell rendering technique: 3D volumetric metaball shader vs. raymarched isosurface vs. marching-cubes-generated mesh vs. billboarded sprite stack. Performance vs. visual quality tradeoff at 8 factions × 20–30 systems.
- Constellation filament rendering: `ImmediateMesh` lines with shader-bloom vs. tube meshes with emissive material vs. particle-system strands.
- How plateau-and-edge interpolation is driven: per-property curves in a Resource, uniform blend factor, or band-state objects with lerp methods.
- Where the territory rendering lives in the existing `WorldViewStructure` / component architecture. The amendment established `SettledReachRenderer` as the per-era class; the new constellation + shell work lands inside it.

---

## Bible Capture Plan

When this design doc's resolved questions are ready for capture, the bible updates are:

**`docs/bible_history/bible_2_00_world.md`:**
- "Galaxy View" section (lines 393–417 area): Add a new subsection titled "Territory Visualization — Constellation and Shell Hybrid" that documents Q1's decision. Mark the existing "projected Voronoi influence field" paragraph (lines 399–403) with an explicit "superseded by [new section]" note — do not delete or rewrite. The append-only rule requires the old text stays in place with a forward-reference.
- Add a new subsection titled "Zoom Disclosure — Plateau-and-Edge Ladder" documenting Q2.
- Each Q2.5 sub-decision (Regional, Overview, Local plateau looks) gets a subsection within or adjacent to the zoom disclosure section.

**`game_bible.md` hub:**
- If any open question in the hub's "Open Design Questions" section corresponds to a resolved question here, remove it from the open list and ensure the resolution is reflected in the spoke.

**`stage_11_amendment.md`:**
- Checkpoint C currently contains C1 (border vs. trade connection distinction), C2 (border contour SubViewport pass), C3 (camera `move_to_position`). C2 is now superseded by this design work. The amendment needs an update acknowledging that the 2D territory plane is being replaced by 3D constellation + shell, and the existing C2 work is archived. New stage spec content captures the implementation plan for the 3D system — this is not yet authored; it follows once Q2.5b, Q2.5c, Q3, Q4 are resolved.

**`world_view_structure.gd`:**
- No code changes during the design phase. Implementation changes only once all design questions are resolved and stage spec authoring begins.

---

## Session Log

**Session 1 — 2026-04-21.** Opened with context gathering (read `docs/bible_history/bible_2_00_world.md`, `game_bible.md`, `amendment_world_view_architecture.md`, `stage_11_amendment.md`, `stage_11_c3c4_territory_redesign.md`, `cc_paste_metaball_territory.md`, `world_view_structure.gd`, `territory_voronoi.gdshader`, current implementation screenshot). Established that current impl uses 2D metaball plane diverging from bible's Voronoi spec — both superseded by this design work. Resolved Q1 (core metaphor — constellation + shell hybrid), Q2 (zoom disclosure — three-band plateau-and-edge), Q2.5a (Regional plateau look — constellation-dominant with shells subordinate and border glow as accent). Open: Q2.5b, Q2.5c, Q3, Q4.
