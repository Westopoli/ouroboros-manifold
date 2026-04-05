# Ouroboros Manifold — AI Integration Pillar Reference

> **Extracted from game_bible.md v1.23.** This file is authoritative for the library pipeline,
> dynamic naming system, and asset pipeline. If this file conflicts with game_bible.md,
> flag it for Westley — do not silently resolve the conflict.
>
> **Modification rule:** Same as the master bible — append-only unless Westley approves
> deletion. Resolved open questions get written here AND reflected back to the hub.

---

## AI Integration Pillar

AI is a core differentiator for this game, not an add-on. AI integration points:

- **Library builder pipeline** — generates chronicle templates, mission archetypes, briefing content, complication templates, and event narratives offline. Pre-generated, stored in JSON, read at runtime. No runtime API calls during play.
- **Dynamic naming system** — generates names for everything in the game across four categories: people (commanders, faction leaders, regional commanders, lineage members), places (regions, systems, landmarks), units (individual named assets, task forces, squad designations), and factions (civilization names, breakaway faction names, external faction names). Draws from a vast cultural range (historical human naming conventions, Tolkien-esque construction, ancient Greek, Sumerian, invented linguistic roots, and beyond). See "Dynamic Naming System" section below for full design.
- **Unit stat tuning** — AI generates per-civilization stat profiles for unit classes within hand-designed mechanical constraints.
- **Unit power balancing** — AI-generated units are scored with strength values. The force parity system uses these scores to ensure missions present winnable fights: the player receives forces with comparable total strength to the enemy, adjusted by civilizational capacity and difficulty setting.
- **Mission variable filling** — AI helps generate the specific narrative context for mission briefs within archetype templates.
- **Chronicle generation** — AI-authored templates produce emergent narrative that reads like real history.
- **Chronicle scroll distillation** — AI-generated templates for compressing hundreds of time-jump events into 5–10 scroll entries.
- **Potential future** — AI-generated antagonist archetype variants, civilization personality profiles, faction flavor, additional mission archetypes.

The principle: **AI generates content within mechanical frameworks.** The engine defines the constraints. AI fills in the specifics. The engine can handle any output because the constraints guarantee validity.

### Automated Balance Testing via Self-Play

With 6 unit types, multiple tech tiers, and AI-generated stat variation, manual balance testing is impractical. The plan is an automated balance testing pipeline that runs headless simulated combat to detect gross imbalances and degenerate strategies.

**Phase 1 (earliest, pre-launch viable):** Scripted heuristic bots play the tactical layer in headless mode (pure Python, no Godot). Simple strategies ("move Strike toward nearest Siege, keep Bombard at max range"). Bots don't need to be good — they need to be consistent enough to reveal gross imbalances. Run thousands of engagements per hour across force compositions and tech tier matchups. Output: composition-vs-composition win rate matrix. Matchups outside a target band are flagged automatically.

**Phase 2 (post-launch):** Self-play reinforcement learning (PPO or AlphaZero-style MCTS) on the reduced tactical state. Networks discover emergent strategies that scripted bots miss. When a network finds a degenerate strategy (e.g., always rush with 6 Raiders wins), that's a balance flag.

**Phase 3 (ongoing):** Automated tournament brackets as a continuous integration tool. Every stat change triggers a rerun. The tactical layer's state space is small enough for CPU-based training.

This is a **post-tactical-layer tool** — prerequisites are a working tactical layer, stable unit stats, and representative map generation. Implementation is far future. Noted here so the design is not lost and so the tactical layer's architecture does not make headless simulation impossible.

### 3D Asset Pipeline — AI-Assisted Modeling with Human Cleanup

The game's low-poly, Art of Rally visual style is a deliberate design choice that also creates a significant production advantage: low-poly assets (200–500 polygons per model, flat or minimal shading, clean geometric forms) are dramatically easier to produce at scale than photorealistic models. This section defines the asset pipeline for producing the 3D models that populate each era — units, environment objects, and structures — at a cost and pace that supports the expansion pack business model.

**Pipeline philosophy: AI generates 70%, humans finish 30%.** Current AI 3D model generation tools (as of early 2026) produce base meshes that are usable starting points but not production-ready without cleanup. The low-poly art style minimizes the gap between AI output and final asset quality — a rough AI-generated shape needs less refinement to become a clean low-poly model than it would to become a detailed realistic one. The pipeline leverages this by using AI tools for rapid base mesh generation and Blender for standardization, cleanup, and visual consistency enforcement.

