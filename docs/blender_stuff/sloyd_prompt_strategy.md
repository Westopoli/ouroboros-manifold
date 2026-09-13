# Sloyd Prompt Strategy — Ouroboros Manifold

> **Purpose:** This document defines the workflow for producing 3D models for Ouroboros Manifold using Sloyd (unlimited generation, mesh export). It replaces the 3D-Agent prompt strategy. Share this alongside the relevant bible spoke files when starting a new session.
>
> **Tool:** Sloyd (web-based, unlimited generation, exports GLB/FBX/OBJ)
>
> **Key difference from 3D-Agent:** Prompts are free. Keep them short and focused — one clear object per prompt. Iteration happens in the tool, not in conversation.

---

## Context for New Chat Sessions

When starting a new session for prompt work, provide:

1. This strategy document
2. `docs/bible_history/bible_2_00_combat.md` (unit descriptions, abilities, roles)
3. `docs/bible_history/bible_2_00_world.md` (tier visual language, sci-fi era creative direction, unit visual designs)
4. `3d_model_outline_all_eras.md` (cross-era unit mapping and silhouette reference)

---

## Prompt Philosophy

Sloyd works best with **short, plain-English descriptions of a single object.** Don't describe construction logic, Blender operations, or poly-level detail. Describe what the thing *is* and what it *looks like.*

**Good Sloyd prompt:** "Low-poly angular spaceship, flat manta ray shape, blocky hull panels, two rear engine prongs, no windows"

**Bad Sloyd prompt:** "Create a flattened kite-shaped mesh using mirror modifier, extrude rear faces into two prongs, bevel the leading edge at 15 degrees, target 400 polygons..."

### Prompt Guidelines

- **One object per prompt.** Don't ask for a scene or multiple models.
- **Lead with the object type** ("spaceship," "trebuchet," "war canoe") so Sloyd knows what category it's working in.
- **Include the art style** ("low-poly," "flat-shaded," "geometric") in every prompt.
- **State key shape features** — the 2–3 things that make this object recognizable.
- **Use negative constraints sparingly** — only when Sloyd is likely to add something unwanted (e.g., "no windows" for spaceships).
- **Don't describe materials, colors, or glow.** Those are applied in Blender post-export.

---

## Workflow

### Per-Asset Loop

1. **Fire the prompt** from the sheet below
2. **Evaluate the result** — does the silhouette read correctly? Is it distinct from roster siblings?
3. **If not right:** tweak the prompt and re-fire (free, no cost)
4. **If close enough:** export the mesh (GLB preferred)
5. **Blender cleanup** (see Post-Export Workflow below)

### Batch Strategy

With unlimited generation, you can fire all prompts for a tier in one session, review them side by side, and iterate on the ones that missed. No need to serialize — work in parallel.

---

## Production Sequence

Same rationale as before: T2 establishes the baseline, T1 pushes rougher, T3 pushes smoother.

**Phase 1 — Tier 2 units:** Vanguard → Bombard → Bastion → Raider → Interceptor → Warden
**Phase 2 — Tier 1 units:** Same order, T2 results as visual reference
**Phase 3 — Tier 3 units:** Same order, T2 results as visual reference
**Phase 4 — Structures:** Stations → Military Installations → Resource Nodes
**Phase 5 — Environment:** Asteroids → Derelicts → Cargo → Beacons → Pylons → Nebula volumes

---

## Post-Export Blender Workflow

After accepting a Sloyd export:

1. **Import GLB** into Blender
2. **Poly check** — if wildly over budget, decimate. If way under, the silhouette may be too simple.
3. **Topology cleanup** — Edit Mode → Select All → Mesh → Clean Up → Delete Loose. Check for non-manifold edges.
4. **Create `faction_color` face group** — select hull panel faces, create vertex group, assign.
5. **Apply tier materials** — use the hex/metallic/roughness/emission values from `docs/bible_history/bible_2_00_ai_pipeline.md`.
6. **Silhouette check** — zoom way out. Can you identify the unit type? Is it distinct from siblings?
7. **Origin and orientation** — Set Origin → Center of Mass. Apply all transforms (Ctrl+A).
8. **Save .blend** to `blender/settled-reach/[category]/[asset]_t[tier].blend`
9. **Export GLB** to `godot/assets/settled-reach/[category]/[asset]_t[tier].glb`

