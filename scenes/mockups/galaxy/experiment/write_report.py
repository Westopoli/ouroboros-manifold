#!/usr/bin/env python3
import make_report as M, os
here = os.path.dirname(os.path.abspath(__file__))
m = M.L("matrix")["runs"]; best = M.L("best")["runs"]
txt = f"""# Galaxy field-bake experiment: is a baked 3D field fast enough for the bubbles?

Throwaway measurement experiment. Branch `push/galaxy-field-experiment` (from `push/mockup-galaxy-scale` 9404a62b). Everything is under `scenes/mockups/galaxy/experiment/`; the only outside edit is a default-off generator hook in `galaxy_gen.gd` (`exp_system_count`, `exp_faction_count`, `exp_min_spacing`, all 0 = unchanged; the default galaxy for seed 11 still reports 219 systems / 402 edges / 4 factions as in the audit).

Labels: **measured** = read from the GPU timestamps or counted in this run. **derived** = computed from measured numbers (formula stated). **estimated** = my guess.

## Short answer

- **Yes, a baked field is fast enough, with a large margin.** At 400 systems / 15 factions, 1920x1080, RTX 3060, the field renderer's GPU time is **0.49 to 0.50 ms** at half-resolution (64 steps, 4 crossings, 96^3 grid) at all four camera positions (measured), and **1.85 to 1.91 ms at full 1080p** with the same settings (measured). The old shader costs **75 to 138 ms** at the same galaxy size (measured). The 2.0 ms target is met at every position by both, but the full-resolution variant only by 0.09 ms (see "Target check").
- Cost does **not** grow with system or faction count: the same settings on the default galaxy (219 systems / 4 factions) measure 0.46 to 0.50 ms (half-res) and 1.80 to 1.94 ms (full-res).
- The look is close to the old one but not identical: the field renderer shows more layered structure (see "Look").

## How it was run

- Device: **NVIDIA GeForce RTX 3060** (Godot reports it in every result file under `meta.device`; startup log: `Vulkan 1.4.329 - Forward+ - Using Device #0: NVIDIA - NVIDIA GeForce RTX 3060`). Godot 4.6.3, Forward+, 1920x1080, vsync disabled.
- **Window-free**: `run_probe.sh` starts an Xvfb virtual display (`:77`) and runs Godot with `--rendering-driver vulkan --rendering-method forward_plus --disable-vsync`. It worked on the first try; no window ever opened on the owner's desktop. (The machine's `godot` wrapper passes through to the x11 driver when DISPLAY is an Xvfb display.)
- GPU time per viewport: `RenderingServer.viewport_set_measure_render_time` + `viewport_get_measured_render_time_gpu`, 60 warm-up draws then 120 recorded draws per camera position (median, p95 reported). Draw calls from `Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME`.
- **Two measurement choices you should know about** (both forced by problems I hit):
  1. Presented frames under Xvfb take 60 to 130 ms each (the driver copies every frame to the X server), so wall-clock frame time is meaningless here, and the GPU sat ~90% idle between frames and dropped to 200 to 900 MHz. Light workloads then read up to ~15x too slow (an unmodified scene read 7 ms instead of 0.4 ms). The probe therefore renders **back to back with `RenderingServer.force_draw(false)` (no present)**, which keeps the GPU at 1850 to 1957 MHz (clock recorded per position in the JSON; positions where it was lower are flagged).
  2. For the field renderer the probe draws the full-screen pass `reps` times per frame (4 to 16) and divides the viewport time by `reps`, so even 0.1 ms passes keep the GPU saturated. Cross-check: total `force_draw` wall time matches `main + reps x field` (e.g. 5.5 ms for 0.46 + 8 x 0.63). Screenshots are always taken with `reps = 1`.
- `Performance.TIME_PROCESS` is recorded in the JSON but is polluted by the Xvfb present stall (60 to 700 ms); do not use it.
- Another process (`ollama`) holds 10.4 GB of VRAM but was idle (1% utilisation).

## Baseline (old shader), measured

Shell cost = shell viewport GPU time + (main viewport time with shell on minus off). Shell-off main-viewport readings taken at low GPU clock are unreliable (flagged); the correction term is below 0.1 ms either way. The shell is the whole story: the rest of the frame (main viewport: 103 to 872 draw calls of filaments, points, particles, HUD) takes 0.34 to 0.5 ms.

{M.baseline()}

Draw calls (measured, median): default galaxy 477 / 195 / 108 / 301 and 400-system galaxy 888 / 313 / 397 / 513 at the four positions; the shell adds 5 to 16.

## Field bake

Grid covers the galaxy ball plus one influence radius: cube from -64 to +64 per axis (128 units). Per cell it stores best `net` over factions (R), that faction's rival term (G), faction id (B) as an RGBAH 3D texture (A unused). Formulas are the shader's: kernel `(1 - d^2/r^2)^3`, `r = R*(0.6 + 0.4*sig)`, own = sum, rival = max single kernel over other factions, `net = own*(1 - gap*smoothstep(0.3, 1.0, rival/own))` with `gap = 0.5` (the value `legacy_shell_renderer.gd` actually sets; the shader's default 0.8 is never used).

Two deliberate differences from the old code, both small: (a) one pass over the systems per cell serves every faction (per-faction sum and max, rival = best max among the other factions) instead of two loops per faction; the maths is identical. (b) Each system's significance is normalised by its **own** faction's maximum, whereas the old code normalised rivals by the *evaluating* faction's maximum (a quirk: faction 0's capital has significance 1.0, the others 0.85). This changes rival radii only between faction 0 and the others, by a few percent.

**GPU fill works** (no CPU fallback was needed): a SubViewport (`use_hdr_2d`, RGBA16F) with a canvas shader draws the cells as slices into a slice atlas (64^3: 8x8 slices; 96^3 and 128^3: 16 columns), the atlas is read back with `get_image()` and sliced into an `ImageTexture3D` (RGBAH, linear filtering). Verified against an independent numpy re-bake of the same formulas: max abs difference 0.00098 (half-precision rounding at values near 1), faction id agrees on 100% of 3,000 sampled inside cells, for every grid size and both galaxies.

{M.bake()}

- GPU bake pass is **derived**: the canvas-only SubViewport reports no viewport GPU time, so I compared steady-state back-to-back `force_draw` loops with and without re-running the bake each iteration (100 iterations each). It is 0.36 to 4.2 ms.
- Wall time is **measured** (draw + `get_image` readback + slicing + `ImageTexture3D.create/update`). Readback and CPU upload dominate, not the GPU pass. The default galaxy at 96^3 (11 ms) is slower than the big galaxy at 96^3 (7 ms) in every repeat; I did not find out why.
- **Refill after one owner change** is measured as a full re-run of the same pass (one system flipped from faction 0 to 1, data verified to change): same cost as a full fill, 2 to 16 ms. I did not implement a dirty-region-only draw; one would cut only the GPU pass (a 28-unit dirty cube is about 1% of the 128-unit volume, **estimated** 0.01 to 0.05 ms) and not the readback/upload that dominate. `ImageTexture3D` cannot be updated partially. A `Texture3DRD` written by compute would avoid the readback; not tried.
- Skip-grid build (16^3 block maxima, CPU GDScript from the readback) is 32 to 351 ms: too slow for per-conquest rebuild in GDScript; the GPU pass could produce it instead (not done).
- Texture memory: as built RGBAH is 8 bytes per cell (2.0, 6.75, 16.0 MiB for 64/96/128). Packing field as RG16F plus a separate R8 id texture would be 5 bytes per cell (1.25, 4.22, 10.0 MiB) (**derived**; not built: the id is read with `texelFetch` from the same texture instead, which is equivalent to a nearest-filtered id texture). Skip grid 16^3 R32F = 16 KiB.

## Field renderer

`field_march.tmpl` + `field_renderer.gd`: one full-screen quad in a SubViewport (own world, transparent, composited with the same premultiplied `TextureRect` on a CanvasLayer as the old shell). Per pixel: ray against the grid cube; fixed `STEPS` filtered fetches; blends up to `CROSS` surface crossings front to back (an entering crossing = below to above the 0.6 iso, a camera that starts inside a bubble counts as a crossing at the start); per crossing `REFINE` bisection fetches, a 4-tap tetrahedral gradient normal, faction id by `texelFetch`, colour from a 16-entry palette, and the old shader's rim, seam-glow and alpha maths verbatim. Early out when 4 crossings are blended or transmittance < 0.02. Optional 16^3 skip grid (block max, widened by one cell); a ray in an empty block jumps to the block exit. Like the old shader (unshaded), only `ALBEDO` reaches the output; `EMISSION` is ignored in both. No depth write (nothing else is drawn inside the shell viewport).

## Measurement matrix (400 systems / 15 factions, 1920x1080, GPU ms of the field viewport per pass, median; **measured**)

Centre point: grid 96, 64 steps, divisor 2, skip on, 4 crossings, refine 2, one thing varied at a time. The shell composite on the main viewport (a full-screen textured quad) is not separable from noise (main viewport 0.42 to 0.48 ms with the field overlay on, 0.34 to 0.38 ms lowest seen with the shell off): at most about 0.1 ms.

{M.table(m)}

Findings from the matrix:
- Grid size (64 / 96 / 128) makes no measurable difference to cost (0.60 to 0.63 ms); it only changes accuracy and memory.
- Steps scale cost linearly: 32 / 64 / 96 steps = 0.39 / 0.63 / 0.86 ms at half-res. 32 steps shows streak artefacts in the overview (see Look).
- Divisor scales cost with pixel count: 1 / 2 / 4 = 2.4 / 0.63 / 0.17 ms.
- **The skip grid does not help in this galaxy**: it saves 16% at distance 120 (0.42 vs 0.50 ms) and costs 25% elsewhere (0.62 vs 0.50 ms), because 400 systems fill the ball and the extra fetch plus divergence outweighs the few empty blocks. The audit predicted 30 to 60% fewer steps; not seen at 16^3.
- Crossing count matters most: 1 crossing is 0.08 to 0.22 ms against 0.60 for 4 (rays that hit early stop). The cheap settings were measured on a GPU that was not quite saturated even with `reps = 8`, so they may be slightly overstated.
- Refine steps (0 / 2 / 4): 0.60 / 0.63 / 0.66 ms.
- Default galaxy at the centre point: 0.38 / 0.59 / 0.40 / 0.61 ms against 0.42 / 0.63 / 0.63 / 0.62 on the big one. The 0.40 vs 0.63 at distance 7.5 is a coverage difference (which bubbles are in view), not a count effect. Cost is independent of system and faction count to within that.

### Best combinations (same galaxy, **measured**)

{M.table(best)}

**Best variant: `b_half64`** (grid 96, 64 steps, divisor 2, skip off, 4 crossings, refine 2): **0.50 ms at every position**, same fidelity settings as the centre point, 150x to 280x cheaper than the old shader at the same resolution (75 to 138 ms). **Full resolution: `b_full64`** (same, divisor 1): **1.85 to 1.91 ms**. Cheapest usable: `b_q64` (divisor 4) 0.13 to 0.15 ms; `b_half32_c2` (32 steps, 2 crossings) 0.15 to 0.25 ms (not inspected visually; 32 steps showed streak artefacts in the matrix screenshots).

### Target check: 2.0 ms shell GPU time at every position, 400 systems / 15 factions

- `b_half64`: **met**, 0.50 ms worst median (0.53 ms worst p95).
- `b_full64` (full 1080p): **met, narrowly**: 1.91 ms worst median, 1.98 ms worst p95. Adding the composite (at most about 0.1 ms, not separable) puts the true total between 1.91 and about 2.0 ms, so treat it as at the limit, not comfortably under. 96 steps at full-res (2.64 ms) and the centre point at divisor 1 with the skip grid (2.43 ms) **miss** the target. The 2.0 ms target was not loosened.
- What limits full-res: cost scales with steps x pixels and not with grid size (derived: 64 steps x 2.07 M pixels = 133 M filtered fetches in 1.9 ms, about 70 G fetches/s, plus the crossing work; consistent with texture-fetch throughput, which I did not confirm with a profiler).

## Accuracy (first surface along 2,000 random rays, grid with linear filtering on the CPU vs exact formulas; **measured**)

Rays start on a sphere of radius 95 and aim at random points inside radius 45 (so they cross the galaxy); both sides sample every 0.25 units and refine the crossing by 22 bisection steps. "Error" is the distance along the ray between the two first-surface positions. Median, p95 and worst are over rays where both found the same surface (within 1 unit); the rays where they did not are counted separately (grazing hits of thin features that one side samples and the other does not; the gap there is the distance to the next surface, tens of units).

{M.accuracy()}

Reading: 96^3 puts the surface within 0.05 to 0.07 units (median) of exact, about 0.2 units at p95, which is about 0.6 px median and 2.5 px at p95 at the overview (11 px per unit at distance 120). When zoomed in (174 px per unit at distance 7.5) the same 0.05 units is about 9 px, but that is a smooth change of surface shape, not a visible artefact by itself. 64^3 doubles the error and picks a different first surface on 3% of rays; 128^3 halves it again. The smallest real bubble (normalised significance 0.35, iso radius 4.1) is never missed at any grid size and is round to within 0.3 / 0.13 / 0.07 units (64 / 96 / 128). Even an artificial significance-0 bubble (iso radius 3.3) is kept.

## Look (old shader versus field renderer, same seed)

Side-by-side montages (left old, right field, centre-point settings: grid 96, 64 steps, divisor 2, skip on, 4 crossings), in `results/look/`: `default_d120.jpg`, `default_d25.jpg`, `default_d7.5_f0.jpg`, `default_inside.jpg`, `big_d120.jpg`, `big_d25.jpg`, `big_d7.5_f0.jpg`, `big_inside.jpg`, plus `closeup_big_d7.5_crop.jpg` (full-resolution crop) and `variants_d120_steps32_centre_div4.jpg` (crops of 32 steps / centre / divisor 4). The full-resolution source screenshots are in `results/shots/` (`base_<galaxy>_on__<pos>.png` old, `m_centre__<pos>.png` and `m_centre_default__<pos>.png` field); they are not committed (size).

Differences I could see:
1. **More layering.** The old shader shows only the first surface of each faction; the field renderer blends up to four surface crossings of the combined field, so seams and second lobes of the same faction appear as extra translucent layers. At distance 120 and 25 it looks denser and more structured (visible ridges inside the large blobs); in the 400-system galaxy it is busier. This is the largest visible difference. It is a design choice (crossing rule), not a baking error; counting only the first crossing per faction id would reduce it.
2. **Colours, rim, seam glow, band opacity**: same palette and same maths; no missing seams or colour mismatch in the 6 comparisons I looked at (default: distance 25, 120, 7.5, inside; 400-system: distance 25 and a close-up crop at 7.5). Faction borders look the same.
3. **Camera inside a bubble**: both fill the screen with the owner's tint; the field render additionally shows more of the far faction layers (orange/brown regions at the lower right) than the old one at the same camera.
4. **Silhouettes**: both have the same half-resolution stair edges (divisor 2); no soft-blob difference visible at 96^3. At divisor 4 the result is blurrier but the shapes hold.
5. **Stepping artefacts**: at 32 steps the overview shows ragged streaks where thin parts are skipped; at 64 steps none visible; 96 not inspected.
6. **Creases from the filtered gradient**: none visible in the close-up at distance 7.5, but the local band's opacity is 0.05, so creases would be faint there anyway. I did not test close zoom at higher opacity; untested.
7. **Artefact seen**: a small black wedge/patch near the top of the distance-120 crops of the 400-system galaxy (present in every variant I looked at; I did not check the old shader's matching frame). Not investigated.

## What did not work, what I could not measure, contradictions with the audit

Did not work / limitations:
- The skip grid at 16^3 did not pay off (see above); finer or distance-based skipping not tried.
- Dirty-region GPU refill not built; the refill measured is a full re-run. No `Texture3DRD`/compute path, so every refill pays a GPU readback and CPU upload (2 to 16 ms).
- First attempts at timing were wrong and discarded: presented frames under Xvfb with an idle GPU (7 ms for a 0.4 ms scene) and a bake benchmark that ran before the canvas was committed (all-zero output, caught by checking the data). Final numbers are all from the corrected harness.
- The default-galaxy bake wall time anomaly (96^3 slower than on the bigger galaxy) is unexplained.

Could not measure:
- A real windowed run on the owner's display: presentation, compositor cost and frame pacing are not covered (GPU shader time is). Any other GPU: the 3060 only. Other clock states: results are for a saturated GPU at 1850 to 1957 MHz; at real game frame pacing the GPU may clock lower.
- CPU-side per-frame cost (`Performance.TIME_PROCESS` is polluted by Xvfb presentation).
- The shell composite cost separately (below the noise).
- Normal quality versus the old central differences; the colour of every pixel (only eyeballed).

Contradictions with, or confirmations of, the audit:
- **Confirmed**: the shell is the dominant cost by far (36 to 138 ms against 0.34 to 0.5 ms for the rest of the frame).
- Audit's old-shader estimate for the 3060 was 30 to 60 ms (default, regional) and 65 to 130 ms (400/15): measured 59.5 ms and 138 ms, so the real cost is at the top of the first range and slightly above the second.
- Audit said old cost does not fall when zoomed in: measured it does fall somewhat (distance 7.5: 41 / 103 ms against 60 / 138 ms at distance 25), but not at all inside a bubble (56 / 137 ms).
- Audit estimate for a baked 96^3 field was 1 to 2 ms full-res and 0.3 to 0.6 ms half-res on the 3060: measured 1.9 and 0.5 ms. **Confirmed.**
- Audit predicted the skip texture would cut steps by 30 to 60%: measured slower in 3 of 4 positions.
- Audit's draw-call estimate (about 470 for seed 11): measured 477 at distance 120 but 108 to 301 at the other positions (culling), and 313 to 888 for 400 systems.

## Files

`probe.gd`, `probe.tscn`, `run_probe.sh` (harness); `field_bake.gd` (GPU fill); `field_march.tmpl`, `field_renderer.gd` (renderer); `accuracy.py` (accuracy, numpy, run with the repo `.venv`); `make_report.py`, `write_report.py` (tables); `cfg_*.json` (run configs); `results/*.json` (raw numbers, every file has `meta.device`); `results/look/` (montages).
"""
open(os.path.join(here, "REPORT.md"), "w").write(txt)
print(len(txt))