**Target asset counts per era pack.** Each era requires approximately 18 unique unit models (6 unit types × 3 tech tiers, following the cross-era silhouette archetypes), 3–6 tiered point-of-interest structure models (1–2 structure types × 3 tiers), and one universal set of 5–10 environment object types (obstacles, cover, hazard visuals, environmental fill — no tier variants). Total per era: roughly 25–35 unique 3D assets, all low-poly. See "Sci-Fi Era — The Settled Reach" in The World section for the tier visual progression that drives per-tier asset variation.

#### Tool Recommendations

Three AI 3D generation tools are viable for this pipeline, each with a different strength:

**Meshy** — the primary generation tool. Meshy offers a dedicated Low Poly Mode that produces efficient wireframes optimized for real-time engines, directly aligned with the game's art style. It has a native Godot plugin for direct scene import. Text-to-3D and image-to-3D modes are both available — image-to-3D produces more consistent results when fed concept art or reference sketches. Exports to GLB, OBJ, FBX, and BLEND. Pricing: free tier with 100 monthly credits; Pro at ~$20/month with 1,000 credits (~50 model generations per month, more than sufficient for a full era pack in a single billing cycle). Meshy is the fastest path from prompt to base mesh.

**3D-Agent** — the best option for Blender-integrated generation. 3D-Agent is a Blender plugin that generates models directly inside Blender using Blender's native modeling tools via Claude MCP integration. The critical advantage over web-based generators is topology quality: it produces clean quad-based wireframes rather than triangle soup, which makes post-generation cleanup significantly faster. Models appear directly in the Blender scene — no export/import cycle. Pricing: free tier at 15 prompts/month, paid tiers at $10–30/month. Best used for hero assets or models where topology quality matters most (units that need clean silhouettes at tactical zoom distance).

**Tripo** — the budget option with polycount control. Tripo offers explicit polycount and mesh density controls on output, allowing precise polygon budget targets per model (e.g., 300–500 polys for the game's low-poly style). Clean quad/triangle topology control. Pricing: ~$12/month. Best used as a secondary tool when Meshy's output needs a different geometric interpretation or when precise polycount control matters.

These tool recommendations reflect the state of AI 3D generation as of early 2026. The landscape is evolving rapidly. The pipeline design is tool-agnostic — any text-to-3D or image-to-3D tool that exports to standard formats (GLB, OBJ, FBX) can substitute into this workflow. The pipeline's value is in the workflow structure, not in any specific tool dependency.

#### Per-Era Production Workflow

**Step 1: Concept art generation.** Before any 3D work, produce 2D reference images for each unit and environment type in the era's visual language. These can be hand-sketched, AI-generated (image generation tools like those in Meshy's pipeline), or sourced from reference boards. The reference image defines the target silhouette, proportions, and visual identity for the asset. For a WW2 era: "low poly Panzer heavy tank, flat shaded, isometric view." For Imperial China: "low poly junk combat unit, flat shaded, top-down angle." The reference image is the creative control point — it's where art direction happens.

**Step 2: Base mesh generation.** Feed the reference images into Meshy's image-to-3D pipeline (or text prompts into text-to-3D) with Low Poly Mode enabled. Generate 3–4 variations per asset and select the best starting shape. This step takes roughly 1–2 minutes per asset. For a full era (25–35 assets), base mesh generation is a single work session.

**Step 3: Blender cleanup and standardization.** Import the selected base meshes into Blender. This is where visual consistency is enforced across the era. The cleanup pass includes: fixing topology issues (removing degenerate faces, ensuring clean edge flow), adjusting polygon count to match the game's target poly budget, standardizing the color palette and material assignments to the era's visual identity, ensuring distinctive silhouettes at tactical camera distance (units must read clearly when small on screen), and verifying export compatibility with Godot. For low-poly models, this cleanup pass is fast — typically 20–45 minutes per asset. No fine sculpting, no complex UV unwrapping, no PBR material authoring. Just clean geometry with flat colors.

