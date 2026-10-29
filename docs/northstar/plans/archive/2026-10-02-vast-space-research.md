# Making space feel vast without a "texture on a sphere"

Research for the Ouroboros Manifold galaxy view (Godot 4.6, Forward+, free orbit camera, content ball radius 50, zoom out to 120).
Date: 2026-10-01. Tags used for sourcing: [DEV] = developer talk, interview, blog or engine docs; [3P] = third-party analysis or community; [NONE] = no reliable source found. Anything labelled "estimate" or "my reasoning" is mine, not a sourced fact.

## 0. The core diagnosis (my reasoning)

The "edge" the owner sees is not a texture problem. It is a geometry problem. Every backdrop piece (starfield r=55, dust r=60, rings r<=49) is a finite object sitting in world space. When the camera is at distance 120, it looks at that object from outside, so it sees the object's silhouette and the void beyond. No amount of better art on a bounded object fixes this. There are only two ways out:

1. Make the backdrop unbounded relative to the camera: it either follows the camera (direction-only sky, or a camera-centred wrapping volume) or it is so much larger than anything the camera can reach that its edge is never visible.
2. Dissolve the boundary: density and brightness fall off smoothly, so there is no line to see.

A pure direction-only sky (skybox, Sky shader, hash-on-direction) never shows an edge, but shows the second tell: nothing in it moves relative to the camera when the camera moves (zero parallax). With an orbit camera at distance 120, orbiting sweeps the camera through a large arc, so parallax from any layer within a few hundred units is very visible. A layer at infinity is the one layer that cannot show it. So: infinity layer for the far wash, true-3D layers at several finite depths for parallax, edge dissolved by fade.

## 1. Games surveyed

