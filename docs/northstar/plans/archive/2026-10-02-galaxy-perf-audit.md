# Galaxy mockup performance audit

Worktree: `/home/westopoli/Projects/om-push/wt/galaxy-before-shrink` (branch `push/mockup-galaxy-scale`, HEAD 9404a62b), directory `scenes/mockups/galaxy/`.
Read-only audit. Throwaway tools are in the scratchpad next to this file: `count.gd`, `dump.gd`, `timing.gd` (Godot headless), `emu.c`, `gen.c` (CPU emulator of the shader loop counts).

## 0. How to read the numbers

- **MEASURED** = counted from the real scene by a headless Godot 4.6.3 run (`env -u DISPLAY -u WAYLAND_DISPLAY godot --headless`). Headless uses the dummy renderer, so counts and GDScript CPU time are real; GPU time and anything rendered is not available. Note the headless run reported rendering method `forward_plus`, so the shell takes the real raymarch path (not the llvmpipe stand-in).
- **EMULATED** = I wrote a C program (`emu.c`) that replays the shader's exact control flow on the real seed 11/12/13 galaxies (positions, significances, owners dumped from the generator) and counts loop iterations per screen pixel. One "iteration" = one `texture()` fetch of a system position plus about 25 ALU ops (the body of `eval_own_field` / `eval_rival_field`). The count is exact for the algorithm; it validates against a synthetic galaxy generator to within about 10% (synthetic 4-faction 219-system galaxy: 10.9k iterations/pixel at the regional view versus 12.2k for real seed 11). Sample grid 96x54 rays per view.
- **ESTIMATE** = anything converting counts to milliseconds, or any claim about GPU hardware. These are order-of-magnitude (factor 2 to 3 either way) and must be confirmed on the owner's machine (section 7).

## 1. Inventory

### 1.1 Measured counts (seeds 11 / 12 / 13)

| Item | seed 11 | seed 12 | seed 13 |
|---|---|---|---|
| systems / edges / factions | 219 / 402 / 4 | 190 / 359 / 7 | 208 / 386 / 5 |
| owned systems (get shells) | 186 | 161 | 176 |
| MeshInstance3D total | 409 | 369 | 394 |
| of which filament tubes (own mesh + own ShaderMaterial each) | 402 | 359 | 386 |
| of which shell boxes (ShaderMaterial, raymarch) | 4 | 7 | 5 |
| StandardMaterial3D mesh instances (central sphere, halo, grid) | 3 | 3 | 3 |
| MultiMeshInstance3D (system points) | 1 (219 inst) | 1 (190) | 1 (208) |
| GPUParticles3D emitters | 16 | 16 | 16 |
| Label3D | 8 | 14 | 10 |
| SubViewport | 1 | 1 | 1 |
| DirectionalLight3D | 1 | 1 | 1 |
| Triangles in filament tubes | 102,912 | 91,904 | 98,816 |
| Triangles in points MultiMesh (130 verts, 216 tris per sphere) | 47,304 | 41,040 | 44,928 |
| Triangles in shell boxes | 48 | 84 | 60 |

Per filament: 17 rings x 9 verts = 153 vertices, 256 triangles, own `ArrayMesh`, own `ShaderMaterial` (measured: 61,602 total vertices on `ShaderMaterial` meshes for seed 11 = 402 x 153 + 4 boxes x 24).

Ambient particles (all GPU particles, measured): central glow 200, 12 rings x 250 = 3000, radial streams 600, dust 400, starfield 2000. Total **6,200 particles in 16 emitters**; every particle is a camera-facing additive quad of 0.1 to 0.3 world units (2 triangles). Rings, streams and glow run at `fixed_fps` 60 with interpolation, dust 30, starfield 0 (static).

Shell SubViewport: `size = visible_rect / 2`, update mode `UPDATE_ALWAYS` (4), no MSAA, own 3D world. Headless reported 960x960 (square headless window); on a 16:9 window the project's 1920x1080 base under `canvas_items` stretch gives **960x540 = 518,400 pixels**, independent of the real window size (the SubViewport reads `get_visible_rect()`, which is the base size; orbit_camera.gd documents this).

### 1.2 Draw calls (static estimate; engine counters are not available headless)