---

## Poly Budget Reference

| Category | T1 | T2 | T3 |
|----------|-----|-----|-----|
| Raider | 200 | 200 | 250 |
| Interceptor | 200 | 200 | 250 |
| Vanguard | 400 | 400 | 450 |
| Warden | 200 | 200 | 250 |
| Bombard | 450 | 450 | 450 |
| Bastion | 500 | 500 | 500 |
| Station | 600 | 600 | 500 |
| Military Installation | 500 | 500 | 400 |
| Resource Node | 300 | 300 | 200 |
| Asteroids | 100–150 | — | — |
| Derelict/Cargo/Beacon | 50–200 | — | — |

---

## Settled Reach — Sloyd Prompt Sheet

### Design Override Note

The Vanguard uses the "Manta" design (wide flat manta ray silhouette) across all three tiers. This overrides the bible's original wedge/slab description. See the Completed Prompt Archive below for the full rationale. All other units follow docs/bible_history/bible_2_00_world.md descriptions.

---

### Tier 2 — Establishment (smooth, integrated, polished)

| # | Asset | Prompt | Look For |
|---|-------|--------|----------|
| 1 | Vanguard T2 | Low-poly spaceship, flat manta ray shape, smooth contoured hull, blunt angled front edge, two rear tail prongs with cylindrical thruster nacelles, no windows, no superstructure, flat-shaded geometric | Wide kite shape from above, thin profile from side, clean bilateral symmetry, twin rear prongs with negative space between them |
| 2 | Bombard T2 | Low-poly long artillery spaceship, elongated hull built around a central-axis weapon running the full length, sleek tapered form, rear engine block, no turrets, flat-shaded geometric | Longest silhouette in the roster, weapon axis dominates, clearly different proportions from Vanguard |
| 3 | Bastion T2 | Low-poly compact heavy armored spaceship, wider than long, dense contoured hull with integrated armor plating, multiple weapon mounts covering all angles, squat and massive, flat-shaded geometric | Widest and most compact shape, reads as dense and immovable, clearly heavier than Vanguard |
| 4 | Raider T2 | Low-poly small sleek fighter spacecraft, narrow dart shape swept back, integrated flush weapon mounts on nose, unified smooth hull, single engine glow point at rear, flat-shaded geometric | Smallest model, narrow and fast-reading, clearly distinct from the wide Vanguard and Interceptor |
| 5 | Interceptor T2 | Low-poly small patrol spacecraft, broad flat body wider than the Raider, integrated sensor hull surface, stubby wings with flush weapons, guardian stance silhouette, flat-shaded geometric | Wider than Raider but still small (squad unit), reads as "coverage" not "attack," distinct from Vanguard's much larger manta |
| 6 | Warden T2 | Low-poly support spaceship, radial symmetry, concentric emitter rings around the hull, vertical profile taller than wide, broadcast antenna geometry, slightly smaller than Vanguard, flat-shaded geometric | Radial/vertical emphasis clearly different from Vanguard's horizontal, reads as "projects influence outward" |

### Tier 1 — Frontier (boxy, seamed, matte, bolted-together)

| # | Asset | Prompt | Look For |
|---|-------|--------|----------|
| 7 | Vanguard T1 | Low-poly angular spaceship, flat manta ray shape, blocky faceted hull panels with visible seam ridges, blunt sharp-edged front, two rear prongs with boxy crude thruster housings, asymmetric sensor block on one wing, no windows, flat-shaded geometric | Same manta planform as T2 but rougher — faceted panels, hard edges, asymmetric detail. Reads as "armed cargo hauler" |
| 8 | Bombard T1 | Low-poly long crude artillery spaceship, oversized exposed cannon barrel dominating the hull, visible structural bracing along weapon axis, rear engine block with exposed pipes, bolted-together industrial look, flat-shaded geometric | Hull built around a gun — weapon is the biggest component. Cruder and more exposed than T2 |
| 9 | Bastion T1 | Low-poly squat heavily-armored block spaceship, thick faceted armor plates, wider than long, visible redundant systems and backup sensors, angular deflection surfaces, crude and industrial, flat-shaded geometric | Thickest visible armor in the roster, squat block shape, reads as "survive through redundancy" |
| 10 | Raider T1 | Low-poly small angular fighter spacecraft, narrow dart shape, oversized thruster cans at the rear, visible bolted-on weapon hardpoints on nose, exposed sensor dish, crude and fast-looking, flat-shaded geometric | Same narrow dart as T2 but rougher — big visible thrusters, bolted-on weapons. "Weaponized shuttle" |
| 11 | Interceptor T1 | Low-poly small broad patrol spacecraft, wide flat body, prominent visible sensor array hardware on top, stubby weapon mounts on wing flanks, built to loiter and scan, crude industrial look, flat-shaded geometric | Wide scan profile, sensor hardware is the dominant feature, "patrol boat" feel |
| 12 | Warden T1 | Low-poly support spaceship, prominent dorsal antenna array or repair bay on top, practical understated hull, visible drone bays or mechanical repair arms, vertical central structure, flat-shaded geometric | Support hardware (antenna/repair bay) is the most visible feature, "field hospital meets comms relay" |