| Game | Technique | Why it reads as vast | Cost | Source (type) |
|---|---|---|---|---|
| Elite Dangerous | Night sky is built from real star catalogue data (naked-eye stars plus roughly 160,000 telescope-only stars, per Braben), rendered as 3D stars; Frontier added dust to the procedural model to match reality. The sky is regenerated from the player's location. | Stars are real positions, so flying produces true parallax; stars you see are places you can go. | Not published. Generated "in a fraction of a second" per a community summary; I could not find a Frontier talk on the renderer. | Braben quotes in PCGamesN interview [DEV, secondhand reporting]; "regenerated per location / parallax" claims from Steam community threads and fan wiki [3P]. https://www.pcgamesn.com/elite-dangerous/every-single-star-in-our-night-sky-is-in-elite-dangerous-david-braben-on-re-creating-a-galaxy-all-over-again |
| Homeworld / Homeworld 2 | Backgrounds are not textures. They are tessellated spheres with per-vertex colour, vertex density chosen by image contrast, mostly smooth gradients with sparse detail. | Gradient-dominated, low-detail backdrop keeps the hierarchy: backdrop never competes with ships, so ships read as small against something big. No texture compression artefacts or pixelation when the camera moves. | Very low: a modest vertex-coloured mesh. One modern re-implementation reports 196 MB memory saved versus textures. | Simon Schreibt analysis of the file format and tooling [3P]; hw2view viewer by laanwj [3P]. https://simonschreibt.de/gat/homeworld-2-backgrounds/ , https://github.com/laanwj/hw2view . NOTE: this is still a sphere, so it has the "no parallax" tell, but it hides it by being soft and gradient-only. |
| EVE Online | Nebulae and starfield are separate layers; nebulae are authored 3D objects whose view is rendered into a skybox per system; the star foreground is semi-generated from galaxy position. Few, highly distinctive nebulae positioned per region. | Position-dependent nebulae give orientation and a sense of travel across a map; layering. | "Load times practically zero." No numbers. | Brendan Drain, Engadget column [3P], who says he is unsure whether skyboxes are baked or built at jump time. https://engadget.com/2011/12/11/eve-evolved-touring-a-galaxy-reborn . Forum posts agreeing on the 2-layer split are community [3P]. |
| Outer Wilds | Reported: stars as a particle system centred on the player, billboarded, no skybox. | Stars are local to the player, so they get real (tiny) parallax and can be animated. | Unverified. | I found only a YouTube video titled "Star Rendering With No Skybox" (https://www.youtube.com/watch?v=Ipl7EVDsExk) and a third-party asset pack (Stone Baked Games) that says it is "Outer Wilds style" and makes no claim about the real game. I could not confirm any of this from Mobius Digital. Treat as [NONE]. |
| No Man's Sky | Galaxy is generated from seeds; the galaxy map is a real-time render of the actual star data. | The map is the real galaxy, so zooming in is continuous with play. | Unknown. | Generic description from Wikipedia and Game Informer [3P]. I found NO developer source (GDC talk or blog) on how the in-space sky, dust or nebulae are drawn. [NONE] for the technique. Hello Games GDC 2017 talk by Innes McKendrick exists but is about planet/world generation, not the sky. https://www.gamedeveloper.com/programming/video-how-continuous-world-generation-works-in-i-no-man-s-sky-i- [DEV] |
| Space Engine | Real catalogue data plus procedural generation for the rest; mentions of a logarithmic depth buffer appeared only in a search summary of its settings. | Real data at all scales. | Unknown. | Overview from Wikipedia and an interview [3P]. Log depth technique itself is documented by Outerra (below) [DEV]. I could not verify Space Engine's own renderer from a developer source. |
| Stellaris galaxy map | Not found. | n/a | n/a | [NONE]. Only generic Paradox/wiki results; no technique source. |
| Everspace | Procedural levels filled with "backdrops, planets, nebulas"; GPU particle FX; UE4. | Per-sector colour palette plus big backdrop objects. | Developer says rendering performance was the bottleneck, not the backdrop. | Unreal Engine developer interview [DEV, vague]. https://www.unrealengine.com/developer-interviews/revving-the-engine-everspace?lang=en-US . No technical detail on the sky. |
| House of the Dying Sun | Flat-shaded polygons, no textures, light effects; rust-red dust backdrops. | Art direction (limited palette, big simple shapes). | n/a | Wikipedia and PC Gamer [3P]. No technique source found. |

Honest summary of the survey: the only games for which I found a primary or near-primary statement about the sky are Elite (data-driven 3D stars) and Homeworld (vertex-coloured mesh, via a third-party teardown). The rest is thin. The techniques in section 2 are drawn from engine docs and general graphics practice, not from claims about those games.

## 2. Techniques, concrete

### 2.1 Layered parallax (the missing cue)
Use several star layers at different true depths. A camera move of distance m shifts a layer at depth D by roughly m/D radians. So a layer 100 units away swings visibly; one at 5000 barely does; a texture at infinity does not at all. The eye reads the differential between layers as depth. Build 3 to 4 layers, depths spaced roughly geometrically (for example 80, 250, 800, 2500), star size and brightness scaled with depth so they stay roughly constant on screen (otherwise far layers become invisible dots; keep them in the 1 to 3 pixel range).
Cost (estimate): one MultiMesh or point mesh per layer, 2k to 8k stars each, unshaded, additive. Tens of thousands of tiny quads is trivial on a ten-year-old GPU. The bottleneck is overdraw and fill, not vertices.

### 2.2 Camera-relative wrapping volume
A box (or shell) of N points that always surrounds the camera. In the vertex shader: `p = base + offset; p = mod(p - cam, size) - size/2 + cam` (or equivalent), so a point leaving one face re-enters at the opposite face. Density is constant around the camera, forever, with zero CPU cost per frame. Add per-point fade near the box faces (alpha as a function of distance to the wrap boundary) so the wrap pop is invisible. Best for dust and near-field particles because they give strong parallax and motion cues when panning and zooming. Not needed for far layers if the camera is bounded (see 2.9).
Cost (estimate): one draw call, 5k to 30k points, a few ALU ops per vertex.
Source for the building blocks: Godot spatial shader docs list `CAMERA_POSITION_WORLD` and the `world_vertex_coords` render mode, and `mod()` is a standard built-in. https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/spatial_shader.html [DEV]. I did not find a ready-made Godot 4 example of the exact technique; you build it.

### 2.3 Procedural direction-based star shader
Hash the normalised view direction at several scales (cells on a sphere, one star per cell, random brightness and colour, optional twinkle by time). Strength: truly infinite, no geometry, no edge, resolution-free. Limit: no parallax. Two known Godot examples: https://godotshaders.com/shader/spatial-starfield/ (MIT, multi-layer, "parallax" by exponential layer scaling in a screen-space-like way) and https://godotshaders.com/shader/starfield/ . Be aware that "parallax" in these shaders typically means scrolling layers at different rates against a camera translation or time, not true 3D parallax, so on an orbit camera they may still read as a skin. Verify on the orbit camera before adopting.
Cost (estimate): per-pixel over the whole screen unless you use a cached pass (see 3.1).

### 2.4 Cheap infinity layer plus true-3D layers
Put the soft, low-frequency stuff (colour wash, faint galactic band, very dim star dust) in a direction-only background. Put anything the eye is supposed to judge distance from (points, nebula cards, dust) in real 3D. The infinity layer should be dim and low-contrast so its lack of parallax is not noticed (this is exactly why Homeworld's gradient-only backdrops work: the lack of detail leaves nothing to track).

### 2.5 Distance fade and aerial perspective
Fade density and brightness with distance from the content (or from the camera) rather than clipping at a radius. In Godot: per-point alpha in the shader as `smoothstep(r_out, r_in, length(p - centre))`; or Environment depth fog, with Aerial Perspective tinting fog from the sky colour (Environment docs). Note: Godot docs state fog "can cause color banding, especially at higher density levels". Also note that depth fog affects only opaque and transparent geometry that opts in; unshaded additive points are often better faded manually in their own shader. https://docs.godotengine.org/en/stable/tutorials/3d/environment_and_post_processing.html [DEV]
Also usable: `visibility_range_begin/end` with `VISIBILITY_RANGE_FADE_SELF` (Forward+ only per the class docs) to fade whole GeometryInstance3D nodes in and out by distance. https://docs.godotengine.org/en/stable/classes/class_geometryinstance3d.html [DEV]

### 2.6 Nested / self-similar structure
Repeat the scene's own structure at larger scale and dimmer: the ball of systems, its filaments and rings become one "galaxy" among others. Use impostors, not full copies: for each distant "galaxy" a low-count point cluster (a few hundred points), maybe a ring pair and a glow sprite, rotating very slowly. Angular speed of motion falls as 1/distance, so scaled copies automatically move slowly, which is itself a scale cue. Do 2 or 3 scale steps, not infinity: the camera cannot see past about 120 plus the pan range, and an infinite regress buys nothing visible. Risk: if distant copies are the same shape as the near one the eye sees cloning; randomise orientation, count and tint.
No game source found; this is my reasoning.

### 2.7 Volumetric and fake-volumetric nebulae
Options, cheapest first: (1) a few huge soft noise-textured billboard cards at depth 200 to 1500, additive, slowly rotating or drifting, depth-sorted back-to-front; (2) many tiny sprites in a cloud (particle nebula); (3) a low-res raymarch. Gaia Sky chose full-screen raymarching rather than billboard particles for nebulae, noting particles looked worse but raymarching costs shader work and needs depth integration. https://tonisagrista.com/blog/2024/rendering-aurorae-nebulae/ [DEV, an open-source app author]. Raymarched nebulae are the expensive route; given the art direction (low-poly, luminous points and lines) I would stylise as a handful of faceted, low-alpha, flat-colour polygons (think translucent shards) rather than noise volumes. Godot has a community volumetric nebula shader: https://godotshaders.com/shader/volumetric-nebulae-clouds/ [3P].
Cost (estimate): cards 5 to 20 quads, fill-rate only; raymarch 20 to 60 steps per pixel, noticeable on integrated GPUs unless run at quarter resolution.

### 2.8 Motion and scale cues
Slow drift on far layers; twinkle (brightness modulation, per-star phase); star size and brightness following a heavy-tailed distribution (many dim, very few bright); a trace of bloom (Environment glow; Godot docs list additive/screen/softlight modes and note the cost of bicubic upscaling on desktop); depth of field is rarely worth it; camera-speed streaks, if used, should be subtle and only on near dust. These are standard practice; no game-specific source.

### 2.9 Clamping the camera, hiding the boundary
Zoom limits and pan clamps remove the need for infinite machinery: if the camera can never be farther than R_cam from the origin, any static layer beyond a radius of several times R_cam never shows an edge from inside the allowed region, and it needs no wrap and no camera-following. Soft limits (ease-out and a gentle pull-back as you approach the limit, plus the scene dissolving rather than stopping) hide the boundary better than a hard stop. Clamping does not solve "the content ball looks like an island in a void" if the void has nothing in it; it only bounds how much void is visible. (My reasoning; no game source.)

### 2.10 Precision (floating origin, depth range)
Float32 gives about 7 decimal digits. At magnitude 10,000 the spacing between representable values is about 0.001 (arithmetic), so nothing in a scene of radius 50 to 2,500 units has a visible precision problem. A floating origin is not needed. Godot 4.3+ uses reverse-Z, which the engine team describes as a large depth precision improvement at no performance or memory cost, and double-precision builds are a separate custom compile. https://godotengine.org/article/introducing-reverse-z/ , https://docs.godotengine.org/en/stable/tutorials/physics/large_world_coordinates.html [DEV]. Logarithmic depth (Outerra, https://outerra.blogspot.com/2009/08/logarithmic-z-buffer.html [DEV]) is for planet-scale-to-metre-scale ranges; irrelevant here. The one thing to watch: make sure Camera3D `far` exceeds the farthest layer (keep layers under `far`, default 4000 per my recollection of Godot; check the project's setting), and if layers are huge, scale point size so they stay visible.

## 3. Godot 4 specifics

### 3.1 Sky shaders
Sky shaders can render a procedural background with no geometry. Per docs, the shader can run in several passes: the cubemap pass (updates the radiance cubemap, "for every pixel in the cubemap", but only when parameters, TIME, camera position, lights or screen size change), half-res and quarter-res passes (`render_mode use_half_res_pass`/`use_quarter_res_pass`), and the main background pass at full res. Recommendation from the docs: do expensive work in the cubemap pass and read it back via `RADIANCE`. Caveat (my reasoning): if the shader uses `TIME`, the docs say that triggers cubemap updates, so an animated sky costs more; an animated direction-only sky is probably unnecessary because motion belongs to the true-3D layers. https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/sky_shader.html [DEV]
Cost (estimate): a static, cached sky is near free per frame; an uncached multi-octave hash at 1080p is a few tenths of a millisecond on discrete GPUs and more on integrated.

### 3.2 GPUParticles3D
Particle process shaders have `start()` and `process()`, keep last frame's output, and expose `TRANSFORM`, `VELOCITY`, `COLOR`, `CUSTOM`, `USERDATA1..6`, `EMISSION_TRANSFORM`, `RESTART` (docs). `local_coords = false` makes particles live in world coordinates. `visibility_aabb` is the region that must be on screen for the system to be active: grow it for any system that spans the view, otherwise the whole system pops out when its node leaves the frustum. `fixed_fps` and `interpolate` let you cap particle update cost. https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/particle_shader.html , https://docs.godotengine.org/en/stable/classes/class_gpuparticles3d.html [DEV]
Practical use: a camera-wrapping dust volume can live in the particle `process()` (read camera position via a uniform that a script updates each frame, or place the emitter on the camera), but a MultiMesh plus vertex-shader wrap (below) is simpler and cheaper for a static field.

### 3.3 MultiMesh
One draw call for thousands of instances. Set `custom_aabb` on the MultiMeshInstance3D (GeometryInstance3D property) to a huge box so culling does not drop the field when the camera moves; if you wrap in the vertex shader, instance positions are outside the AABB anyway. (GeometryInstance3D `custom_aabb`/`extra_cull_margin` exist per docs.)

### 3.4 Spatial shader tricks
In a `spatial` shader with `render_mode unshaded, blend_add, depth_draw_never, depth_test_disabled` (check names against the 4.6 docs; `depth_draw_never` and `depth_test_disabled` exist as render modes), draw order is controlled with `render_priority` on the material (lower first) and `sorting_offset`/transparent pass ordering. For camera-relative wrapping compute in the vertex function: `vec3 world = (MODEL_MATRIX * vec4(VERTEX,1)).xyz;` then wrap against `CAMERA_POSITION_WORLD`, then write back into `VERTEX` with `world_vertex_coords` render mode. Draw far layers first with depth writes off so they never occlude systems.

### 3.5 Fog, volumetric fog, visibility ranges
Depth fog and aerial perspective: cheap but can band; volumetric fog: light-aware but a froxel cost I would not spend on an art style of luminous points; `visibility_range_*` with fade: Forward+ only for fades, so it is available in this project's renderer.

### 3.6 Existing community starfields
Godot Shaders "Animated Starfield" (MIT, spatial, multi-layer). Paul Gestwicki's blog covers the 2D ParallaxLayer motion mirroring approach, which is 2D and not directly useful. http://paulgestwicki.blogspot.com/2020/04/infinite-scrolling-starfields-in-godot.html [3P]

## 4. For this project: ranked options

Common assumptions for the estimates: 1080p, a mid-range discrete GPU and an integrated GPU as the low end; the current scene is already busy, so I count only the added cost. These are estimates, not measurements.

### Option 1 (recommended core): Dissolve the edge, then add a bounded-camera deep field of real 3D star layers
What the player sees: stars and faint dust continue past where the old starfield ended, thinning out gradually with distance; when orbiting or panning, near stars slide past far ones; at max zoom the galaxy sits inside a deep field rather than a void.
How it avoids the tell: no sphere to see; layers at several finite depths (for example 100/250/800/2500 units) produce parallax; their outer limits are beyond anywhere the camera can see from inside the clamped region; brightness and density fade smoothly (per-point alpha by distance), so no boundary line exists. A very dim, low-contrast direction-only wash (colour gradient, galactic band) sits behind everything as the infinity layer.
Cost (estimate): 3 to 4 MultiMesh draw calls, 4k to 8k stars each, unshaded additive; total below 0.3 ms on discrete GPUs, perhaps 0.5 to 1 ms on integrated. Sky wash cached: close to free.
Build difficulty: low to medium. A star-layer generator script, one small shader (size by depth, fade), custom_aabb, render_priority. A day or two of Doer work plus tuning.
Risk: star size scaling and fill rate on integrated GPUs; far stars flicker (aliasing) if sub-pixel, so clamp minimum size and fade by size; the "dissolve" values need eye-balling. Low overall.

### Option 2: Camera-relative wrapping dust volume
What the player sees: faint motes drifting around the camera at all times, sliding past as the camera pans or zooms, and giving speed and scale cues when moving; they never run out.
How it avoids the tell: the volume follows the camera, so there is no boundary in any direction; being near, they generate strong parallax, which is the exact cue a texture lacks.
Cost (estimate): one draw call, 5k to 20k points, a handful of ALU ops per vertex; under 0.2 ms.
Build difficulty: medium. The wrap maths is simple; the fade-near-faces and the interaction with an orbit pivot (centre on the camera, not the pivot) need care.
Risk: if motes are too bright or too many they read as snow; at zoom 120 the motes become sub-pixel and vanish, so scale size with camera distance. Also check this does not conflict with the existing r=60 dust field (two similar systems; this one should replace it, not coexist, to avoid duplication).
Best used with Option 1 for the near field; Option 1 alone is enough if the camera is bounded.

### Option 3: Distant "other galaxies" as nested, dimmer scaled impostors (owner idea a)
What the player sees: when zoomed out, a few faint luminous clusters far off in the dark, each a miniature of the home galaxy's character (point cluster, one or two rings, a glow), moving very slowly.
How it avoids the tell: they have real positions (parallax) and a built-in scale story (this galaxy is one of many). Slow motion falls out of distance for free.
Cost (estimate): 3 to 8 impostors, each 200 to 500 points plus a ring or glow sprite; negligible (under 0.1 ms).
Build difficulty: low to medium; a generator reusing the existing ring and particle builders with parameters scaled down and a tint shift.
Risk: cloning is visible if copies match the home galaxy; clutter competes with the gameplay read; the owner's art direction ("busy and alive") favours it, but gameplay clarity may not. Needs a visual decision, not a technical one.

### Option 4: Faceted low-poly nebula shards
What the player sees: a few huge, faint, translucent coloured shapes far behind the galaxy, slowly drifting, that give depth and colour variation (and, per EVE, orientation: different directions look different).
How it avoids the tell: they are real 3D objects at different depths, so they slide against stars and against each other when the camera moves; faceting keeps the low-poly look.
Cost (estimate): 5 to 15 meshes with additive or alpha shading; fill-rate dominated; 0.2 to 1 ms depending on screen coverage. Avoid raymarched volumes: the cost is higher and the style does not call for it.
Build difficulty: medium (art direction heavy).
Risk: overdraw on large translucent shapes; competing with faction bubbles (also translucent) so colours must be kept apart; the owner may see it as clutter. It adds direction-dependent character but is not needed to remove the void.

### Option 5: Zoom limit and soft boundary (owner idea b)
What the player sees: they cannot zoom out far enough to see the galaxy as a small isolated island; at the limit the camera eases to a stop.
How it avoids the tell: it does not, by itself; it only bounds how much void is visible. With nothing beyond the starfield, even a modest zoom shows the edge from the right angle. It also does not address the unlimited pan if the pan is not clamped.
Cost: none.
Build difficulty: trivial.
Risk: it is a gameplay decision (how far the player may see) not an art one; I would not use it as the fix, but a soft limit combined with Option 1 is cheap insurance because it lets you size the layers.

## 5. Direct answers and recommendation

(a) Copy or nest the existing moving pieces outward? Partly yes, but not "forever". Nesting 2 or 3 sparse, dimmer, bigger copies (Option 3) adds a strong scale cue and free slow motion. A literal infinite regress costs more and shows nothing extra, because the camera cannot see past a few hundred units. Do not simply stretch the existing rings (they would have the same outer edge, only further out); use impostors with randomised shape. The existing starfield and dust should instead be extended outward with density that fades (Option 1) rather than stopping at 55 and 60.

(b) Limit zoom-out? Helpful, not sufficient. It shrinks how much void is visible and lets you size the backdrop layers, but with no backdrop beyond r=60 the void is still visible from any angle where the content does not fill the view. Use a soft limit (ease and gentle pull-back, not a wall) as support.

Recommended combination: Option 1 as the core (edge dissolve plus 3 to 4 true-3D depth layers plus a dim infinity wash), Option 2 replacing the existing r=60 dust field as the near-field parallax carrier, Option 3 added sparingly for the "many galaxies" feel, and Option 5 as a soft limit. Skip raymarched nebulae. Reason: the missing cue is parallax across multiple depths plus a boundary that fades, which this gives at roughly one-digit draw calls and well under 1 ms (estimate) on ordinary hardware, with no precision issues at this scale.

Verification suggestion for whoever builds it (my reasoning): record a short clip while orbiting at zoom 120 and at zoom 20, and check three tells: any visible radius, layers moving in lock-step, and shimmering of sub-pixel stars.

## 6. Sources

Developer or engine documentation [DEV]:
- Godot sky shaders: https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/sky_shader.html
- Godot particle shaders: https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/particle_shader.html
- GPUParticles3D class: https://docs.godotengine.org/en/stable/classes/class_gpuparticles3d.html
- GeometryInstance3D class (visibility range, custom_aabb): https://docs.godotengine.org/en/stable/classes/class_geometryinstance3d.html
- Environment and post-processing (fog, aerial perspective, glow): https://docs.godotengine.org/en/stable/tutorials/3d/environment_and_post_processing.html
- Spatial shaders: https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/spatial_shader.html
- Reverse Z article: https://godotengine.org/article/introducing-reverse-z/
- Large world coordinates: https://docs.godotengine.org/en/stable/tutorials/physics/large_world_coordinates.html
- Outerra log depth buffer: https://outerra.blogspot.com/2009/08/logarithmic-z-buffer.html
- Hello Games GDC 2017 summary (planets, not sky): https://www.gamedeveloper.com/programming/video-how-continuous-world-generation-works-in-i-no-man-s-sky-i-
- Braben interview (Elite night sky from data): https://www.pcgamesn.com/elite-dangerous/every-single-star-in-our-night-sky-is-in-elite-dangerous-david-braben-on-re-creating-a-galaxy-all-over-again (secondhand report of developer statements)
- Gaia Sky nebula rendering (open-source app author): https://tonisagrista.com/blog/2024/rendering-aurorae-nebulae/
- Everspace UE interview (vague): https://www.unrealengine.com/developer-interviews/revving-the-engine-everspace?lang=en-US

Third-party analysis or community [3P]:
- Homeworld 2 backgrounds teardown: https://simonschreibt.de/gat/homeworld-2-backgrounds/ ; viewer https://github.com/laanwj/hw2view
- EVE nebulae (Engadget column): https://engadget.com/2011/12/11/eve-evolved-touring-a-galaxy-reborn
- Elite "stars move in parallax / regenerated per location": Steam community threads (e.g. https://steamcommunity.com/app/359320/discussions/0/3288067088117995425/) and fan wiki https://elite-dangerous.fandom.com/wiki/Galaxy
- Godot Shaders starfield examples: https://godotshaders.com/shader/spatial-starfield/ , https://godotshaders.com/shader/starfield/ , https://godotshaders.com/shader/volumetric-nebulae-clouds/
- Gestwicki Godot starfield (2D): http://paulgestwicki.blogspot.com/2020/04/infinite-scrolling-starfields-in-godot.html
- Outer Wilds-style asset pack (not by the developers): https://stone-baked-games.itch.io/outer-wilds-style-starry-background-unity-package

No reliable source found [NONE]: how No Man's Sky draws its in-space sky and nebulae; how Space Engine's renderer works (only the Outerra log-depth technique itself is sourced); Stellaris galaxy map background; Everspace and House of the Dying Sun backdrop technique; Outer Wilds star rendering (only an unverified video and a third-party pack). Two fetches failed to return article content (space.com Elite interview, AusGamers Braben dust article), so nothing here relies on them.

Unverified details I flagged inline: exact Godot 4.6 render-mode names and the default Camera3D far value should be checked against the 4.6 docs before building.