| Item | Draws | Pass |
|---|---|---|
| Filaments | 402 (one per edge) | transparent, additive |
| System points | 1 (MultiMesh) | transparent alpha (opaque would suffice) |
| Shell boxes | F (4 to 7), inside the shell SubViewport | transparent, full raymarch |
| Shell overlay | 1 canvas draw (TextureRect, premult blend) | canvas |
| Particle emitters | 16 | transparent, additive |
| Central sphere, halo | 2 | opaque-ish / additive |
| Grid plane (ImmediateMesh, 5 line strips + 12 line surfaces) | 17 (one per surface) | transparent |
| Label3D (2 sets: names and shell labels, each outline + fill) | about 16 to 28 | transparent |
| HUD | batched, small | canvas |
| **Total (seed 11)** | **about 470** | |
| Real game (about 800 edges, 15 factions) | **about 900** | |

Lights: one DirectionalLight3D, no shadows, and every material is unshaded, so the light does no work (it can be deleted). Fog is enabled (cheap depth fog).

### 1.3 Per-frame GDScript (measured CPU time, headless, so renderer-side calls are near free; treat as a lower bound)

| Function | Cost per call | What it does |
|---|---|---|
| `galaxy_view.update_view` (every frame, from `galaxy_mockup._process`) | **1.1 to 1.2 ms** at 219 systems / 402 edges | per system: `owner_color()` (loops factions), `Color`/`Transform3D` allocation, `set_instance_transform` + `set_instance_color`; per edge: dictionary lookup, `get_meta`, `set_shader_parameter("emphasis_multiplier")`; per label: two property writes |
| `constellation._process` | 0.15 ms | `set_shader_parameter("alpha_multiplier")` on every edge, every frame |
| `shell._process` | 0.005 ms | per faction `set_shader_parameter("shell_opacity")`, label alpha |
| `orbit_camera._process` | 0.002 ms | |
| `pick_at` (every mouse-motion event) | 0.33 ms | `unproject_position` for all systems |
| Build on regenerate (`HUD.timing_ms.build`) | 50 to 57 ms | filament meshes, territory textures |
| Generate (`gen`) | 75 to 101 ms | O(n^2 log n) linking, brute-force placement |
| `set_system_owner` conquest (rebuilds every shell) | 1.2 ms | new textures, boxes, materials per faction |

Per frame this is about 1.3 ms of GDScript at today's size. Scaling to 400 systems / 800 edges it is about 2.5 ms (estimate, linear), plus real renderer-side cost of 800 uniform-buffer updates per frame.

Tweens: central pulse and stream rotation (cheap, one node each) plus the camera move tween. No timers. Per-frame allocations: `update_view` creates a `Color` and `Transform3D`/`Basis` per system and a Dictionary from `_band_weights()` once; modest.

One-time or event costs: Godot rebuilds the faction shell on every `territory_set`, so the initial populate runs `_rebuild_faction_shell` once per owned system (186 times for seed 11), each creating two `ImageTexture`s, a `BoxMesh` and a `ShaderMaterial`. It is inside the 50 ms build, so harmless today.

### 1.4 A correctness finding on the way (measured)

Because of that rebuild-per-system order, a faction's rival texture contains only the other factions' systems that had been populated when its last system was added. Measured `rival_count` for seed 12: 124, 133, 134, 136, 137, 138 where the full value is 138 (161 owned minus 23). Seed 11: 132/136/138/139 versus 139 to 140. The gap suppression and seam glow therefore use incomplete rival data until a conquest triggers `_rebuild_all_shells`. A baked-volume rewrite removes this by construction. Not a performance issue; reported because it affects the look.

## 2. The bubble shader (`shell_metaball.gdshader`) in detail

### 2.1 What the code does, per fragment

For each faction there is one box mesh (`BoxMesh` with `cull_front`, so the back faces are drawn). The box is the faction's system bounding box plus `BOX_MARGIN = 14 x 1.15 = 16.1` on every side, which for today's interleaved factions is **75 to 120 units per side against a galaxy diameter of 100** (measured: box volumes 440k to 970k versus a ball volume of 524k). Every faction box therefore covers nearly the whole galaxy on screen, and when the camera is inside the galaxy (every view closer than about 45 units) the camera is inside every box and every box covers every screen pixel.

Per fragment of each box:

