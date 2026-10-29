# Blobby territory bubbles: algorithm research for the Galaxy shell renderer

Date 2026-10-02. Read-only research. Our case read from: galaxy perf audit (2026-10-02), shell_metaball.gdshader, legacy_shell_renderer.gd.

## 0. Labels and honesty

Number labels: **[SRC]** = stated or measured by a cited source; **[DER]** = derived by me from the audit's counts or from public spec numbers with the arithmetic shown; **[EST]** = my estimate, factor 2 to 3 either way. No GPU was available, so every millisecond figure is [DER] or [EST] and must be replaced by the experiment in section 7.

Source labels: **primary** = paper, official talk or engine documentation/tracker; **third-party** = blog, forum, news write-up. Fetch status matters: I read the Godot class docs and the Kanamori project page. My attempts to open the Claybook slides, the NVIDIA Green slides and the WBOIT paper returned unreadable PDF binaries or empty pages, so claims about those come from my prior knowledge and are marked "(from memory, not re-verified)". I found no reliable published benchmark for "translucent merged metaball shells, 400 points, 15 colours" specifically; nothing below is a measured result for our exact case.

Facts of our field that drive everything (from the shader): kernel k = (1 - d^2/r^2)^3 with r = R * (0.6 + 0.4*significance); iso at 0.6 of own field; rival field is a MAX over rival systems; suppression is own * (1 - 0.8*smoothstep(0.3, 1.0, rival/own)). Two consequences I derived:
- Single isolated system: iso radius = 0.396 * r (solve (1 - x)^3 = 0.6, x = 0.157). For R = 8 and r in 4.8..8 that is 1.9 to 3.2 units; for R = 14 it is 3.3 to 5.5 units. [DER]
- The suppression term is not polynomial in the ray parameter, which rules out the cheapest analytic ray solves unless the seam formula changes (section 1).