**Step 4: Export and integration.** Export cleaned assets from Blender in GLB or GLTF format (Godot's preferred 3D format). Assets are organized into the era pack's content directory structure alongside the JSON data files (naming libraries, chronicle templates, event templates, unit stat profiles). The engine's existing era-agnostic loading system consumes the 3D assets through the same abstract type mapping it uses for everything else: the theme pack maps "heavy combat unit" to the WW2 era's heavy tank model, or the Roman era's war galley model, or the sci-fi era's battlecruiser model.

#### Environment Assets

Environment objects follow the same workflow but are simpler to produce. Environment pieces don't need rigging or animation — they're static geometry. A low-poly asteroid field, a cluster of Roman columns, a bombed-out WW2 building — these are geometrically simple shapes that current AI tools handle well with minimal cleanup. The spine + gradient map system places environment objects by abstract type ("dense obstacle region," "hazard zone," "structure cluster"), and the era pack maps those abstract types to the era's visual prefabs. Each era needs 10–15 environment object types, and cleanup time per object is typically under 15 minutes.

#### Cost and Time Per Era

Estimated production cost per era pack's 3D assets: one month of Meshy Pro ($20) covers all base mesh generation credits. Blender cleanup at 30 minutes average per asset across 30 assets totals roughly 15 hours of modeling time. If self-taught in Blender (the low-poly modeling learning curve is approximately 2–3 focused weeks for someone with prior game development experience), the ongoing per-era cost is $20 in tooling plus 15 hours of labor. If outsourced to a freelance low-poly 3D artist, the cleanup pass costs roughly $20–50 per asset, or $600–1,500 per era. Either path produces a complete set of 3D assets for an era pack at a cost well within the revenue the era pack generates at a $2–3 selling price across even modest player numbers.

#### Future Pipeline Evolution — Modular Kit-Bashing

As the era catalog grows, a modular kit-bashing approach may replace or supplement the per-asset generation workflow. Instead of generating complete models per era, the pipeline would build a library of modular parts — hull shapes, turret types, propulsion modules, weapon mounts, structural details — that are recombined per era through assembly recipes defined in the theme pack JSON. A Roman-era "Line" unit might combine a galley hull module, a ram prow module, and a sail module. A WW2 "Siege" unit might combine a heavy tank chassis, a large turret, and track modules. The parts are modeled once (or AI-generated and cleaned once), then recombined per era. This approach becomes increasingly efficient at scale because each new era reuses the modular library with new combinations rather than starting from scratch, and it naturally enforces visual consistency because every unit in every era is built from the same construction grammar. The modular approach is a natural evolution once the per-asset pipeline has produced enough eras to identify which part categories are universal across eras. It is not required for the first several era packs — the per-asset Tier 1 workflow described above is sufficient and simpler to execute.

#### Sci-Fi Era Production Spec — "The Settled Reach"

> **RESOLVED (v1.20).** This section is the production reference for creating all 3D assets for the base sci-fi era. It contains polygon budgets, color palettes, material specifications per tier, the faction color system, and example generation prompts for 3D-Agent and Meshy. Designed to be used as a working reference during Blender sessions. For creative direction and visual identity, see "Sci-Fi Era — The Settled Reach" in The World section.

##### Asset Manifest

Total unique 3D models for the Settled Reach era: **~33 assets.**

**Unit models (18):** 6 unit types × 3 tiers. Primary tool: 3D-Agent (clean quad topology for hero assets). These are the highest-priority assets — on screen during every mission.

| Unit | Tier 1 | Tier 2 | Tier 3 |
|------|--------|--------|--------|
| Raider (Strike/squad) | Angular dart, bolted weapons | Sleek dart, flush mounts | Blade profile, edge-channeled energy |
| Interceptor (Strike/squad) | Flat patrol boat, visible sensors | Integrated sensor hull, refined wings | Manta-ray disc, luminous detection edges |
| Vanguard (Line/individual) | Blocky armored wedge | Contoured battlecruiser | Organic front-heavy, luminous dense hull |
| Warden (Line/individual) | Antenna/dish on practical hull | Emitter rings, broadcast geometry | Projection platform, luminous aura |
| Bombard (Siege/individual) | Hull built around oversized cannon | Integrated weapon platform | Smooth tapered form, hull-is-weapon |
| Bastion (Siege/individual) | Squat armored block, faceted plates | Contoured fortress, clean density | Geometric polyhedron, impossible density |

**Point-of-interest structures (9):** 3 types × 3 tiers. Primary tool: Meshy (image-to-3D with reference art). Viewed at more distance than units.

| Structure | Tier 1 | Tier 2 | Tier 3 |
|-----------|--------|--------|--------|
| Station (objective/staging) | Modular, bolted hab rings | Unified architecture, planned layout | Monolithic single-form, luminous accents |
| Military installation | Blocky hardened modules | Layered defensive geometry | Subtle, embedded capability |
| Resource node | Mining rig, visible pipes/tanks | Automated, clean extraction | Nearly invisible, exotic sources |

**Universal environment (6–8):** No tier variants. Primary tool: Meshy (text-to-3D). Simplest geometry, viewed at distance.

Asteroid (3 variants — small, medium, large cluster), derelict hull fragment, cargo container, shield pylon / barricade, navigation beacon, nebula volume shape (for sensor interference zones).

##### Polygon Budgets

All models target the low-poly Art of Rally aesthetic: clean geometric forms, flat or minimal shading, no fine detail.

| Asset Category | Poly Target | Notes |
|----------------|-------------|-------|
| Strike squad member (Raider, Interceptor) | 150–300 | Smallest models. 3–5 on screen simultaneously per squad. Must read as silhouette at distance. |
| Line unit (Vanguard, Warden) | 300–500 | Medium models. Individual command. More detail budget for front-facing features. |
| Siege unit (Bombard, Bastion) | 400–600 | Largest unit models. Individual high-value. Distinctive silhouettes justify the higher budget. |
| Station / military installation | 400–800 | Viewed at more distance. Detail in overall form, not surface. Tier 3 can be simpler geometry (smooth forms). |
| Resource node | 200–400 | Background importance. Functional reads. |
| Environment object | 100–300 | Ambient geometry. Asteroids can be very low-poly. Beacons are tiny. |

**Cleanup rule:** If 3D-Agent or Meshy output exceeds the poly target by more than 50%, decimate in Blender. If under by more than 30%, the silhouette is probably too simple — regenerate or add geometry by hand.

##### Faction Color Regions

Faction colors are per-civilization data assigned at runtime, not baked into models. During the Blender cleanup pass, each unit and structure model must have **designated face groups for faction color application**. These are the surfaces where the engine swaps in the owning faction's color at runtime. The remaining surfaces use the tier-specific neutral materials defined below.

The creative direction for how faction color appears changes per tier (consistent with the tier visual language): at Tier 1, faction color reads as painted-on livery over neutral metal. At Tier 2, faction color reads as integrated hull plating. At Tier 3, faction color reads as an emissive material property. The specific treatment is decided during the Blender session for each model — the key requirement is that every model has clearly separated face groups so the engine can swap faction color without re-authoring materials.

**Blender workflow:** Name the faction-color face group `faction_color` on every model. All faces in this group receive the faction's color at runtime. All other faces use the tier's neutral materials. The engine handles the color swap and any per-tier treatment (matte vs metallic vs emissive) through the shader pipeline in Godot.

##### Tier Material Specifications — Blender Reference

These are the material settings applied during the Blender cleanup pass (Step 3 of the per-era production workflow). Every unit and structure model gets materials assigned from these tier-specific specs.

**Tier 1 — "Frontier" materials:**

- *Hull primary:* Base color #6B6B6B (medium gray), metallic 0.7, roughness 0.7. The worn, unpolished metal of functional construction.
- *Hull secondary:* Base color #4A4A4A (dark gray), metallic 0.6, roughness 0.8. Structural reinforcement, internal framing visible on exterior.
- *Hazard/accent:* Base color #D4A017 (industrial yellow-orange), metallic 0.0, roughness 0.9. Safety markings, panel borders, thruster housings.
- *Faction color faces:* Assigned to `faction_color` face group. Runtime shader applies faction color as flat matte paint (metallic 0.0, roughness 0.8).
- *Engine glow:* Base color #FF8844 (warm orange), emission strength 2.0. Visible thruster output — hot, raw, obvious.
- *Viewport/sensor:* Base color #88CCFF (pale blue), emission strength 0.5. Windows, sensor panels, display screens.

**Tier 2 — "Establishment" materials:**

- *Hull primary:* Base color #C0C0C8 (polished silver), metallic 0.9, roughness 0.3. Clean manufactured surface.
- *Hull secondary:* Base color #E8E8F0 (titanium white), metallic 0.8, roughness 0.35. Accent paneling, upper surfaces.
- *Accent line:* Base color #AAAAAA (medium silver), emission strength 0.3. Subtle seam glow along hull panel boundaries — the first hint of integrated lighting.
- *Faction color faces:* Assigned to `faction_color` face group. Runtime shader applies faction color as metallic plating (metallic 0.7, roughness 0.35).
- *Engine glow:* Base color #66AAFF (cool blue-white), emission strength 3.0. Cleaner, more contained than Tier 1.
- *Weapon integration:* Base color #808088 (steel), metallic 0.9, roughness 0.2. Flush-mounted weapon surfaces — distinct from hull but not bolted-on.

**Tier 3 — "Zenith" materials:**

- *Hull primary:* Base color #1A1A2E (deep space dark), metallic 1.0, roughness 0.1. Near-black reflective surface that makes emissive elements pop.
- *Hull secondary:* Base color #2A2A3E (dark blue-black), metallic 0.9, roughness 0.15. Slight variation for surface articulation.
- *Faction emissive faces:* Assigned to `faction_color` face group. Runtime shader applies faction color as emissive material (emission strength 2.0). The defining visual element — the ship glows in faction color.
- *Edge accent faces:* Assigned to `faction_color` face group (edges/seams subset). Runtime shader applies faction color at reduced brightness (emission strength 0.8). Traces along edges, seam lines, structural boundaries.
- *Energy field:* VFX overlay in Godot (not model geometry). Semi-transparent halos for Warden aura, Bastion fortify zone, Interceptor detection edges. Tinted with faction color at runtime.
- *Drive signature:* Faction color whitened, emission strength 4.0. Engine/propulsion output — vivid, bright, the most emissive element on the model. Applied at runtime.

##### Example Generation Prompts

These prompts are starting points for 3D-Agent (Blender plugin) and Meshy (web/Godot plugin). Generate 3–4 variations per asset and select the best starting shape. All prompts assume low-poly output mode is enabled.

**3D-Agent prompt format** (for hero unit assets — generates directly in Blender):

> *Template:* "Create a low-poly [UNIT TYPE] spaceship for a strategy game. [TIER DESCRIPTION]. [SILHOUETTE GUIDANCE]. Style: flat-shaded, geometric, Art of Rally aesthetic. Target: [POLY COUNT] polygons. No textures — color will be assigned as flat materials in Blender."

**Tier 1 Raider:**
"Create a low-poly strike fighter spaceship for a strategy game. Frontier-era design: angular, utilitarian, built from scavenged parts. Narrow dart-shaped silhouette swept back for speed. Visible oversized thruster clusters at rear. Weapon hardpoints bolted onto nose. Exposed sensor antenna. Asymmetric details — a panel or component on one side only. Style: flat-shaded, geometric, Art of Rally aesthetic. Target: 200 polygons. No textures."

**Tier 2 Raider:**
"Create a low-poly strike fighter spaceship for a strategy game. Military-grade design: sleek, purpose-built, integrated systems. Narrow dart silhouette with swept-back geometry. Flush weapon mounts on nose. Integrated engine housing. Bilateral symmetry. Clean unified hull surface. Style: flat-shaded, geometric, Art of Rally aesthetic. Target: 200 polygons. No textures."

**Tier 3 Raider:**
"Create a low-poly advanced strike fighter spaceship for a strategy game. Far-future design: blade-like profile, razor-thin geometry, minimal surface detail. Elongated narrow silhouette tapering to a sharp nose point. Smooth flowing curves. No visible weapon mounts or engine housings. Organic-geometric hybrid form. Style: flat-shaded, geometric, Art of Rally aesthetic. Target: 250 polygons. No textures."

**Tier 1 Vanguard:**
"Create a low-poly heavy warship for a strategy game. Frontier-era design: blocky, heavily armored, utilitarian. Front-heavy wedge silhouette — thick armored prow, narrower at rear. Visible layered armor plating. Forward-mounted weapons. Blunt aggressive posture like a battering ram. Exposed structural reinforcement. Style: flat-shaded, geometric, Art of Rally aesthetic. Target: 400 polygons. No textures."

**Tier 2 Vanguard:**
"Create a low-poly heavy warship for a strategy game. Military-grade design: proper battlecruiser, contoured armor, integrated weapons. Front-heavy wedge silhouette with smooth deflection-angled plating. Weapons integrated into forward hull. Bilateral symmetry. Clean manufactured look. Style: flat-shaded, geometric, Art of Rally aesthetic. Target: 400 polygons. No textures."

**Tier 3 Vanguard:**
"Create a low-poly advanced heavy warship for a strategy game. Far-future design: organic front-heavy form, smooth surfaces, no distinction between armor and hull. Massive, dense-looking wedge shape with sweeping curves. Minimal surface detail — complexity implied through form. Subtly luminous appearance. Style: flat-shaded, geometric, Art of Rally aesthetic. Target: 450 polygons. No textures."

**Tier 1 Bombard:**
"Create a low-poly artillery spaceship for a strategy game. Frontier-era design: a long chassis built around an oversized main weapon. The cannon is the largest visible component — the ship is clearly built around it. Visible recoil bracing and power conduits along the weapon axis. Rear section is engines and power plant. Minimal armor. Longest silhouette of any unit. Style: flat-shaded, geometric, Art of Rally aesthetic. Target: 450 polygons. No textures."

**Tier 3 Bastion:**
"Create a low-poly advanced fortress spaceship for a strategy game. Far-future design: compact polyhedron shape, wider than long, impossibly dense-looking. Smooth geometric form — almost crystalline. Minimal surface detail. The heaviest, most solid-looking object imaginable. Subtly luminous deep glow. Style: flat-shaded, geometric, Art of Rally aesthetic. Target: 500 polygons. No textures."

**Meshy prompt format** (for structures and environment — web-based generation):

> *Template:* "Low poly [OBJECT TYPE] for a sci-fi strategy game. [DESCRIPTION]. Flat shaded, geometric, clean forms. [POLY TARGET] polygons."

**Tier 1 Station:**
"Low poly space station for a sci-fi strategy game. Frontier design: modular sections bolted together over time. Visible hab rings, docking arms at odd angles, solar panel clusters, antenna arrays. Grown through addition, not designed as a whole. Flat shaded, geometric, clean forms. 600 polygons."

**Tier 3 Station:**
"Low poly advanced space station for a sci-fi strategy game. Far-future design: monolithic single-form structure, smooth surfaces, luminous accent lines. Looks cast or grown rather than assembled. Large scale, elegant, minimal visible detail. Flat shaded, geometric, clean forms. 500 polygons."

**Asteroid (universal):**
"Low poly asteroid cluster for a sci-fi strategy game. 3–5 rocky fragments in a loose group. Irregular angular shapes. Dark gray stone. Flat shaded, geometric, clean forms. 150 polygons total."

**Derelict hull (universal):**
"Low poly wrecked spaceship hull fragment for a sci-fi strategy game. Broken section of a destroyed vessel. Torn metal edges, exposed interior structure. Tilted, drifting. Flat shaded, geometric, clean forms. 200 polygons."

**Navigation beacon (universal):**
"Low poly space navigation beacon for a sci-fi strategy game. Small pylon with a blinking light element on top. Simple functional design. Flat shaded, geometric, clean forms. 50 polygons."

##### Production Sequence

The recommended order for producing the Settled Reach asset set, optimized for learning curve and visual consistency:

**Phase 1 — Tier 2 units first.** Start with Tier 2 because it's the visual middle ground — clean and readable but not as creatively demanding as Tier 1's scrappy asymmetry or Tier 3's organic abstraction. Producing Tier 2 first establishes the "baseline" silhouette for each unit type, making it easier to push toward Tier 1 (rougher, more angular) and Tier 3 (smoother, more abstract) afterward. Order within Tier 2: Vanguard (largest, most straightforward shape), Bombard (distinctive long silhouette), Bastion (wide compact form), Raider (small dart), Interceptor (wide flat), Warden (radial projection geometry — the most unusual shape).

**Phase 2 — Tier 1 units.** Take each Tier 2 model's silhouette as the starting point and push it toward the Frontier language: add visible paneling, break symmetry, bolt on external components, roughen the surfaces. Same unit order as Phase 1.

**Phase 3 — Tier 3 units.** Take each Tier 2 silhouette and push toward the Zenith language: smooth surfaces, remove visible detail, introduce organic curves, simplify toward abstraction. Same unit order.

**Phase 4 — Structures.** Points of interest across all three tiers. Start with Tier 2 station (establishes the architectural language), then Tier 1 and Tier 3 variants. Then military installations, then resource nodes.

**Phase 5 — Environment.** Universal objects. Fastest to produce, lowest priority. Asteroids first (most common on-screen object), then derelicts, cargo, beacons, shield pylons, nebula volumes.

**Estimated total production time:** 18 unit models at ~45 min cleanup each = ~13.5 hours. 9 structure models at ~30 min each = ~4.5 hours. 6–8 environment models at ~15 min each = ~1.5–2 hours. Total: ~20 hours of Blender work spread across the production phases, plus generation time (negligible — minutes per asset in 3D-Agent/Meshy). One month of Meshy Pro ($20) covers all generation credits for structures and environment. 3D-Agent free tier (15 prompts/month) may require 2 months for all 18 unit models if generating 3–4 variations per unit to select from, or one month on a paid tier.

#### Humanoid Unit Animation Pipeline — Weapon Separation Pattern

> **RESOLVED (v2.02).** This section defines the production workflow for era packs containing humanoid units (infantry, cavalry, standard bearers, etc.) that require skeletal animation. The Settled Reach era's spaceship units do not require this workflow — they use code-driven transform animation in Godot (translation, rotation, scale tweens) and VFX particles for ability feedback. This section applies to all non-spaceship eras: Roman, Medieval, Viking, Feudal Japan, WW2, and all future humanoid eras.

**The problem.** Humanoid units carrying weapons (swords, shields, spears, bows, standards) need skeletal animation for walk cycles, attack swings, idle poses, and death animations. AI 3D generation tools (Sloyd, Meshy) produce static meshes without rigs. Mixamo (Adobe, free) auto-rigs humanoid meshes and provides a library of pre-made animations — but Mixamo's auto-rigger treats weapon geometry as part of the body, assigning skin weights across multiple bones and producing warped, broken weapon deformation during animation.

**The solution — weapon separation.** Humanoid units are generated and rigged as bare bodies (no weapons, no shields). Weapons and shields are generated as separate standalone prop assets. Animation is applied to the bare body only. Weapons are attached at runtime in Godot via `BoneAttachment3D` nodes parented to hand bones exposed by the Mixamo skeleton (`RightHand`, `LeftHand`). The weapon mesh follows the hand bone perfectly through every animation frame.

**Production workflow per humanoid era:**

1. **Sloyd: Generate bare bodies.** Each humanoid unit type at each tier is generated in T-pose (arms spread, no weapons, no shields). T-pose is required for Mixamo's auto-rigger to correctly identify joint positions.
2. **Sloyd: Generate weapon props.** Swords, shields, spears, bows, standards, etc. are generated as standalone objects — one per weapon type per tier. Weapon props are shared across unit types (e.g., all T2 sword-wielding units use the same T2 gladius mesh).
3. **Mixamo: Auto-rig and animate.** Upload each bare body as FBX or OBJ. Mixamo auto-rigs the humanoid and applies animations from its library (walk, idle, sword swing, death, etc.). Download as FBX Binary at 30fps with skin.
4. **Blender: Cleanup and materials.** Import rigged/animated FBX. Apply era-appropriate materials, fix any topology issues, verify animation playback. Export as GLB.
5. **Godot: Runtime weapon attachment.** Import the animated GLB. Create `BoneAttachment3D` nodes on `RightHand` and `LeftHand` bones. Parent weapon prop meshes to these attachments. Weapons follow hand bones through all animations automatically.

**Weapon prop reuse.** Weapons are shared across units within a tier. A T2 Roman gladius is used by the Legionary, Equites, and any other T2 sword-wielding unit. This means weapon props per era are a small fixed set (typically 10–15 total across all tiers), not a per-unit cost.

**Animation state machine.** Godot's AnimationTree with a state machine manages transitions between clips (idle → walk → attack → death). Cross-fade blending over 0.2s prevents hard snapping between poses. Most humanoid units need only 3–4 animation states. The Mixamo animation library provides all common states; custom animations are not required for launch.

**Spaceship eras do not use this workflow.** Spaceship units (Settled Reach and any future space-themed eras) use rigid body movement — code-driven position/rotation transforms in Godot. Abilities (Brace, Surge, Barrage, etc.) are communicated through VFX (particle effects, shader flashes, scale pulses), not skeletal animation. No rigging, no Mixamo, no animation files. This keeps the spaceship pipeline fast and simple.

**Performance note.** At RTS camera distance, humanoid animation detail is barely perceptible. 30fps animation data with Godot's built-in interpolation produces smooth playback at 60fps game framerate. Humanoid models at ~5,000 polys with skeletal animation are well within performance budgets even at 200–400 units on screen simultaneously, provided instancing (MultiMeshInstance3D) is used for repeated squad members.

---

### Dynamic Naming System

The naming system generates names for all named entities in the game: people, places, units, and factions. It uses a variable-driven prompt architecture that produces massive output diversity through combinatorial variety, drawing from historical human naming conventions, Tolkien-esque construction, ancient Greek, Sumerian, invented linguistic roots, and beyond.

**The naming library is completely separated from the game.** Generated offline by the library builder pipeline, shipped as static JSON data. Zero runtime AI dependencies. No runtime API calls, no regeneration, no redraw. The game reads from pre-generated pools. This separation is non-negotiable — the game must never depend on AI availability at runtime.

#### Variable-Driven Prompt Architecture

The system uses a multi-stage pipeline. An AI first generates a diverse set of naming variables across three categories. Those variables feed a prompt builder that constructs generation prompts. A second AI pass produces the actual names. The combinatorial variety of variable combinations means the output stays fresh across runs without handcrafting individual prompts.

**Three variable categories:**

**Linguistic roots** (~15–20 values) — the phonetic foundation. Values like: Semitic triconsonantal, Polynesian open syllables, Germanic compound, Sino-monosyllabic, Tolkien-esque (Elvish-inspired), ancient Greek, Sumerian, invented liquid-heavy, invented guttural-aspirated, and others spanning a vast cultural range.

**Phoneme patterns** (~10–15 values) — structural rules layered on top of roots. Values like: patronymic (-son, -ov, -ibn), place-derived (-of-[place]), title-prefix, two-part compound, single name only, and others.

**Cultural flavor tags** (~8–12 values) — aesthetic/tonal direction. Values like: martial, pastoral, mercantile, priestly, frontier/rough, imperial/formal, and others.

Era markers are deliberately excluded as a variable category — consistent with the era-agnostic engine principle. Era-appropriate name presentation is handled by the theme pack layer, not the name generator.

#### Per-Faction Variable Subsets

At world generation, each faction is assigned a curated subset of allowed values per variable category (e.g., 2–3 linguistic roots, 3–4 flavor tags). All names for that faction are generated from prompts assembled from its allowed subset. Each generation batch, the prompt builder randomly selects one value from each of the faction's subset categories — pure random selection, no rotation tracking.

Subset width is a tuning knob for faction personality: a large subset produces diverse, cosmopolitan-sounding names (appropriate for the player's multi-regional civilization). A narrow subset produces coherent, monocultural-sounding names (appropriate for an isolated aggressive faction).

**Schism cultural drift.** Breakaway Schism factions inherit their parent faction's variable subset with one value swapped — representing cultural divergence. The Schism's names sound *almost* like their parent faction but slightly off, producing emergent cultural worldbuilding through the naming system.

#### Era-Split Pools

50% of each naming pool is **era-agnostic** — names that work across all theme packs, generated without era-specific style constraints. 50% is **era-specific** — generated per theme pack, with style prompts appropriate to that setting.

At runtime, the game draws from the era-agnostic pool half the time and the current era's pool the other half. The base engine ships with the era-agnostic pool plus the sci-fi era pool. Each future theme pack expansion adds its own era-specific pool that slots in alongside the permanent era-agnostic names.

#### Library Sizing

Initial release pool sizes per faction: 500 people names, 200 places, 200 units, 100 faction names. These are starter values — pool sizes will increase for full release. Generated offline in batches by the library builder.

#### Deduplication

Levenshtein distance filter at library build time. Names below a configurable edit distance threshold (e.g., 3 edits) from any other name in the same batch are discarded — no redraw, no additional API calls on rejection. Matches are simply dropped. The pool ships pre-cleaned. No runtime deduplication.

#### Name Reuse

Names assigned to active characters in the coherence ledger are unavailable for new assignment. Once a character has been dead for 500+ ticks, their name returns to the available pool. Across long playthroughs (1,000–2,000+ ticks / 10–20 gameplay hours), occasional name reuse is natural and expected — the same way real human naming traditions produce many people with the same name across centuries.

#### Coherence Ledger Interface

The ledger calls the naming system on character creation with a thin interface: `get_name(faction_id, category)` → string. The naming system returns a name from the appropriate pool and marks it as used. Clean separation of concerns — the ledger doesn't know about linguistic roots or variable subsets; the naming system doesn't know about characters, roles, or lifespans. The naming system needs faction IDs at initialization (minor coupling to world generation).