### Tier 3 — Zenith (flowing, luminous, abstract)

| # | Asset | Prompt | Look For |
|---|-------|--------|----------|
| 13 | Vanguard T3 | Low-poly organic spaceship, flat manta ray shape, paper-thin edges thickening at center, smooth continuous curves with no visible seams, rear prongs merge smoothly into hull, minimal surface detail, flat-shaded geometric | Same manta but abstracted — thinner, smoother, fewer distinct features. Elegant and dense-feeling |
| 14 | Bombard T3 | Low-poly smooth tapered spaceship, elongated organic form with no visible barrel or weapon, entire hull is one flowing weapon shape, minimal surface detail, sleek and abstract, flat-shaded geometric | No visible gun — the whole ship IS the weapon. Smooth taper, beautiful and unsettling |
| 15 | Bastion T3 | Low-poly dense compact polyhedron spaceship, smooth heavy geometric form, wider than long, minimal detail suggesting impossible density, subtle faceted surfaces, abstract and massive, flat-shaded geometric | Geometric polyhedron, dense and heavy-reading, "made of something that shouldn't exist" |
| 16 | Raider T3 | Low-poly razor-thin blade spacecraft, narrow elongated form, knife-edge profile, energy-suggesting lines along leading edges, minimal geometry, abstract and fast, flat-shaded geometric | Blade-like, almost 2D thin, reads as pure speed. "Surge is a streak of light" |
| 17 | Interceptor T3 | Low-poly broad disc spacecraft, almost manta-ray profile, smooth wide form suggesting a detection field beyond the hull, minimal detail, abstract sensor platform, flat-shaded geometric | Broad disc/manta that reads as "the whole surface is a sensor." Must stay clearly smaller than Vanguard |
| 18 | Warden T3 | Low-poly abstract projection platform spaceship, hull secondary to implied energy field, minimal smooth form with radial geometry suggesting outward influence, ethereal and minimal, flat-shaded geometric | Less a ship, more a contained phenomenon. The most visually unique T3 unit |

### Structures

| # | Asset | Prompt | Look For |
|---|-------|--------|----------|
| 19 | Station T2 | Low-poly space station, modular ring sections with docking arms, cylindrical central hub, antenna arrays, integrated design, flat-shaded geometric | Reads as a proper designed facility, distinct from military installations |
| 20 | Station T1 | Low-poly crude space station, mismatched modular sections bolted together, exposed framework, industrial and improvised, flat-shaded geometric | Assembled not manufactured, visible joints and mismatched parts |
| 21 | Station T3 | Low-poly monolithic space station, smooth flowing form, minimal surface detail, single unified structure, abstract and elegant, flat-shaded geometric | One continuous form, no visible modularity |
| 22 | Military Installation T2 | Low-poly military space platform, weapon turrets on a compact armored base, sensor domes, angular defensive geometry, flat-shaded geometric | Clearly military — weapons and armor visible, distinct from civilian station |
| 23 | Military Installation T1 | Low-poly crude military space platform, exposed gun emplacements on a rough welded base, bolted armor plates, industrial, flat-shaded geometric | Rougher version of T2, guns bolted on rather than integrated |
| 24 | Military Installation T3 | Low-poly abstract military platform, smooth compact form with no visible weapons, implied threat through dense geometry, minimal and sleek, flat-shaded geometric | Weapons invisible, the platform itself is the threat |
| 25 | Resource Node T2 | Low-poly mining space platform, extraction arm or drill extending from a small industrial base, storage containers, processing equipment, flat-shaded geometric | Functional industrial, clearly about extraction not combat |
| 26 | Resource Node T1 | Low-poly crude mining rig in space, exposed drilling equipment, scaffold framework, rough industrial look, flat-shaded geometric | Improvised mining operation, barely held together |
| 27 | Resource Node T3 | Low-poly sleek extraction platform, smooth minimal form, abstract resource collection geometry, elegant and efficient, flat-shaded geometric | Clean and abstract, extraction process is invisible |