1. Ray/box intersection (about 30 ALU). `discard` if it misses.
2. March **52 fixed steps** across the chord. Step = chord/52, so about 1.5 to 2 world units for a 100-unit chord, independent of what is on screen.
3. Each step calls `eval_own_field(p)`: a loop over the faction's own systems (`N_o`, up to 512) that does **one `texture()` fetch per system, unconditionally**. The compact-support test `if (d2 >= r*r) continue;` comes after the fetch and the distance maths, so it only skips the final multiply-add. It saves essentially nothing on a GPU (a fetch is already paid; on a warp, lanes execute the loop together). The loop does break at `system_count`, which is the right bound.
4. Only if `own >= 0.3` does the step call `eval_rival_field(p)`, a loop over **every other faction's systems** (`N_r = n_owned - N_o`, up to 2048), again one fetch per system. The 0.3 gate is the only skip.
5. If `net = own x (1 - gap)` reaches 0.6 the march stops early (this is the only early exit; rays that never reach the threshold march all 52 steps).
6. On a hit, the shader runs 5 bisection steps and 6 central-difference normal samples, each through `eval_net_field`, which evaluates both loops unconditionally: **11 x (N_o + N_r)** fetches, plus one more rival eval for the border glow: total hit cost = 11 x n_owned + N_r fetches per hit fragment.
7. If `shell_opacity > 0.3` (overview band) it writes `DEPTH`. Writing depth and using `discard` both disable early-Z, which does not matter here because nothing is drawn in front of the shell inside its own SubViewport, but it also means a pixel already filled by a nearer faction does not save the later faction's draws.

What a ray costs, by outcome:

- **Ray misses the faction's bubbles (the common case: about 60 to 80% of box fragments today):** full 52 steps x N_o fetches, plus 52 x rho x N_r where rho is the fraction of steps with `own >= 0.3`. Fetches only, with no early exit.
- **Ray hits early:** a partial march plus the 11-evaluation hit tail, which is about as expensive as a full miss march.
- **Ray never enters the box:** one intersection test.

### 2.2 Cost formula

Let `n` = owned systems in the galaxy, `F` = factions, `N_f` = systems of faction f (`sum N_f = n`), `S` = steps (52), `p_f` = probability a pixel's ray hits faction f's bubble, `H = sum p_f` = expected hit boxes per pixel, `k` = fraction of a box's volume where `own >= 0.3` per own system.

Iterations per screen pixel (summing over every faction box that covers the pixel):

```
I_px  ~=  S * n * (1 - 0.5*p_hit)            own march (sum of N_f over boxes = n, regardless of F)
        + S * k * n^2 * (1 - 1/F)            rival march (rivals only evaluated near own systems)
        + H * 11 * n                          bisection + normal + border glow at hits
```

Two non-obvious consequences. First, the own-march term does not depend on the number of factions F: the loops sum to the total system count. Second, the rival term is quadratic in system count and the hit tail is proportional to the number of boxes that hit, which grows as more of the screen is covered by bubbles.

