# Main Menu — Particle Galaxy Structure

> **Staged implementation plan.** This document covers the full vision across four stages (A–D). Only Stage A should be implemented first. Each subsequent stage builds on the previous and has its own verification checklist.
>
> **Relationship to previous spec:** This replaces Layer 1 (Slow Celebration Loop) from `main_menu_animation_spec.md`. Layer 2 (Departure Board Heartbeat) and Layer 3 (Menu Item Reactivity) remain unchanged. The `starfield.gdshader` background is removed — the 3D particle structure IS the background now.
>
> **Lineage:** The particle system descends from `fate_space.gd` (the previous game's psychohistory visualization). Same core tech (`GPUParticles3D`, billboard quads, additive blending), but restructured from an amorphous attractor-based galaxy into a geometric sandogram — concentric rings, radial streams, and structured orbital paths. This structure will later serve as the foundation for the world view during inter-mission time jumps (faction borders rendered as colored regions within the particle field).

---

## Vision

When the player opens Ouroboros Manifold, behind the menu text they see a slowly rotating structure made of thousands of tiny gold-white luminous particles. The structure resembles a psychohistory projection from Asimov's Foundation — a sandogram, an astrolabe, a mathematical model of a galaxy rendered in light. Concentric rings of particles orbit at different speeds. Radial streams of particles flow inward along geometric paths. A bright central point pulses slowly.

A camera moves through this structure autonomously — sometimes pulled back to reveal the full disc shape, sometimes close enough that individual particle streams rush past the viewport. The effect is meditative and cinematic. It never demands attention, but it rewards a lingering glance.

The particle color is predominantly **light gold** — warm but luminous, like distant stars. The brand accent gold (`#D4A017`) is the baseline hue, brightened toward white for the particles themselves. Think `Color(1.0, 0.88, 0.5)` — a pale gold that reads as "warm starlight" rather than "yellow." A minority of particles (10–15%) are cooler blue-white for depth and contrast.

---

## Particle Budget Strategy

The goal is intricate and detailed with excellent performance. The approach: **multiple smaller GPUParticles3D nodes** rather than one massive emitter. This gives independent control over each structural element (rings, streams, ambient dust) and lets us tune density per-element. It also means we can disable individual elements on lower-end hardware without redesigning the whole system.

**Budget breakdown:**

| Element | GPUParticles3D nodes | Particles per node | Total particles | Notes |
|---|---|---|---|---|
| Ring A (inner) | 1 | 800 | 800 | Tightest orbit, fastest rotation |
| Ring B (mid) | 1 | 1,200 | 1,200 | Primary visual ring, most particles |
| Ring C (outer) | 1 | 1,000 | 1,000 | Widest orbit, slowest rotation |
| Radial streams | 1 | 600 | 600 | Inward-flowing geometric paths |
| Ambient dust | 1 | 400 | 400 | Sparse background fill |
| Central glow | 1 | 200 | 200 | Dense cluster at the center |
| **Total** | **6** | — | **4,200** | — |

**Why this works:** Your fate_space ran 3,250 + 260 = 3,510 particles with attractors, turbulence, and full `_process()` per-frame logic, and it was performant. This budget is ~20% higher in raw count but simpler per-particle (no attractors, no turbulence — particles follow fixed orbital paths via custom particle shaders). The draw cost is dominated by the billboard quad overdraw (additive blending), which scales with screen coverage not particle count. Since most particles are tiny (0.15–0.25 world units), overdraw is minimal even at 4,200 particles.

**Scalability lever:** If performance is tight, the ambient dust (400) is the first cut. Then reduce Ring C to 600. The structure reads clearly with as few as 2,800 particles.

---

## Stage A — Static Particle Structure

**Goal:** The geometric particle structure renders correctly in 3D space with a fixed camera. No camera movement yet. All rings orbit, streams flow, central point pulses. Visually complete but cinematically static.

### File Structure

```
scenes/main_menu/
```
scenes/shared/galaxy/
├── galaxy_structure.tscn           (3D scene: camera + particle structure)
├── galaxy_structure.gd             (public API + structure builder + camera)
├── ring_particles.gdshader         (custom particle shader for orbital motion)
├── stream_particles.gdshader       (custom particle shader for radial inflow)
└── dust_particles.gdshader         (custom particle shader for ambient drift)
```

### Architecture: SubViewport Rendering

The 3D particle structure renders in a `SubViewport` that feeds a `TextureRect` behind the 2D menu content. This cleanly separates 3D and 2D rendering.

```
main_menu.tscn
├── TextureRect (galaxy_bg)           ← Displays SubViewport texture, fills screen
│   └── SubViewportContainer
│       └── SubViewport (galaxy_viewport)
│           └── GalaxyStructure (instanced from scenes/shared/galaxy/galaxy_structure.tscn)
│               ├── Camera3D
│               ├── RingA (GPUParticles3D)
│               ├── RingB (GPUParticles3D)
│               ├── RingC (GPUParticles3D)
│               ├── RadialStreams (GPUParticles3D)
│               ├── AmbientDust (GPUParticles3D)
│               ├── CentralGlow (GPUParticles3D)
│               ├── CentralPoint (MeshInstance3D — emissive sphere)
│               └── GridPlane (MeshInstance3D — faint concentric circles)
├── MenuTitleHeartbeat (Control)      ← Layer 2, z_index -1
├── MenuContent (Control)             ← Layer 3, existing menu layout
└── ScanlineOverlay (CanvasLayer)
```

**SubViewport settings:**
- `size`: Match window resolution (bind to window resize signal).
- `transparent_bg`: `true` — the galaxy renders on a transparent background, so the `BASE` color (`#0A0D12`) shows through from the main scene. This means sparse areas of the particle field naturally show the menu background color.
- `render_target_update_mode`: `ALWAYS`.
- `msaa_3d`: `OFF` — additive-blend particles don't benefit from MSAA, and it's expensive.
- `use_hdr_2d`: `false`.

**TextureRect settings:**
- `stretch_mode`: `KEEP_ASPECT_COVERED`.
- `modulate`: `Color(1, 1, 1, 0.7)` — dials the entire galaxy to 70% opacity so it sits behind the menu text without competing. Tunable.

### The Structure: Geometry and Dimensions

The particle structure occupies a disc ~100 world units in diameter, centered at the origin, primarily on the XZ plane (flat disc, like a galaxy viewed from slightly above). The disc has a slight vertical thickness (~8 world units) so particles don't appear paper-thin from oblique angles.

**Coordinate system:**
- Origin: center of the structure, center of the central glow.
- XZ plane: the disc plane. Rings orbit in this plane.
- Y axis: vertical. Camera elevation is measured from this plane.
- Scale: 1 world unit ≈ 1 conceptual unit. The full structure spans roughly -50 to +50 on X and Z.

#### Central Point

A `MeshInstance3D` with a `SphereMesh` (radius 1.5, 32 segments) and an emissive `StandardMaterial3D`:
- `albedo_color`: `Color(1.0, 0.95, 0.75, 1.0)` — warm white-gold.
- `emission_enabled`: true.
- `emission`: `Color(1.0, 0.90, 0.55)` — gold.
- `emission_energy_multiplier`: `2.5`.
- `shading_mode`: `UNSHADED`.

The sphere pulses in scale: `1.0 + sin(time * 0.8) * 0.08` — very subtle breathing. Driven by a Tween loop, not `_process()`.

#### Central Glow (GPUParticles3D)

200 particles in a tight sphere (emission radius 3.0) around the origin. These create a dense luminous haze around the central point.

- `emission_shape`: `SPHERE`, radius `3.0`.
- `initial_velocity`: `0.3–1.0` (very slow drift).
- `damping`: `2.0–4.0` (particles decelerate quickly, staying near center).
- `gravity`: `Vector3.ZERO`.
- Lifetime: `6.0s`.
- Quad size: `0.3 × 0.3` (slightly larger than ring particles for glow effect).
- Color: `Color(1.0, 0.92, 0.6, 0.6)` — bright warm gold, semi-transparent.
- Material: additive blend, unshaded, billboard.

#### Ring A — Inner Ring

800 particles orbiting at radius **12–16** world units. This is the fastest, tightest ring.

**Implemented via custom particle shader** (`ring_particles.gdshader`). The shader assigns each particle an orbital position based on its `INDEX` and `TIME`:

```
// Conceptual shader logic (actual syntax in implementation)
float angle_offset = float(INDEX) / float(TOTAL) * TAU;  // Evenly spaced start
float orbit_radius = RADIUS_MIN + hash(INDEX) * (RADIUS_MAX - RADIUS_MIN);  // Slight radius variation
float orbit_speed = BASE_SPEED + hash(INDEX + 1000) * SPEED_VARIATION;  // Slight speed variation
float angle = angle_offset + TIME * orbit_speed;

// Slight vertical offset for disc thickness
float y_offset = (hash(INDEX + 2000) - 0.5) * DISC_THICKNESS;

TRANSFORM[3].xyz = vec3(cos(angle) * orbit_radius, y_offset, sin(angle) * orbit_radius);
```

**Ring A parameters:**
- Radius: `12.0–16.0` (randomized per particle).
- Orbit speed: `0.15–0.25 rad/s` (one full revolution every ~25–42 seconds).
- Disc thickness (Y scatter): `±2.0`.
- Particle count: `800`.
- Lifetime: `1000.0s` (effectively infinite — particles persist and orbit continuously).
- Quad size: `0.15 × 0.15`.
- Color: 85% warm gold `Color(1.0, 0.88, 0.5, 0.85)`, 15% cool blue-white `Color(0.7, 0.8, 1.0, 0.7)`. The shader picks color based on `hash(INDEX + 3000) < 0.15`.
- Material: additive blend, unshaded, billboard.
- Emission energy: `3.0` (bright enough to read as luminous points).

#### Ring B — Mid Ring

1,200 particles at radius **24–32** world units. The primary visual ring — densest, widest, most visually prominent.

**Same shader as Ring A**, different uniforms:
- Radius: `24.0–32.0`.
- Orbit speed: `0.08–0.14 rad/s` (slower — one revolution every ~45–78 seconds).
- Disc thickness: `±3.0` (slightly thicker band).
- Particle count: `1,200`.
- Quad size: `0.18 × 0.18` (slightly larger since farther from center).
- Color: same 85/15 gold/blue split.
- Emission energy: `2.5`.

#### Ring C — Outer Ring

1,000 particles at radius **38–48** world units. The outermost edge of the structure. Sparser, slower, defines the boundary.

- Radius: `38.0–48.0`.
- Orbit speed: `0.04–0.08 rad/s` (slowest — one revolution every ~78–157 seconds).
- Disc thickness: `±4.0`.
- Particle count: `1,000`.
- Quad size: `0.2 × 0.2`.
- Color: same split, but gold particles are slightly dimmer: `Color(1.0, 0.88, 0.5, 0.65)`.
- Emission energy: `2.0`.

#### Radial Streams

600 particles flowing **inward** along 6 evenly-spaced radial lines (every 60°). These create the geometric "sandogram" character — visible lines of particles moving toward the center like spokes of a wheel.

**Custom shader** (`stream_particles.gdshader`). Each particle is assigned to one of 6 streams based on `INDEX % 6`. Within each stream, the particle starts at the outer edge and flows inward:

```
// Conceptual logic
int stream_id = INDEX % 6;
float stream_angle = float(stream_id) / 6.0 * TAU;

// Particle's position along the stream (0.0 = outer, 1.0 = center)
float progress = fract(TIME * FLOW_SPEED + hash(INDEX) * 1.0);  // Continuous loop
float radius = mix(OUTER_RADIUS, INNER_RADIUS, progress);

// Slight perpendicular scatter so streams aren't 1px thin lines
float scatter = (hash(INDEX + 5000) - 0.5) * STREAM_WIDTH;
vec3 stream_dir = vec3(cos(stream_angle), 0.0, sin(stream_angle));
vec3 perp = vec3(-stream_dir.z, 0.0, stream_dir.x);
float y_scatter = (hash(INDEX + 6000) - 0.5) * 1.5;

TRANSFORM[3].xyz = stream_dir * radius + perp * scatter + vec3(0.0, y_scatter, 0.0);
```

**Stream parameters:**
- Outer radius: `45.0`.
- Inner radius: `5.0` (particles fade near center, don't pile up).
- Flow speed: `0.06` (each particle traverses the full stream in ~16 seconds).
- Stream width (perpendicular scatter): `±1.5` world units.
- Particle count: `600` (100 per stream).
- Quad size: `0.12 × 0.12` (smaller — these are fast-moving, should feel like streaks).
- Color: `Color(1.0, 0.92, 0.65, 0.7)` — slightly brighter gold than rings.
- Opacity fades near inner radius (last 20% of travel) to avoid center pile-up.
- Emission energy: `2.5`.

**The 6 streams rotate slowly as a group** — the entire stream structure rotates at `0.02 rad/s` (one revolution per ~5 minutes). This means the streams visually sweep across the ring particles, creating slow interference patterns. Implemented by rotating the parent `Node3D` of the stream `GPUParticles3D`.

#### Ambient Dust

400 particles scattered in a large sphere (radius 60) around the entire structure. These are the sparse background fill — visible when the camera is far out, providing context that the structure exists in space.

**Simple particle shader** (`dust_particles.gdshader`) — random positions in a sphere, very slow random drift:

- Emission shape: sphere, radius `60.0`.
- Initial velocity: `0.1–0.5` (barely moving).
- Damping: `0.5–1.0`.
- Lifetime: `20.0s` (long, slow cycle).
- Quad size: `0.1 × 0.1` (tiny).
- Color: 50% dim gold `Color(1.0, 0.88, 0.5, 0.3)`, 50% dim blue `Color(0.6, 0.7, 1.0, 0.2)`.
- Emission energy: `1.5`.
- This can use a standard `ParticleProcessMaterial` instead of a custom shader — it's simple enough.

#### Grid Plane

Reused directly from your fate_space code (lines 463–499). Concentric circles + radial lines drawn with `ImmediateMesh` on the XZ plane at `y = -5.0` (slightly below the disc). Very low opacity (`0.03–0.05` alpha). Color shifted to match the new palette: `Color(0.8, 0.75, 0.55, 0.04)` — faint warm tone instead of the blue-gray from fate_space.

5 concentric rings at radii 10, 20, 30, 40, 50. 12 radial lines. This creates the "astrolabe" geometric underlay that gives the particle structure mathematical character.

### Particle Quad Material (Shared)

All particle quads share the same material pattern from fate_space, adapted for the new color:

```gdscript
var quad_mat := StandardMaterial3D.new()
quad_mat.albedo_color = particle_color  # Per-element, set by shader or material
quad_mat.emission_enabled = true
quad_mat.emission = emission_color      # Per-element
quad_mat.emission_energy_multiplier = energy  # Per-element
quad_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
quad_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
quad_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
quad_mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
```

The additive blending is critical — it's what makes dense particle regions glow brighter (particles add their light together) and gives the structure its luminous quality.

### Initial Camera Position (Stage A — Static)

For Stage A only, the camera is fixed at a position that shows the full structure:

- Position: `Vector3(0, 45, 65)` — elevated, slightly in front.
- Look-at: `Vector3.ZERO` (center of structure).
- FOV: `50°`.

This gives a 3/4 view that reveals the disc shape, the rings, and the radial streams simultaneously. It's the "establishing shot" that proves the structure works before Stage B adds camera movement.

### Stage A Verification Checklist

- [ ] SubViewport renders the 3D scene correctly behind the 2D menu.
- [ ] Central point sphere renders with gold emission and subtle pulse.
- [ ] Central glow particles create a bright haze around the center.
- [ ] All three rings are visible as distinct orbital bands at different radii.
- [ ] Ring particles orbit smoothly — no jittering, no clumping, no visible seams in the orbit.
- [ ] Ring A orbits noticeably faster than Ring B, which orbits faster than Ring C.
- [ ] 6 radial streams are visible as lines of particles flowing inward.
- [ ] Stream particles fade near the center (no pile-up at origin).
- [ ] Stream structure rotates very slowly relative to the rings.
- [ ] Ambient dust particles are visible in the background, very faint.
- [ ] Grid plane is faintly visible beneath the disc.
- [ ] Color is predominantly light gold with occasional blue-white particles.
- [ ] Total particle count is ~4,200. FPS stays above 60 at 1920×1080.
- [ ] The `TextureRect` modulate at 0.7 opacity lets the menu text remain clearly readable.
- [ ] Layer 2 (title heartbeat) and Layer 3 (hover reactivity) still function correctly on top.
- [ ] Background color is `#0A0D12` in areas without particles.

---

## Stage B — Camera Choreography

**Goal:** The camera moves autonomously through the structure, creating a cinematic ambient background. Full 360° movement on all axes.

### Camera State Machine

The camera controller (`galaxy_structure.gd`) runs a state machine with 5 moods. Each mood defines a camera behavior pattern. Transitions between moods happen on a timer (20–45 seconds per mood, randomized). Transitions lerp position and rotation over 4–6 seconds.

#### Mood: Wide Orbit

The "establishing shot." Camera orbits the full structure at distance 70–90, elevation 25°–45°. Slow azimuth rotation at 0.015–0.025 rad/s. The full disc, all rings, and the central glow are visible. This is the mood the camera starts in.

Duration: 25–40 seconds.

#### Mood: Ring Follow

Camera drops to disc level (Y ≈ 2–5, within the disc thickness) at a radius matching Ring B (25–30 units from center). It tracks along Ring B's circumference, matching the ring's orbital speed. Individual ring particles stream past in the foreground, with the central glow visible ahead/behind. Stars from Ring C are visible in the distance.

This is the most immersive mood — the player is "inside" the galaxy.

Duration: 20–35 seconds.

#### Mood: Approach

Camera begins at wide orbit distance and slowly moves toward the center over the mood's duration. As it approaches, the particle density increases — Ring C passes by, then Ring B, then Ring A. The central glow grows brighter. The camera stops at distance ~15 (just outside Ring A) and holds briefly before transitioning.

Duration: 25–35 seconds.

#### Mood: Drift

Camera positioned at medium distance (30–50) with slow lateral drift (not orbiting the center — translating sideways). This creates a parallax effect where near particles move faster than far ones. The camera's look-at target drifts slightly off-center, creating a gentle sweeping view.

Duration: 20–30 seconds.

#### Mood: Pullback

The reverse of Approach. Camera starts close (distance 15–20) and slowly retreats to wide orbit (distance 80–100). The structure shrinks from an immersive particle field to a luminous disc shape. This is the "reveal" moment — the player sees the whole thing.

Syncs with Layer 2: When the camera reaches full wide view (distance > 75), emit the `structure_revealed` signal. Layer 2's title heartbeat intensifies (replaces the old `celebration_climax` signal).

Duration: 20–30 seconds.

#### Mood: Underside

Camera moves below the disc plane (Y = -20 to -35), looking up through the grid plane at the particle structure from below. The concentric circle grid is prominently visible with particles glowing above it. This is a dramatic angle change that shows the structure's mathematical underpinning.

Duration: 15–25 seconds.

### Camera Transition Logic

```
Current mood ends (timer expires)
    │
    ▼
Pick next mood (weighted random, never repeat same mood twice)
    │
    ▼
Calculate entry position/rotation for next mood
    │
    ▼
Lerp camera position + look_at target over 4–6 seconds
    │
    ▼
New mood begins, mood timer starts
```

**Camera movement within a mood** uses smooth interpolation — position and look-at are lerped toward slowly-moving targets each frame. No snapping, no abrupt direction changes. The camera should feel like it's floating on a current, not being driven.

**All camera motion uses `_process(delta)`** — this is the one place where per-frame computation is acceptable (camera position updates). The particle systems themselves are entirely GPU-driven and don't use `_process()`.

### Stage B Verification Checklist

- [ ] Camera begins in Wide Orbit mood on scene load.
- [ ] Camera transitions smoothly between all 6 moods with no snapping.
- [ ] Wide Orbit shows the full disc structure clearly.
- [ ] Ring Follow puts the camera inside the particle field — particles stream past.
- [ ] Approach creates a sense of moving into the structure.
- [ ] Drift creates parallax between near and far particles.
- [ ] Pullback reveals the full structure from close to far.
- [ ] Underside shows the grid plane with particles above.
- [ ] Camera moves on all three axes — not locked to any single plane.
- [ ] Mood transitions happen every 20–45 seconds with no repetition.
- [ ] `structure_revealed` signal fires during Pullback, Layer 2 responds.
- [ ] Menu text remains readable during all camera positions (the 0.7 opacity helps).
- [ ] FPS remains above 60 during camera transitions and all moods.

---

## Stage C — Integration and Signal Wiring

**Goal:** Wire the galaxy into the full main menu with Layer 2 and Layer 3. Replace the old Layer 1 entirely.

### Changes

- **Remove Layer 1 (Slow Celebration Loop):** Delete `menu_bg_celebration.gd` and its references. The galaxy is the new Layer 1.
- **Remove `starfield.gdshader` from main menu:** The particles replace the shader atmosphere.
- **Signal replacement:** `celebration_climax` → `structure_revealed` (emitted by galaxy camera during Pullback mood). Layer 2 connects to this for title heartbeat intensification.
- **Galaxy opacity reacts to menu state:** When the player is navigating deeper menus (hover on any item), the galaxy `TextureRect` modulate can brighten very slightly (0.7 → 0.75) as a subtle reactivity. On scene transition out, the galaxy fades with the rest of the menu.
- **Scene entrance:** On main menu load, the galaxy starts with 0 opacity and fades in over 2 seconds (matches the stagger entrance timing). The camera starts at maximum zoom-out distance and the first mood is always Wide Orbit, so the player's first view is the full structure revealing itself.

### Stage C Verification Checklist

- [ ] No remnants of the old Layer 1 (celebration loop, starfield shader).
- [ ] Galaxy renders as the background atmosphere on the main menu only.
- [ ] Layer 2 title heartbeat intensifies on `structure_revealed` signal.
- [ ] Layer 3 hover/click reactivity still functions.
- [ ] Galaxy fades in on scene load (2 second fade).
- [ ] Galaxy fades out during scene transition.
- [ ] Scanline overlay renders on top of everything.

---

## Stage D — Polish and Tuning

**Goal:** Final visual quality pass. Color tuning, density adjustments per camera mood, performance verification at multiple resolutions.

### Polish Tasks

- **Particle density vs. camera distance:** When camera is in Ring Follow (close), the particle quad size could scale down slightly (0.12 instead of 0.18) so individual particles don't become large blobs. When camera is in Wide Orbit (far), particles at full size read as luminous points. This can be done via a shader uniform tied to camera distance, or by accepting the natural perspective scaling.
- **Ring particle clustering:** Natural randomness may leave visible gaps or clumps in ring orbits. If this happens, switch from pure random distribution to a blue-noise or stratified distribution for the initial `angle_offset` per particle (jittered grid instead of pure random). This ensures even coverage.
- **Stream fade tuning:** The radial streams should fade gracefully at both ends — particles appearing at the outer edge with 0 opacity, building to full over the first 10% of travel, then fading over the last 20%. Adjust the shader's opacity curve.
- **Central glow haze:** If the central glow particles look grainy up close, consider adding a single billboard quad (large, heavily blurred, 5–10% opacity) at the origin as a soft halo behind the particle cluster.
- **Color temperature gradient:** Particles could shift very slightly cooler (more blue-white) at the outer edge and warmer (more gold) near the center. This creates a subtle sense of temperature/energy without being obvious.
- **Performance profiling:** Test at 1280×720, 1920×1080, and 2560×1440. The SubViewport can render at a fraction of the window resolution (e.g., 75%) for a performance gain with minimal visual quality loss, since the particles are small and additive-blended.

### Stage D Verification Checklist

- [ ] Visual quality is production-ready — no obvious artifacts, gaps, or clumping.
- [ ] Color reads as "warm starlight galaxy" at all camera distances.
- [ ] Performance: 60+ FPS at 1920×1080 on target hardware.
- [ ] Performance: acceptable FPS at 2560×1440.
- [ ] SubViewport resolution scaling works correctly if needed.
- [ ] The overall background integrates with the menu text, title heartbeat, and hover reactivity as a cohesive visual identity.

---

## Resolved Design Decisions

### 1. Custom Particle Shaders — CONFIRMED

Godot 4's `shader_type particles;` shaders provide the `INDEX` (int, 0 to amount-1) and `NUMBER` (uint, unique per emission) built-in variables in both `start()` and `process()` functions. `TRANSFORM[3].xyz` can be set directly to position particles. This is the approach for ring orbital motion and stream flow — pure GPU, zero CPU cost.

**Key API notes for implementation:**
- Godot 4 particle shaders use `start()` (runs on spawn/restart) and `process()` (runs every frame per particle). The Godot 3 `vertex()` function no longer exists for particle shaders.
- `INDEX` is deterministic per particle — it's the particle's slot in the buffer (0 through amount-1). Use it to seed per-particle properties (orbit radius, speed, starting angle) via a `hash()` function.
- `TIME` is a global float available in both functions. Use `TIME * orbit_speed + angle_offset` for orbital position.
- `RESTART` bool is true on the frame a particle spawns. Use it in `process()` to avoid glitches on first frame.

### 2. SubViewport Rendering — CONFIRMED

The 3D galaxy renders in a `SubViewport` fed to a `TextureRect` behind the 2D menu. This cleanly separates 3D and 2D, avoids z-ordering/input-routing bugs from mixing them in one scene tree, and is much easier to describe and debug in Claude Code sessions. The extra render pass is acceptable — the SubViewport contains only unshaded additive-blend particles with no lighting, shadows, or post-processing.

### 3. Reusable Scene Architecture — CONFIRMED

The galaxy structure is built as its own standalone scene (`galaxy_structure.tscn` + `galaxy_structure.gd`) with a public API designed for both main menu and world view use. The main menu and the inter-mission world view both instance this scene. The world view methods are stubbed in Stage A — they exist in the API with empty implementations and `# TODO: Stage N` comments, ready to be filled in when the world view is built.

---

## Reuse API — Galaxy Structure Public Interface

> **Reference:** `docs/bible_history/bible_2_00_world.md` §"Galaxy View — The Strategic Layer Between Missions" defines the world view requirements. The galaxy structure scene provides the ambient particle field and camera system. System nodes, faction territory, connections, and military activity visualization are layered on top by the world view consumer.

The galaxy structure scene (`galaxy_structure.tscn`) exposes the following public interface. Methods marked **(STUBBED)** have empty implementations in Stage A — they exist so consumers can call them without error, but they do nothing until the world view stages fill them in.

### File Location

```
scenes/shared/galaxy/
├── galaxy_structure.tscn          (the 3D scene — particles, camera, grid)
├── galaxy_structure.gd            (public API + structure builder + camera)
├── ring_particles.gdshader
├── stream_particles.gdshader
└── dust_particles.gdshader
```

Note the location: `scenes/shared/galaxy/`, not `scenes/main_menu/galaxy/`. This makes the reuse intent explicit in the file path.

### Signals

```gdscript
signal structure_revealed          # Emitted during Pullback camera mood when full structure visible
signal camera_mood_changed(mood: String)  # Emitted on mood transitions ("wide_orbit", "ring_follow", etc.)
```

### Camera Control

```gdscript
## Start the autonomous camera choreography (mood state machine).
## Called by main menu on scene load.
func start_auto_camera() -> void:

## Stop auto camera and hold current position.
func stop_auto_camera() -> void:

## Transition camera to a specific position/look_at over duration.
## Called by world view for scripted camera moves (e.g., push-in to mission system).
func move_camera_to(position: Vector3, look_at: Vector3, duration: float) -> void:

## Enable manual orbit controls (click-drag to orbit, scroll to zoom).
## Used by world view during time jumps when the player can override auto-orbit.
## Matches fate_space.gd's orbit/pan/zoom input handling.
func enable_manual_orbit() -> void:

## Disable manual orbit, return to auto camera.
func disable_manual_orbit() -> void:

## Get current camera position (for seamless transition from tactical view).
func get_camera_position() -> Vector3:

## Get current camera look_at target.
func get_camera_target() -> Vector3:
```

### Appearance

```gdscript
## Set the overall opacity of the particle structure (0.0–1.0).
## Main menu uses ~0.7 so particles sit behind UI text.
## World view uses 1.0 for full brightness.
func set_opacity(alpha: float) -> void:

## Set the primary particle color. Default is the brand gold.
## Could be overridden per-era if different eras want different galaxy tints.
func set_particle_color(color: Color) -> void:

## Fade the entire structure in/out over duration.
func fade_in(duration: float) -> void:
func fade_out(duration: float) -> void:
```

### World View Integration (STUBBED in Stage A)

These methods exist in the API now with empty bodies. The world view stages will implement them. The bible's galaxy view spec (§"Galaxy View — The Strategic Layer Between Missions") defines the visual requirements these methods will fulfill.

```gdscript
## --- System Nodes ---
## Add a system node at a 3D position within the particle field.
## node_id: unique identifier (maps to region ID from simulation).
## position: 3D world position within the galaxy structure's coordinate space.
## size: relative size (0.0–1.0, maps to significance: population, economic weight).
## color: faction color for the node.
## (STUBBED) Creates a luminous point per bible spec: "Each system is a luminous
## point positioned in 3D space. Node size communicates significance."
func add_system_node(node_id: String, position: Vector3, size: float, color: Color) -> void:
    pass  # TODO: World view stage

## Remove a system node (e.g., system destroyed or depopulated).
func remove_system_node(node_id: String) -> void:
    pass  # TODO: World view stage

## Update a system node's properties (faction changed, size shifted).
func update_system_node(node_id: String, size: float, color: Color) -> void:
    pass  # TODO: World view stage

## Clear all system nodes (reset for new game or test).
func clear_system_nodes() -> void:
    pass  # TODO: World view stage

## --- Faction Territory ---
## Set the faction territory visualization for a region.
## Per bible: "colored regions with clearly defined borders in 3D space —
## not just node color, but volumetric territory coloration."
## region_id: maps to simulation region ID.
## center: 3D center of the territory volume.
## radius: approximate extent.
## color: faction color (with alpha for volume transparency).
## (STUBBED)
func set_territory(region_id: String, center: Vector3, radius: float, color: Color) -> void:
    pass  # TODO: World view stage

## Update territory bounds (expansion/contraction during time jump).
func update_territory(region_id: String, radius: float, color: Color) -> void:
    pass  # TODO: World view stage

## Remove territory (region lost, faction destroyed).
func remove_territory(region_id: String) -> void:
    pass  # TODO: World view stage

## --- Connections ---
## Add a connection line between two system nodes.
## connection_type: "border" (solid, faction color) or "trade" (thin/dashed).
## Per bible: "Trade routes and border connections rendered as faint lines
## between nodes in 3D."
## (STUBBED)
func add_connection(from_id: String, to_id: String, connection_type: String, color: Color) -> void:
    pass  # TODO: World view stage

func remove_connection(from_id: String, to_id: String) -> void:
    pass  # TODO: World view stage

## --- Military Activity ---
## Flash military activity between/around systems.
## Per bible: "small rapid flashes of light pulse between or around the
## involved systems. Sped up to match the time jump's accelerated pace."
## intensity: 0.0–1.0 (scales flash brightness and frequency).
## (STUBBED)
func flash_military_activity(region_id: String, intensity: float) -> void:
    pass  # TODO: World view stage

## Flash conflict between two specific systems (border friction, attack).
func flash_conflict(from_id: String, to_id: String, intensity: float) -> void:
    pass  # TODO: World view stage

## --- Highlight ---
## Highlight a specific system (e.g., next mission target).
## Per bible: "The next mission's system is highlighted or gently pulsed."
## (STUBBED)
func highlight_system(node_id: String) -> void:
    pass  # TODO: World view stage

func clear_highlight() -> void:
    pass  # TODO: World view stage
```

### How the Main Menu Uses It

```gdscript
# In main_menu.gd _ready():
var galaxy = $GalaxyViewport/SubViewport/GalaxyStructure
galaxy.set_opacity(0.7)
galaxy.fade_in(2.0)
galaxy.start_auto_camera()
galaxy.camera_mood_changed.connect(_on_camera_mood)
galaxy.structure_revealed.connect(_on_structure_revealed)

# None of the world view methods are called — they're just sitting there
# ready for when the world view scene instances the same galaxy_structure.tscn.
```

### How the World View Will Use It (Future — Not Implemented Now)

```gdscript
# In world_view.gd (future stage):
var galaxy = $WorldViewport/SubViewport/GalaxyStructure
galaxy.set_opacity(1.0)
galaxy.fade_in(1.0)
galaxy.start_auto_camera()
galaxy.enable_manual_orbit()  # Player can override auto-orbit

# Populate from simulation state:
for region in simulation.get_regions():
    galaxy.add_system_node(region.id, region.galaxy_position, region.significance, region.faction_color)
    galaxy.set_territory(region.id, region.galaxy_position, region.territory_radius, region.faction_color)

for connection in simulation.get_connections():
    galaxy.add_connection(connection.from_id, connection.to_id, connection.type, connection.color)

# During time jump tick:
func _on_simulation_tick():
    for region in simulation.get_changed_regions():
        galaxy.update_system_node(region.id, region.significance, region.faction_color)
        galaxy.update_territory(region.id, region.territory_radius, region.faction_color)
    for conflict in simulation.get_active_conflicts():
        galaxy.flash_conflict(conflict.from_id, conflict.to_id, conflict.intensity)

# Transition to next mission:
galaxy.highlight_system(next_mission.system_id)
galaxy.move_camera_to(zoom_in_position, next_mission.system_position, 3.0)
```

---

## Files Created / Modified

### New Files (Stage A)
- `scenes/shared/galaxy/galaxy_structure.tscn` — Reusable 3D scene
- `scenes/shared/galaxy/galaxy_structure.gd` — Public API + structure builder + camera
- `scenes/shared/galaxy/ring_particles.gdshader` — Orbital motion shader
- `scenes/shared/galaxy/stream_particles.gdshader` — Radial inflow shader
- `scenes/shared/galaxy/dust_particles.gdshader` — Ambient drift shader

### New Files (Stage B)
- No new files — camera choreography is added to `galaxy_structure.gd`

### Modified Files
- `scenes/main_menu/main_menu.tscn` — Add SubViewport + TextureRect, instance `galaxy_structure.tscn`
- `scenes/main_menu/main_menu.gd` — Wire galaxy fade-in, connect signals, remove old Layer 1

### Removed Files (Stage C)
- `scenes/main_menu/menu_bg_celebration.gd` — Replaced by galaxy