### Environment (Universal — no tier variation)

| # | Asset | Prompt | Look For |
|---|-------|--------|----------|
| 28 | Asteroid (small) | Low-poly small space asteroid, irregular rocky shape, angular facets, compact, flat-shaded geometric | Simple rocky form, ~100 polys |
| 29 | Asteroid (medium) | Low-poly medium space asteroid, irregular rocky shape with crater indentations, angular facets, flat-shaded geometric | Slightly more complex, still reads as rock |
| 30 | Asteroid (large cluster) | Low-poly large asteroid cluster, 2–3 connected rocky masses, irregular angular shapes, flat-shaded geometric | Multiple connected forms, largest asteroid variant |
| 31 | Derelict Hull | Low-poly destroyed spaceship hull fragment, broken and hollow, torn metal edges, drifting wreck, flat-shaded geometric | Clearly a dead ship — broken, hollow, not a functioning vessel |
| 32 | Cargo Container | Low-poly space cargo container, simple rectangular box with panel lines, utilitarian, flat-shaded geometric | Clean box, recognizable as cargo, very low poly |
| 33 | Shield Pylon | Low-poly energy pylon, tall narrow vertical structure with a geometric emitter at the top, simple base, flat-shaded geometric | Vertical, clearly a device not a building |
| 34 | Navigation Beacon | Low-poly space navigation beacon, small antenna on a compact base, signal dish or light, minimal, flat-shaded geometric | Smallest structure, reads as "signal point" |
| 35 | Nebula Volume | Low-poly abstract cloud volume, soft irregular rounded shape, translucent-feeling geometry, flat-shaded | Organic cloud form, distinct from hard-edged assets |

---

## Completed Prompt Archive

### Vanguard — "The Manta" (Design Override)

**Design origin:** Developed in the T2 prompt engineering session. Overrides the bible's original wedge/slab Vanguard description for the Settled Reach era.

**Shape identity:** Wide, flat manta ray silhouette. Flattened kite planform from above, wider toward the front with a blunt leading edge. Length 1.5x width, height 0.15x length. Rear splits into two angled prongs like manta tail fins with thruster nacelles. No dorsal superstructure.

**Why the manta:** The Vanguard's role is durable frontliner that holds the line. The manta silhouette communicates coverage and immovable presence. Brace (plant and become immobile with damage reduction) reads naturally — a broad flat shape planting itself as a barrier.

**Key decisions:**
- Kite planform, not diamond — wider toward the front so the leading edge dominates
- Beveled grooves instead of visible weapons — prevents "WW2 battleship with turrets" failure mode
- Twin rear prongs — creates distinctive negative space, evokes manta tail fins, unique rear silhouette
- Length 1.5x width (not wider-than-long) — more imposing capital ship proportions

**Cross-roster distinctiveness:**
- vs Raider: small narrow dart — nothing like the Manta's breadth
- vs Interceptor: flat and wide but much smaller, disc/patrol profile — **closest sibling, keep size difference prominent**
- vs Warden: radial/vertical projection — opposite axis emphasis
- vs Bombard: longest, narrowest — opposite proportions
- vs Bastion: compact and thick/cubic — Manta is wide but thin, Bastion is wide but heavy

**Tier progression:**
- T1: Same planform, angular and rough. Faceted panels, visible seams, asymmetric sensor cluster on one wing, crude box thrusters. "Armored platform someone welded together and armed."
- T2: Smooth and contoured. The baseline design.
- T3: Almost abstract. Paper-thin edges, continuous curves, prongs merge into hull, minimal features. "The ship merges with space."