Scale used below: ball radius ~55, plus kernel margin 14 gives a 138-unit cube. Systems density 400 / (4/3 pi 55^3 = 697k) = 5.7e-4 per unit^3 (the audit's 524k is for radius 50); a ray through the ball crosses the bounding spheres of about density * pi R^2 * chord = 5.7e-4 * 380 (R=11) * 90 = about 20 systems. [DER]

## 1. Metaball and implicit-surface rendering

**Kanamori, Szego, Nishita, "GPU-based Fast Ray Casting for a Large Number of Metaballs", Eurographics 2008 / CGF 27(2)** (primary; project page read, PDF with numbers not read). Per-pixel isosurface evaluation, no polygonisation; keeps a per-ray list of contributing balls and updates it; combines depth peeling over bounding spheres, Bezier clipping to solve for the iso crossing inside each interval, and tile-based ray casting. Needs no precomputation or acceleration structure. It relies on a compact polynomial kernel (ours is one: degree-6 in the ray parameter per ball), so the sum over overlapping balls is a degree-6 polynomial between interval boundaries and roots are found exactly, no step-size artefacts. Related primary: Gourmel et al., "BVH for efficient raytracing of dynamic metaballs on GPU" and "Fitted BVH for fast raytracing of metaballs" (CGF 2010), which target moving balls, an advantage we do not need.

Fit to us:
- Cost model [DER]: about 20 candidate spheres per ray at R=11; per pixel you test 20 spheres (about 15 ALU each, positions from a shared buffer), sort intervals, and solve 1 to 4 polynomials. That is roughly 20 * 15 + 4 * 100 = 700 ALU and no per-step texture fetches, but it needs a per-tile sphere list (clustered-light style: 400 spheres vs 8,160 16x16 tiles = 3.3M cheap tests, about 0.1 ms [EST], about 27 spheres per tile at distance 60 [DER]).
- Problem 1: our rival suppression (max over rivals, ratio, smoothstep) is not a polynomial, so Bezier clipping does not apply as is. It works only if the seam is redefined as a polynomial, e.g. own - lambda * sum(rival kernels), a look change that needs Westley's say.
- Problem 2: it needs per-pixel arbitrary code with lists. In Godot that means a compute shader through a CompositorEffect, Forward+ only (section 5), with no fallback for Compatibility or the QA llvmpipe path. Large implementation risk.
- Problem 3: camera inside bubbles makes lists long (20 or more intervals everywhere). It does handle it correctly, though.
- Verdict: elegant and exact, but it solves a problem we do not have (moving balls). Our data is static, so baking wins.

**Sphere tracing with Lipschitz bounds** (Hart 1996, primary, from memory). A sum of compact kernels has a gradient bound: single-kernel max slope is 6 d/r^2 (1 - d^2/r^2)^2 at d = r/sqrt(5), value 1.72/r. [DER] A sum of k overlapping kernels has L about k * 1.72/r (about 1.1/unit for 9 overlapping at R=14, 0.65/unit for 3 at R=8). Safe step is (iso - f)/L. In empty space f = 0, so step = 0.6/1.1 = 0.55 units: terrible. Raw density is therefore a bad sphere-tracing field; you need a separate distance-to-support field for empty space or a true signed distance (section 3). [DER]

**Per-pixel/tile candidate lists** (clustered/tiled culling, primary lineage: Olsson et al. 2012 "Clustered deferred and forward shading", from memory). Useful to shrink the CURRENT shader (audit rec 4: loops over about 20 candidates instead of 400). A uniform grid of system lists (cell 16 units) gives about 20 to 40 candidates per cell [DER] versus one trilinear fetch for a baked volume, so grid lists lose per step; they are only worth it at hit refinement (below).

**Bounding-sphere rasterisation for entry/exit** (Kanamori's depth peeling; also the Claybook trick of rasterising the SDF grid's bounding box and sphere tracing the contents, Aaltonen GDC 2018, primary, from memory/search summary). Rasterise 400 sphere proxies to get a min-depth and max-depth image of the union. Gain for us is small: the union of bubbles fills most of the galaxy ball, and the camera is usually inside it, so the interval is nearly the whole chord. Not worth the extra pass.

## 2. Screen-space fluid style (impostors, depth, smoothing)

Sources: van der Laan, Green, Sainz, "Screen space fluid rendering with curvature flow", I3D 2009 (primary; abstract only); Truong and Yuksel, "A Narrow-Range Filter for Screen-Space Fluid Rendering", I3D 2018 (primary; abstract only); Simon Green GDC 2010 slides (primary; PDF fetch failed, from memory: point sprites to depth, smooth, reconstruct normals, plus a thickness pass).

Pipeline: draw one sphere impostor per system to a depth buffer, smooth the depth (curvature flow or narrow-range bilateral), reconstruct normals, shade; thickness from additive sprites. Cost [DER]: impostor overdraw about 20 per pixel (same as the ray-sphere count above) = 20 * 2.07M = 41M fragments at 1080p, then 3 to 10 smoothing passes at full resolution, about 1 to 3 ms on a 3060 [EST].

What it gives: a merged blobby look with no field at all. What breaks for us:
- One depth layer: only the nearest surface exists. "Far bubbles visible through near ones" needs depth peeling per layer (multiply cost by 2 to 4), or a thickness-only look.
- Shape is the filter's, not the iso-surface: merge and blob size change with distance and zoom (screen-space kernel), so bubble shapes wobble when the camera moves; the iso 0.6 contour and the seam suppression are not reproducible.
- Factions: need one depth buffer per faction (15) or an id buffer. Seams between factions come out wrong because blending at seam pixels mixes depths of different shells.
- Camera inside: impostors are clipped by the near plane; surfaces behind the camera vanish; spheres cut by near plane leave holes in the depth buffer.
- One useful sub-idea: the additive thickness (line integral of the density along the ray) has a closed form per kernel (the integral of a degree-6 polynomial over the chord), so a single additive pass of 400 impostors gives an exact optical depth: a soft fog-like territory with no iso-surface. Cost = same 41M fragments [DER], about 1 to 2 ms [EST] on a 3060, about 0.3 ms at half-res. Different look (no crisp shell, no rim), so it is a fallback tier, not a drop-in. Faction colour mixes naturally additively and seams fall out as colour blends.

Verdict: not viable as the main shell look; viable only as the low-end fallback with a different look.

## 3. Baked volumes

**Density versus distance.** Density (our kernel sum) is smooth, so trilinear sampling reconstructs the iso-surface almost exactly: positional error is about (h^2/8) * |f''|/|f'|. With h = 1.44 (96^3 over 138 units), f' = 0.21/unit and f'' about 0.075/unit^2 at the iso for r = 8: about 0.09 units, well under a pixel at overview. [DER, rough] A signed distance field stores distance to the iso-surface, so the zero set is as accurate as the SDF's subvoxel precision and the sphere-trace step is the SDF value (Lipschitz 1). The kernel's own smoothing is lost in the SDF away from the surface (medial-axis creases), which does not matter for stepping.

**Empty-space skipping** (medical volume rendering lineage: Levoy 1990 early termination; min/max octree/brick skipping in Hadwiger et al., "Real-Time Volume Graphics", from memory; GigaVoxels, Crassin et al. 2009, from memory). Standard coarse structure: a 24^3 to 32^3 texture of per-brick min/max (or of conservative distance to the nearest surface, computed with an EDT). For us the structure is a distance-to-support or distance-to-surface texture at about 5 units per texel, 32^3 R8 = 32 KB. [DER]

**Engines.**
- Unreal mesh distance fields: per-mesh volume texture, max 128^3 = 8 MB each, packed into one atlas, streamed by distance; global distance field is a set of clipmaps around the camera (primary: Unreal docs, found by search).
- Claybook (Aaltonen, GDC 2018, primary): compute-shader SDF ray tracing of a fully deformable SDF grid, ran on Switch; coarse low-res pre-pass and bounding-box rasterisation to start rays near the surface (from memory/search summary; exact grid size and ms not verified).
- Dreams (Evans, SIGGRAPH 2015 "Learning from Failure", primary talk, only press summaries read): started with SDF edit lists and brick/gigavoxel ideas, abandoned them for point splats, a data point that brick/sparse SDF has real complexity cost; not an argument for our small static case.

**Resolution versus accuracy for our scale** [DER]:

| Grid | Voxel size over 138 units | R16F size | RGBA16F size | Voxels across a 4-unit-radius feature | Across a 1.9-unit iso radius (smallest case) |
|---|---|---|---|---|---|
| 64^3 | 2.16 | 0.52 MB | 2.1 MB | 1.9 | 0.9 (too coarse) |
| 96^3 | 1.44 | 1.77 MB | 7.1 MB | 2.8 | 1.3 (marginal) |
| 128^3 | 1.08 | 4.2 MB | 16.8 MB | 3.7 | 1.8 (good) |

A tight bounding cube (ball only) saves little. Recommend 96^3 for the main look, 128^3 if isolated tiny systems with small r must stay round.

**Partial updates.** A conquest changes the field only within r of the changed system: a cube 2 * 14 = 28 units on a side = 19.5^3 = 7.4k voxels at 96^3 (0.8% of the volume). [DER] In Godot see section 5: the CPU-side ImageTexture3D can only be updated whole; a compute shader writing a Texture3DRD can update any sub-region. The full re-upload of 1.77 MB is not the cost problem; building the data is.

**Normals from a baked volume.** Trilinear interpolation is C0: the gradient is discontinuous at voxel faces, which shows as faint creases when zoomed in (zoom 174 px/unit means a voxel spans 250 px). Options, cheapest first: (1) tetrahedral 4-tap gradient at the hit only (as GPU Gems/Inigo Quilez style); (2) store the gradient as extra channels so the filtered gradient is smoother; (3) 8-tap cubic B-spline reconstruction built from 8 trilinear taps, at hit only; (4) at the hit only, evaluate the true kernel sum over a per-cell candidate list (20 to 40 fetches), giving exact smooth normals independent of grid resolution, worth it only at close zoom. [EST on visual benefit; I have not rendered it]

## 4. Meshing the surface

Algorithms (all primary lineage, from memory): marching cubes (Lorensen and Cline 1987), surface nets (Gibson 1998; Mikola Lysenko's write-up is a popular third-party description), dual contouring (Ju et al. 2002). Surface nets or dual contouring give one vertex per surface cell and quads, fewer and better triangles than MC; with a smooth density field, sharp-feature handling of DC is unnecessary, so surface nets is the right pick.

**Smoothness.** Normals should come from the field gradient, not from face normals: evaluating the analytic gradient of the kernel sum (or the baked gradient) per vertex gives a smooth look even on coarse triangles. The silhouette stays polygonal: at 1.44-unit cells and zoom 174 px/unit, a facet edge is about 250 px long, so corners of the outline are visible when zoomed in close. [DER] In the overview (11 px/unit) facets are 16 px; marginal.

**Triangle count** [DER, wide range]. Surface area: each faction's shell is roughly closed; 15 shells of about 6k units^2 plus roughness 1.5 gives 100k to 150k units^2 total. Surface-net quads ~ 1.5 * area/h^2: at h = 1.44 about 72k to 108k quads = 145k to 215k triangles; at h = 2.16, 65k to 95k triangles. The audit's 20k to 40k at 2 units is likely too low. Either size is trivial for a GPU (about 1 ms or less [EST]); memory 70k to 110k vertices * 24 B = 2 to 3 MB. [DER]

**Translucency.** Godot sorts transparent objects, not triangles (Godot spatial shader docs: `depth_prepass_alpha`, `depth_draw_*`, fetched). Options:
- Additive blend (`blend_add` or premultiplied alpha): commutative, so order does not matter, and "far bubbles visible through near ones" is automatic. Our alphas are 0.05 to 0.5 and the rim/glow are already emissive, so additive is a close match; it costs the "darkening" of blend_mix, which this unshaded look hardly uses. This is my recommended path for any mesh variant.
- `depth_prepass_alpha`: shows only the front-most layer: kills far-bubble visibility. Rejected.
- Weighted blended OIT (McGuire and Bavoil, JCGT 2013, primary, page fetch failed, from memory): two render targets and a composite, approximate for high alpha and similar colours; Godot 4.6 has no OIT feature and a custom one needs a CompositorEffect or manual SubViewport passes: unnecessary given additive.
- Per-faction meshes drawn cull-front then cull-back: correct for convex, imperfect for concave shells; skip.

**Rim and seam glow on a mesh.** Rim = fresnel from the interpolated normal, trivial. Seam glow: store the rival term per vertex (CUSTOM0 channel) or, better, keep the baked 3D attribute texture and sample it at the fragment's world position, so glow is per pixel and independent of triangle size. Hybrid mesh + baked-texture shading removes the "triangle-sized glow" problem.

**Cost when territory changes** [DER/EST]: dirty AABB 28 units = 7.4k cells at 96^3. Re-meshing it in C (surface nets) is well under 1 ms; in GDScript about 10 to 50 ms (loops of 7.4k cells with 12-edge logic) so it needs a thread or a GDExtension. Chunk meshes: with 24-voxel chunks (35 units) the ball has about 30 non-empty chunks; a conquest re-meshes 1 to 8 of them; draw calls about 30 or 1 if merged. Too-small chunks (8 voxels) mean about 500 draws: avoid. GPU marching-cubes in compute is possible but Godot cannot feed an RD buffer into a MeshInstance3D without readback (workaround: vertex pulling from a Texture2DRD; unverified and risky). Prefer CPU meshing in C/GDExtension.

## 5. Godot 4.6 specifics (docs read where marked)

- **ImageTexture3D**: `create(format, w, h, d, mipmaps, Array[Image])` and `update(Array[Image])`; update must match the original size and format; no partial region (docs read; third-party/engine tracker: godot-proposals #4017 and issues #7146, #65762 are open requests for partial update; Godot 3 had a partial call, Godot 4 does not). Consequence: any CPU-side update re-uploads the whole volume (1.77 MB at 96^3 R16F, tiny [DER]); the bake itself is the cost.
- **Building the volume data**: GDScript over 885k voxels is far too slow; a full bake is seconds in GDScript [EST]. Acceptable options: (a) bake in GDScript on a Thread at load (hidden behind loading), dirty-region re-bake (7.4k voxels * about 20 systems = 150k kernel evals) on a thread, 0.1 to 0.3 s [EST], double-buffer so the old volume shows until the new one is ready; (b) GDExtension or the C sim producing a PackedByteArray (milliseconds); (c) compute shader through RenderingDevice writing into the volume.
- **Compute output into a spatial shader**: `Texture3DRD` wraps a 3D texture created on the RenderingDevice and is usable as a material texture; docs say it is low-level and intended for RenderingDevice work (docs read; the stable page I read is labelled 4.7, so check the 4.6 page for the same class). The compute-texture demo pattern is the main-RD path with `RenderingServer.call_on_render_thread`. Works in Forward+ and Mobile only, so not in the Compatibility/llvmpipe QA path; keep an ImageTexture3D path for that.
- **Spatial shader**: `uniform sampler3D x : filter_linear;` (shading language; the spatial page I fetched did not mention it, but the shading-language page lists sampler3D); writing `DEPTH` in any branch requires writing it in all; depth texture via `sampler2D ... hint_depth_texture`; `depth_prepass_alpha`, `depth_draw_*` render modes exist (docs read). Writing DEPTH or `discard` disables early-Z (as the audit notes).
- **Full-screen pass without a box**: a QuadMesh with `POSITION = vec4(VERTEX.xy, 1.0, 1.0)` and a large extra_cull_margin renders one fullscreen quad; ray from INV_PROJECTION_MATRIX. This replaces the 15 per-faction cull-front boxes by one draw (known Godot technique, third-party community pattern; not in the pages I fetched).
- **CompositorEffect**: Forward+ and Mobile only, runs on the render thread, only the 3D pipeline stages are exposed, uses RenderSceneBuffersRD and RD compute (docs read). It would host a half-res compute raymarch or the Kanamori approach but gives no Compatibility fallback and needs a mutex for sharing data with the main thread.
- **SubViewport pass**: the current design (half-res SubViewport with its own world, TextureRect overlay) works in all renderers; cost is a copy plus an extra pass, small relative to the shader. Keep it for the half-res scale; alternatively render in the main pass at full res once the shader is cheap.
- **MultiMesh custom data**: per-instance Color/custom data lets one draw carry position, radius and faction colour: useful for the impostor fallback (400 instances in one draw) or per-system overlays. (Godot docs, from memory.)
- **Update frequency**: territory changes a few times per few seconds, so everything above can rebuild on a worker thread and swap.

## 6. Per-approach comparison at our scale

Fetch counts below assume 64 steps and four crossings; 1080p = 2.07M pixels, half-res 0.52M. Throughput assumptions [DER from public spec rates]: RTX 3060 112 TMU * 1.78 GHz = 199 G bilinear texel/s, about 100 G trilinear/s after 3D and filtering penalties; GTX 1650 56 TMU * 1.665 GHz = 93 G, about 45 G trilinear/s; UHD 620 class iGPU about 20 G, about 10 G trilinear/s. Real throughput depends on cache hits and ALU; treat as 2x either way.

| Approach | Per-pixel work [DER] | 3060 full-res | 1650 full-res | iGPU | Change cost | Memory | Scaling with systems / factions | Camera inside | Look fidelity | Godot difficulty |
|---|---|---|---|---|---|---|---|---|---|---|
| Current shader | 10k to 25k point fetches | 30 to 130 ms (audit [EST]) | 140 to 290 ms | seconds | none | tiny | n, n^2, boxes per faction | fine | reference | exists |
| A. Baked density volume, one-pass march, 4 crossings | 64 march + 4 * (4 gradient + 1 attribute + 2 refine) = 92 trilinear, ~1.9 ms full-res work [DER, if memory-throughput holds] | 1 to 2 ms (half-res 0.3 to 0.6) | 3 to 5 ms (half-res 0.8 to 1.2) | 15 to 25 ms full, 4 to 6 ms half, 1 to 1.5 ms quarter | bake 7.4k voxels, thread; full upload 1.8 MB | 1.8 to 7 MB | independent of n and F after bake | native | identical field, mild voxel softness | medium |
| A+. A plus coarse skip texture and early out at alpha saturation | about 30 to 60% of A's steps [EST] | 0.5 to 1.2 ms | 1.5 to 3 ms | half-res 2 to 4 ms | + 32 KB | +32 KB | same | native | same | medium |
| B. Surface-nets mesh, additive, texture-sampled glow | 65k to 215k triangles; about 6 layers of blended overdraw per pixel = 12M fragments [DER] | 0.3 to 0.8 ms [EST] | 1 to 2 ms [EST] | 3 to 8 ms [EST] | re-mesh 1 to 8 chunks, C: under 1 ms; GDScript 10 to 50 ms | 2 to 3 MB mesh + volume if hybrid | triangles with surface area, not n | works, additive back faces seen | smooth normals, faceted silhouette when close; looks different at seams unless attribute sampled | medium to large (needs mesher in C or thread) |
| C. Analytic per-pixel Kanamori | 20 candidates * 15 ALU + solves, no fetches | 1 to 3 ms [EST] | 4 to 8 ms [EST] | likely over budget | none (static lists) | list buffers | n via tile lists | native | exact; seam formula must become polynomial | large; compute + CompositorEffect, Forward+ only |
| D. Screen-space impostor smoothing | 20 overdraw + 3 to 10 smoothing passes | 1 to 3 ms [EST] | 3 to 8 ms [EST] | 10+ ms | none | few buffers | n via overdraw | breaks (near plane) | merged-blob but unstable shape, single layer | medium |
| D'. Optical-depth impostors (soft fog look) | 41M fragments, additive | 1 to 2 ms (half-res 0.3) | 3 to 5 ms | 5 to 10 ms half-res | none | none | n via overdraw | fine | different look: no shell, no rim | small |

Cell notes: the A full-res figure comes from 190M trilinear / 100 G/s = 1.9 ms; the quoted range includes cache and ALU. The fixed-step artefact: with 64 steps over a 138-unit chord the step is 2.2 units while the smallest iso radius is 1.9 to 3.3 units, so thin tips can be skipped: use 80 to 96 steps for chords above 100 units, jittered start, or the skip texture to shorten the active chord. [DER]

## 7. Ranked shortlist

**1. Baked 96^3 R16F density volume plus small attribute volume, single fullscreen pass, half-res, coarse skip texture, 4 crossings, tetrahedral gradient at hits. (Recommended; matches the current plan.)**
Reasoning and numbers: 92 trilinear fetches per pixel at about 100 G/s (3060) and 45 G/s (1650) gives 1 to 2 ms and 3 to 5 ms at full 1080p, a quarter of that at half-res [DER, spec-based]. Cost independent of n and F; keeps the exact look and removes the audit's stale-rival defect. Camera-inside is natural. Marching field as R16F alone (1.77 MB, nearly L2-resident) and sampling the 4-byte RGBA8 attribute volume (colour, seam) only at hits keeps bandwidth low. Build the volume with a threaded GDScript bake first; move to compute (Texture3DRD) only if the 0.1 to 0.3 s dirty bake [EST] is felt. Risks: thin-tip skipping, C0 normal creases at close zoom (use the 4-tap/cubic or exact local evaluation at hits), integrated GPUs need quarter-res or about 40 steps.

**2. Same baked volume, surface-nets mesh for the shell, additive blend, per-fragment glow and rim sampled from the volume. (Second choice and the iGPU tier; also the later faceted low-poly mode.)**
Reasoning: GPU cost is fixed by triangle count (65k to 215k [DER]) and about 12M blended fragments, 0.3 to 0.8 ms on a 3060, 3 to 8 ms on an iGPU [EST], so it degrades best; no per-pixel marching at all. Costs: a mesher (C or threaded) and a smooth-silhouette risk when zoomed in (facets of about 250 px at 174 px/unit [DER]); chunked remesh is cheap (below 1 ms in C). It shares the bake with option 1, so building 1 first keeps 2 cheap as a quality tier. Not smooth enough at close zoom to replace 1 under the current "smooth" requirement.

**3. Optical-depth sphere impostors (soft-territory look), as a last-resort low-end tier only.**
Reasoning: 41M additive fragments [DER], 0.3 ms at half-res on a 3060 and perhaps 5 to 10 ms on an iGPU [EST]; no baking, no volume; exact closed-form line integral per kernel. It changes the look (no shell, no rim) so it needs a design ruling; listed only because the analytic and screen-space routes all fail either the look or the Godot-support test. Analytic Kanamori ray casting and screen-space fluid smoothing are NOT shortlisted: the first requires a polynomial seam model and compute/Forward+ only; the second cannot give layered, faction-separated, camera-inside shells.

**The one experiment that separates them cheaply (half a day, no gameplay code):**
Standalone Godot 4.6 scene with the real 400-system seed. Pre-bake the 96^3 R16F field offline once (a throwaway script writing a .res or a threaded GDScript at load; do not optimise it) and load it as ImageTexture3D. Implement variant A as a single fullscreen-quad shader with a `STEPS` constant and a half-res SubViewport divisor; implement variant B by running a 30-line surface-nets over the same array in a script, building one ArrayMesh with additive material. At three camera positions (overview 120, regional 25, close 7.5, plus one inside a bubble) read `RenderingServer.viewport_get_measured_render_time_gpu` for STEPS = 32, 64, 96 and divisors 1, 2, 4, and for B at 64^3 and 96^3 cells. That one run reveals (a) the true trilinear fetch rate on the owner's 3060 (to replace my 100 G/s), (b) whether A fits 2 ms, (c) B's overdraw cost, and (d) on the 1650/iGPU, which of A at quarter-res or B is the low tier. It also checks visually whether 96^3 is soft enough to need 128^3.

## 8. Sources

Primary:
- Kanamori, Szego, Nishita, GPU-based Fast Ray Casting for a Large Number of Metaballs (EG 2008) project page: https://kanamori.cs.tsukuba.ac.jp/projects/metaball/ (read)
- Gourmel et al., Fitted BVH for Fast Raytracing of Metaballs (CGF 2010): https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-8659.2009.01597.x (search listing only)
- van der Laan, Green, Sainz, Screen space fluid rendering with curvature flow (I3D 2009): https://www.semanticscholar.org/paper/Screen-space-fluid-rendering-with-curvature-flow-Laan-Green/19865d92faa033632cc1c8ecf95d12a7400c34f1 (abstract only)
- Narrow-Range Filter for Screen-Space Fluid Rendering (I3D 2018): https://dl.acm.org/doi/10.1145/3203201 (abstract only)
- Aaltonen, GPU-Based Clay Simulation and Ray-Tracing Tech in Claybook (GDC 2018): https://media.gdcvault.com/gdc2018/presentations/Aaltonen_Sebastian_GPU_Based_Clay.pdf (could not read the PDF; used search summary and memory)
- McGuire and Bavoil, Weighted Blended OIT (JCGT 2013): https://jcgt.org/published/0002/02/09/ (fetch returned nothing; from memory)
- Unreal Engine Mesh Distance Fields docs: https://dev.epicgames.com/documentation/en-us/unreal-engine/mesh-distance-fields-in-unreal-engine (search excerpt)
- Godot ImageTexture3D: https://docs.godotengine.org/en/stable/classes/class_imagetexture3d.html (read)
- Godot Texture3DRD: https://docs.godotengine.org/en/stable/classes/class_texture3drd.html (read; page labelled 4.7)
- Godot spatial shader reference: https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/spatial_shader.html (read)
- Godot Compositor / CompositorEffect: https://docs.godotengine.org/en/stable/tutorials/rendering/compositor.html (read)
- Godot proposals/issues on partial texture update: https://github.com/godotengine/godot-proposals/discussions/4017 , https://github.com/godotengine/godot/issues/7146 , https://github.com/godotengine/godot/issues/65762 (search listings only)
- Evans, Learning from Failure (Dreams), SIGGRAPH 2015 / Umbra Ignite: https://www.mediamolecule.com/blog/article/alex_at_umbra_ignite_2015_learning_from_failure_video (blog page only)

Third-party:
- DualShockers summary of the Dreams talk: https://www.dualshockers.com/media-molecule-shows-dreams-beautiful-failures-massive-untapped-potential-in-compute-shaders/
- Godot forum threads on 3D textures in compute shaders (e.g. https://forum.godotengine.org/t/handling-3d-texture-for-renderingdevice/130194), no complete compute-to-spatial 3D example found.

Not found: any published measurement of baked-volume raymarching cost for translucent metaball shells on RTX 3060 / GTX 1650 / iGPU; a verified statement of the Texture3DRD first-supported Godot version; the exact Claybook grid size and ms numbers. All such figures above are my derivations.