Frame iterations = 518,400 (shell pixels) x `I_px` averaged over the screen (the emulator's averages already include screen pixels that no box covers).

### 2.3 Emulated results (iterations per screen pixel at 960x540 shell resolution)

Views: overview = distance 120 (DIST_MAX, whole galaxy about fits), mid = 60, regional = 25 (DIST_DEFAULT), local = 10 focused on a faction-0 system. Pitch 40 / 40 / 55 / 30 degrees.

Current shader (compact kernel radius 14, 52 steps, 5 bisection steps):

| Galaxy | View | own march | rival march | hit tail | **total** | boxes covering a pixel | px with any hit |
|---|---|---|---|---|---|---|---|
| seed 11 (n=219, F=4) | overview | 5,380 | 464 | 1,339 | **7,183** | 2.6 | 47% |
| | mid | 7,733 | 1,112 | 3,035 | **11,881** | 4.0 | 94% |
| | regional | 7,148 | 1,524 | 3,527 | **12,200** | 4.0 | 93% |
| | local | 5,983 | 414 | 2,996 | **9,393** | 3.7 | 100% |
| seed 12 (n=190, F=7) | overview | 4,336 | 506 | 1,177 | **6,019** | 4.0 | 44% |
| | mid | 6,322 | 1,325 | 2,787 | **10,434** | 6.1 | 91% |
| | regional | 7,401 | 1,206 | 2,057 | **10,664** | 6.8 | 79% |
| | local | 5,713 | 2,290 | 2,692 | **10,695** | 5.8 | 90% |
| seed 13 (n=208, F=5) | overview | 5,370 | 489 | 1,362 | **7,222** | 3.3 | 47% |
| | mid | 7,567 | 1,141 | 2,652 | **11,360** | 4.8 | 88% |
| | regional | 6,817 | 1,226 | 3,633 | **11,675** | 5.0 | 98% |
| | local | 6,880 | 1,028 | 3,620 | **11,528** | 5.0 | 100% |

Today, then: **6,000 to 7,200 iterations per pixel at overview, 10,400 to 12,200 in the regional and local bands**. In frame terms 3.1 to 3.7 G iterations at overview, 5.4 to 6.3 G close in (518,400 pixels x I_px). Cost peaks at mid and regional zoom and does not fall again when zoomed in, because the camera is inside every box.

Real-game scale, synthetic galaxy of 400 systems (about 340 owned), 15 factions, nearest-capital territories (validated above). Case A: same ball radius 50, spacing 9 (denser). Case B: radius 61, spacing 11 (same density as today, galaxy 22% wider). Kernel radius left at 14 (the real kernel scale is not known).

| Case | View | own march | rival march | hit tail | **total** | boxes covering a pixel |
|---|---|---|---|---|---|---|
| A (R 50, 400 sys, F 15) | overview | 6,750 | 2,047 | 4,607 | **13,404** | 6.0 |
| | mid | 9,962 | 4,359 | 10,458 | **24,780** | 10.1 |
| | regional | 11,210 | 2,954 | 10,703 | **24,867** | 12.1 |
| | local | 8,130 | 5,080 | 9,338 | **22,549** | 7.9 |
| B (R 61, 400 sys, F 15) | overview | 7,545 | 2,624 | 5,157 | **15,326** | 6.9 |
| | mid | 10,626 | 3,659 | 10,742 | **25,028** | 10.8 |
| | regional | 12,192 | 3,192 | 6,392 | **21,776** | 11.6 |
| | local | 8,573 | 4,725 | 8,993 | **22,291** | 8.6 |
| A with F = 8 | regional | 11,260 | 2,589 | 9,019 | **22,869** | 7.4 |

So the real game costs about **2x today's prototype per pixel (22k to 25k iterations versus 10k to 12k)**, driven by system count, not faction count (F = 8 versus F = 15 changes the total by under 10%). Per frame that is about 11.7 to 12.9 G iterations at 960x540.

### 2.4 Converting to time (ESTIMATE)

Assumed effective throughput for this loop (point-sampled RGBA32F fetch with a uniform address, about 25 ALU; limited by texture-unit rate and ALU together). These are guesses from public GPU specs and must be replaced by the measurement in section 7:

| GPU class | iterations per second | today regional (about 6 G) | real regional (about 12.9 G) |
|---|---|---|---|
| Laptop iGPU (UHD 620 / Vega 8 class) | 5 to 10 G | 0.6 to 1.2 s | 1.3 to 2.6 s |
| Entry discrete (GTX 1650 / RX 580) | 45 to 90 G | 65 to 135 ms | 140 to 290 ms |
| Upper mid (RTX 3060 / 4060) | 100 to 200 G | 30 to 60 ms | 65 to 130 ms |
| Strong (RTX 4080 / 4090) | 400 to 800 G | 8 to 15 ms | 16 to 32 ms |

This matches the owner's report: a strong machine runs today's prototype cleanly (and without the extra 2x for real-game scale it would not at 400 systems on a mid card), while an ordinary player's hardware would not hold 60 fps even at today's size.

### 2.5 Why the earlier "giant bubble" version was slower or not

Git history of the shader and generator: commit cd7b4329 (influence 5.25, 64 steps, no bisection) used the kernel `r^2/(d^2 + r^2)` with no cutoff; c3af2be4 switched to a compact kernel (radius 10.5), added bisection and a bigger box margin; 9404a62b widened the radius to 14 and cut steps 64 to 52. The "bubbles filled most of the galaxy" version is the Lorentzian one (a 1/d^2 tail summed over 40 to 50 systems exceeds the 0.6 threshold far outside the cluster). I replayed that version on the same galaxies (emulated, 64 steps, box margin 1.6 x radius):

| Galaxy | View | Lorentzian 64 steps (giant) | Compact r=10.5 64 steps | Current r=14 52 steps |
|---|---|---|---|---|
| seed 11 (F=4) | overview / regional | 10,229 / 7,335 | 7,304 / 13,332 | 7,183 / 12,200 |
| seed 12 (F=7) | overview / regional | 12,222 / **35,216** | 5,679 / 10,831 | 6,019 / 10,664 |
| seed 13 (F=5) | overview / regional | 13,328 / **22,305** | 7,237 / 13,154 | 7,222 / 11,675 |

Reasoning from the shader, confirmed by the replay's breakdown (seed 12 regional: own march 5,541, **rival march 26,761**, hit 2,914):

1. **The rival gate stopped working.** The `own >= iso * 0.5` skip only helps when own is small away from the territory. A heavy-tailed kernel keeps `own` above 0.3 nearly everywhere in the box, so the second loop over all rival systems (`N_r` fetches) ran at almost every step instead of near own systems. That is the dominant cost: about 20x today's rival term on seed 12.
2. **Rays often did not hit.** The rival-suppression term `gap_factor` pulled `net` below 0.6 along many rays through the broad field, so those rays marched the full 64 steps (no early exit) with the expensive rival loop each step.
3. **64 steps instead of 52** adds a factor of 1.23 on the march.
4. It was **not** fill area: boxes already covered the screen (the old box margin was smaller, so coverage was actually lower: 2.0 to 6.2 covering boxes versus 2.6 to 6.8 today).

The effect is seed-dependent: with few factions (seed 11, F=4) early hits kept the giant version cheaper than today (7.3k versus 12.2k regional); with more factions (seed 12, F=7; seed 13, F=5) it was 1.9x to 3.3x slower. The honest summary is that giant Lorentzian bubbles were up to about 3x slower on 5 to 7 faction maps, driven by the rival loop, and that making today's compact-kernel bubbles large (radius 20 or 28 instead of 14) is **not** a big penalty by itself: emulated regional totals 11.7k to 12.4k (seed 11) and 13.3k to 16.5k (seed 12), about 1.0x to 1.55x, because big compact bubbles raise hit-tail cost but shorten own marches through earlier exits.

Confidence: **medium-high** that the Lorentzian version cost more on multi-faction maps and that the rival loop is the reason (it follows directly from the code and the replay counts); **medium** on the size of the factor, because I do not know which exact build the owner saw, the replay counts iterations rather than GPU time, and a strong machine's cache behaviour could shift constants. If "giant" meant compact kernels with a larger radius, the shader is only about 1.0x to 1.5x slower and his hardware experience may have been dominated by how many pixels were covered by bubbles at that zoom (more hit pixels means more of the 11-evaluation tail).

## 3. The ambient rig

- All 16 emitters are GPU particles; the process shaders are per-particle hash maths (4 hashes plus a sincos for rings), run at 60 or 30 Hz or not at all (starfield). Per-frame GPU work for 6,200 particles is negligible (estimate under 0.05 ms on any discrete GPU).
- Drawing: 6,200 quads = 12,400 triangles in 16 draws. Quads are small: at overview (distance 120, about 11 px per world unit on 1080p) a 0.15-unit quad is about 1.6 px square; at the closest zoom (distance 7.5, about 174 px per unit) a particle 15 units away is about 17 px square. Even with a few hundred close-up particles the additive overdraw is well under 0.5 M pixels (estimate, under 0.3 ms on a mid GPU).
- The central halo is a 20 x 20 unit billboard with a 256x256 radial gradient, `no_depth_test`, additive. Its screen area is 218 px square at distance 120, 1,045 px square (52% of a 1080p screen) at distance 25, and larger than the screen below about 12. It is one full-screen additive texture fill at close zoom: about 2 M pixel writes, estimate 0.1 to 0.2 ms on a mid GPU. Fine.
- Rings, grid lines and the central sphere: negligible.
- **Several times more of it (the owner's ask):** cost is linear in particle count and in on-screen quad area. At 10x (62k particles) estimate +0.1 to 0.5 ms GPU on a mid card, +3 MB of particle buffers (64 B each). Stars placed further out are smaller on screen at fixed world size, so they are cheaper; to stay visible their world size must grow with distance, which holds screen area per star roughly constant (3 x 3 px is about 9 px^2, so 50k stars is about 0.45 M px, estimate under 0.2 ms). The real limits are the number of emitters (each is a draw and its own process pass) and keeping stars bright enough to read, not fill rate. The static starfield does not need a particle system at all (see recommendation 7).

## 4. Filaments and star points

- **Filaments:** one `MeshInstance3D` per edge, each with its own `ArrayMesh` (17 rings x 8-sided tube, 153 vertices, 256 triangles) and its own `ShaderMaterial` instance. Built in `_on_connection_added` when the data model emits `connection_added` (once per edge at regenerate, again for each edge touching a conquered system). No rebuild per frame, but two `set_shader_parameter` calls per edge per frame (`alpha_multiplier` from the constellation renderer, `emphasis_multiplier` from `update_view`) which is 2 x 402 per frame today. Shader: additive, `cull_disabled`, a sine and a dash step per fragment, trivial.
- Cost today: 402 draws, 103k triangles (measured). Radius is 0.0175 (trade) to 0.0375 (border) world units, so at overview a tube is about 0.4 px thick: 256 triangles per edge, each a few pixels, which is the worst case for GPU rasteriser efficiency (2x2 quad overshading) and for draw-call count. Fill is negligible.
- At 800 edges (real game): 800 draws, about 205k triangles, 800 material/uniform updates per frame. Estimate 1 to 3 ms CPU (draw submission plus GDScript) and 0.5 to 1.5 ms GPU; the draw count is the real cost on weak CPUs. At 15 factions the generator will also produce roughly 1.7 edges per system, as seen here (402/219 = 1.84).
- **Star points:** one `MultiMeshInstance3D`, 219 instances of a 12x8 sphere (130 vertices, 216 triangles) = 47k triangles, one draw. `update_view` rewrites transforms and colors of every instance every frame (14 KB upload, trivial); the cost is the GDScript loop (about 0.5 ms of the 1.1 ms), not the GPU. At 400 systems: 86k triangles, still one draw; a 6x4 sphere would cut that 4x with no visible change at 1 to 20 px point sizes.
- Dead code risk: the pass-1 `update_view` loop runs for a flat-state feature (hover/pin emphasis) every frame whether or not anything changed.

## 5. Scaling table

| Cost | Screen resolution | System count n | Faction count F | Zoom / coverage |
|---|---|---|---|---|
| Shell raymarch (dominant) | **none**: fixed 960x540 base/2 SubViewport; scales with aspect ratio if the window is wider than 16:9 (expand mode) | own march and hit tail linear in n; rival term roughly n^2 | almost none for the loop total (sum over boxes is n); fragment launches, texture rebuilds and overdraw grow with F | peaks when camera is inside the galaxy (every box covers the whole screen); drops about 40% at full pull-back because boxes cover less of the screen |
| Shell compositing | one 960x540 upscale blend, negligible | none | none | none |
| Filaments | tiny fragment cost | draws and triangles linear in edges (about 1.8 x n) | none | none (alpha only) |
| Points | fill trivial | triangles linear in n | none | none |
| Ambient particles | grows with quad pixel area; halo grows to full-screen at close zoom | none | none | close zoom enlarges nearby quads |
| GDScript per frame | none | linear in n and edges (1.1 ms now, about 2.5 ms at 400/800) | linear in F (labels) | none |
| Regenerate / load | none | generation O(n^2 log n) (about 100 ms now, about 330 ms estimated at 400) | small | none |
| Main 3D pass fill | native window pixels (3D is not stretched by `canvas_items`) | none | none | none |

## 6. Ranked recommendations

Gain factors are on the shell field cost unless stated. All gains are estimates derived from the iteration counts above.

### 1. Bake the territory field into one 3D texture and march that in a single pass. First change, large payoff, medium effort.

What: on territory change, evaluate the net field (own x gap-suppression, winner faction, border term) on a coarse voxel grid (for example 64^3 to 96^3 at about 1.5 to 2 units per voxel, RGBA16F half-float, 4 to 7 MB; channels: net field, rival/border term, faction colour packed in two channels or a second small texture). The fragment shader then marches the volume with one trilinear fetch per step. Merge all factions into one box and one draw. Rebake only the dirty AABB on a conquest (a change affects at most 2 x radius = 28 units, about 14^3 voxels, a few ms in GDScript; the initial full bake can run at load or on a thread, or in the C sim).

Expected gain: per pixel from 10k to 25k iterations to about 52 + 6 fetches plus normal (about 60 to 150 fetch-equivalents, counting trilinear as 4 point fetches), i.e. **roughly 50x to 150x less shell shader work**, and the F-fold box overdraw disappears (15 passes become 1). Cost independent of system count and faction count. Estimate: shell drops to 0.2 to 3 ms from tens of ms on a mid GPU.

Risk to the look: low to medium. Surface becomes slightly softer or lumpier at voxel scale; bisection is no longer needed for terracing; seam glow and gap suppression are baked so they must be recomputed in the bake (it also fixes the stale-rival bug of section 1.4); nested surfaces of two factions along one ray merge into one winner surface.

Why first: it removes the O(n) per-pixel loop entirely, it preserves the existing look so it needs no design decision, and the same voxel grid is the input for recommendation 2.

### 2. Bake the iso-surface to a low-poly mesh (surface nets or marching cubes) on territory change. Medium to large effort, best long-term fit.

What: one `ArrayMesh` per faction from the baked grid, flat or lightly smoothed shading, ordinary transparent material (no raymarch at all). Estimated 20k to 40k triangles for the whole galaxy at 2-unit voxels.
Expected gain: shell cost becomes vertex plus blend (under 1 ms on any discrete GPU, estimate), also works on weak iGPUs. This matches the owner's low-poly aesthetic natively. Risk: the look changes from smooth metaballs to faceted shapes (a design decision for Westley); transparent self-overlap needs a depth pre-pass or cull-front/back ordering to look clean. Effort medium to large (surface nets about 80 lines of GDScript or C; marching cubes needs tables).

### 3. Quick constants while 1 or 2 are built (small effort, factor 2 to 5 combined).

- `SHELL_RES_DIVISOR` 2 to 3 (640x360, 2.25x fewer pixels) or 4 (480x270, 4x). The bubbles are soft translucent shapes with low alpha (0.05 to 0.5), so the loss is mostly silhouette crispness. Risk: shimmer at edges when upscaled linearly. Effort: one constant.
- Steps 52 to 32 (1.6x on the march and the bisection becomes more important). The smallest bubble has an iso radius of about 4.2 units (0.4 x r, r at least 10.4), so a step up to about 3 units is safe: 32 steps over a 100-unit chord is 3.1 units, borderline; use 36 to 40 with jitter if shimmer appears. Risk: thin tips may flicker.
- Replace `texture(...)` with `texelFetch(...)` or `textureLod(..., 0.0)` in both loops: avoids implicit derivative/LOD maths in a non-uniform loop; modest gain (estimate 1.1x to 1.3x, uncertain), no look change.
- Optional: skip the SubViewport render on frames where neither camera nor territory changed.

### 4. If the baked field is not wanted: ray/sphere candidate culling in the shader (medium effort, 5x to 10x).

First pass over systems does a cheap ray/sphere (radius r) test and keeps up to about 16 hits in a local array; the march and the 11 hit-tail evaluations then loop only over those. This turns 52 x N_o + 11 x n into n + 52 x K + 11 x K (K about 6 to 12). Merge all factions into one pass or the rival candidate pass costs n x (F - 1) fetches per pixel. Risk: low look change, moderate shader complexity (register pressure with up to 15 factions).

### 5. Filaments into one merged mesh with ribbons (medium effort, big CPU win).

Replace the 402/800 tube meshes by one `ArrayMesh` (one draw call) of camera-facing ribbons (2 vertices per ring: 34 vertices, 32 triangles per edge versus 153 / 256) with per-vertex color and an edge id; hover/pin emphasis and the band alpha go in as one uniform plus one small data texture indexed by edge id (or vertex CUSTOM). Gain: draws 800 to 1, triangles 205k to 26k, per-frame `set_shader_parameter` calls 1,600 to a few. Estimate 1 to 3 ms CPU and about 1 ms GPU saved at 400 systems. Risk to look: low (the lines are sub-pixel to 2 px wide); keep UV.x for dash and shimmer. Effort medium.

### 6. GDScript per-frame work (small effort, 1 to 2 ms CPU).

`update_view` rewrites every point color and every filament emphasis every frame. Recompute only when the band weight, focus, hover or pin changes (dirty flag); cache owner color per faction; set label modulate only when the target alpha changes (each write queues a Label3D mesh rebuild); drop the duplicate per-edge parameter writes in `constellation._process` when the target alpha has not changed. `pick_at` should compare squared distances in screen space and early-out. Estimate 1.1 ms now, about 2.5 ms at 400/800.

### 7. Ambient: more and further stars cheaply (small to medium effort, no GPU risk).

Replace the 2,000-particle static starfield and the dust with one static `ArrayMesh` of 20k to 100k points or quads (one draw), animating in the vertex shader from `TIME` and vertex id (rings, streams and drift need no particle system). Draw cost linear in vertices (100k quads is 400k vertices, estimate 0.1 to 0.3 ms on a mid GPU). Keep size constant in screen pixels so far stars stay readable. Effort small for stars, medium to also fold the 12 ring emitters into one.

### 8. LOD by zoom band (small effort, modest gain).

Use `visibility_range` or alpha thresholds to hide trade filaments at overview (their alpha is 0.3 there and they are sub-pixel), hide particle rings that are off-screen, and drop point-sphere detail (6x4). Estimated draws 470 to about 250 at overview. Does nothing for the shell.

### 9. Leftovers (negligible individually).

Delete the unused DirectionalLight3D; render points opaque; fold the 17 grid surfaces into one; replace `own_world_3d` shell viewport only if recommendation 2 lands (the viewport then goes away).

### What I would do first

Recommendation 1: bake the field into one 3D texture and march it in one pass. Reasons: the shell is the only cost that is both large (about 6 G iterations per frame today, about 13 G at 400 systems, an order of magnitude over everything else in this scene) and unbounded as the galaxy grows (own march linear and rival march quadratic in system count); the bake removes both and the F-fold box overdraw; and it keeps the look so no design sign-off is needed. Everything else in this list combined does not move the frame time on a mid GPU as much as this one change.

## 7. What cannot be known without a real GPU run, and the measurement to take

Unknown from here: the real cost per iteration (texture-unit rate for point-sampled RGBA32F with uniform addresses versus ALU), whether the driver unrolls or spills the 52-step plus eleven-evaluation loops, shader compile time and register pressure (the Windows build uses the D3D12 driver per `project.godot`, whose compiler differs from Vulkan), warp divergence on the `own >= 0.3` branch, whether the SubViewport pass costs more in setup than in fill, and real draw-submission cost of 470 to 900 draws on the owner's CPU. All GPU millisecond figures above are estimates.

Measurement for the owner (Windows, the project's D3D12 Forward+ build), three camera positions, same seed (11) each time:

1. Overview: distance 120 (scroll out to the maximum), default pitch.
2. Regional default: distance 25 (the startup distance; or run the QA step `["call", "qa_camera", 25, -1]` from `scenes/mockups/galaxy/qa/focus.json`).
3. Close: distance 7.5 (maximum zoom in), focused on a faction-0 system (`["call", "qa_camera", 7.5, <system id>]`).

At each position: turn off vsync (Project Settings > Display > Window > V-Sync mode = Disabled, or launch with `--disable-vsync`), then read:

- **Debugger panel > Visual Profiler** (Debugger bottom panel, tab "Visual Profiler", press Start): it lists CPU and GPU milliseconds per render step and per viewport; the shell SubViewport is reported separately from the main viewport, so "GPU time of the shell viewport" is one line. This is the single most useful reading.
- **Debugger > Monitors** (Video group), or `Performance.get_monitor(...)`: `Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME`, `RENDER_TOTAL_PRIMITIVES_IN_FRAME`, `RENDER_TOTAL_OBJECTS_IN_FRAME`, `RENDER_VIDEO_MEM_USED`, plus `TIME_PROCESS` (script and process time) and `TIME_FPS`. Compare draw calls to the 470 estimate.
- Per-viewport GPU time from a script: `RenderingServer.viewport_set_measure_render_time(vp_rid, true)` then each frame `RenderingServer.viewport_get_measured_render_time_gpu(vp_rid)` with `vp_rid = $World/GalaxyView/ShellRenderer/<SubViewport>.get_viewport_rid()` (and the same call on the root viewport RID for the rest of the scene).

A/B toggles to isolate cost (frame time with vsync off, at each of the three positions): (a) full scene; (b) shell hidden (`_overlay.visible = false` and `_sub_viewport.render_target_update_mode = UPDATE_DISABLED`), so (a) minus (b) is the shell's total cost; (c) ambient rig hidden; (d) filaments hidden; (e) `SHELL_RES_DIVISOR = 4`, which should drop the shell cost about 4x if it is fill-bound and not at all if it is something else (which would falsify the model). Record milliseconds, not fps. If (a) minus (b) at the regional position is near the 30 to 60 ms my table gives for an upper-mid card, the model is right; if it is a fraction of that, per-iteration throughput is higher than assumed and the real-game number scales down by the same factor.

Also worth reading once: shader compile hitch on first show of the shell (first-frame time), because the loops are inlined about 14 times.

## 8. Method notes and limits

- Emulation fidelity: same loop structure, same early exits, same gating; field maths in double precision on the CPU, so a few boundary rays may differ from the GPU. It does not model warp divergence (rival evaluation on a few rays holds a whole warp at that cost; the real rival term may be up to 1.5x higher), trilinear cost, or caches.
- The real-game galaxy is synthetic (nearest-capital territories, 85% owned, kernel radius 14); the real game's spacing, kernel radius and territory shapes are not in this branch, so treat the 22k to 25k per pixel as plausible rather than exact.
- I did not modify any tracked file. `git status` in the worktree already showed many `.import` files modified before my first Godot run (Godot rewrites those when it opens the project); I did not touch them.
