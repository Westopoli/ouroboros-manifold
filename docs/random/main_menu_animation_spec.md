# Main Menu Background Animation — Implementation Spec

> **Context:** This spec defines the animated background system for the main menu screen. It extends the animation design language from `animation_strategy.md` into an ambient, infinite-loop composition. It also establishes the game-wide background color and the main menu title treatment.
>
> **Bible impact:** After implementation, update `theme_constants.gd` BASE color, update main menu spec in Stage 9, and append this as a new section to `animation_strategy.md`.

---

## Color Changes

### New Background Palette

The global background color shifts from warm near-black to cool-tinted deep blue-black. This creates higher contrast with the gold accent (`#D4A017`) — the gold glows more aggressively against a cool surface, and the cold void undertone evokes deep space without locking the aesthetic to sci-fi (it reads as "darkness" more than "space" when no stars are present).

Update `theme_constants.gd`:

| Token | Old Value | New Value | Notes |
|-------|-----------|-----------|-------|
| `BASE` | `#0a0a0c` | `#0A0D12` | Blue-black. All full-screen backgrounds. |
| `SURFACE` | `#111114` | `#10141A` | Shift to match new BASE undertone. Cards sit on this. |
| `CARD` | `#18181c` | `#171C24` | Same blue-cool shift. |
| `ELEVATED` | `#1f1f24` | `#1E242E` | Hover states, modals. |

The text colors (`PRIMARY` `#e8e6e1`, `SECONDARY`, `TERTIARY`) remain unchanged — the slightly warm off-white against the cool background creates a subtle temperature contrast that adds depth.

The gold accent `#D4A017` is now officially designated as the **brand accent color** — the color that appears in the logo, the main menu title heartbeat, hover effects, and as the default accent when no era is active. Era-specific accents (Roman gold, Settled Reach teal, 1980s olive) remain unchanged.

### Website Alignment

For the marketing website, the dark theme tokens should be updated to match:

| CSS Variable | Old | New |
|---|---|---|
| `--surface` (dark) | `#111110` | `#0A0D12` |
| `--surface-subtle` (dark) | `#1A1918` | `#10141A` |
| `--surface-elevated` (dark) | `#222220` | `#171C24` |

Light theme is unaffected.

---

## Main Menu Title Treatment

### Remove Duplicate Title

The current layout has "OUROBOROS MANIFOLD" as a classification label above "Ouroboros Manifold" as a serif title. Replace with:

- **Studio credit:** "A WESTOPOLI GAME" in `CLASSIFICATION_LABEL` style (10px JetBrains Mono, letter-spacing 3px, `TERTIARY` color). This is static — it does not participate in the departure board heartbeat.
- **Game title:** "OUROBOROS MANIFOLD" in Newsreader, 28px+, `PRIMARY` color. This is the departure board heartbeat target (see Layer 2 below).

The classification label goes above the title, same position as before. The game title replaces the old serif rendering.

---

## Animation Architecture

Three independent layers, composited via Godot's node tree. Each layer is a separate node with its own responsibility. They never share state except for one signal (see Layer 1 → Layer 2 coupling below).

```
main_menu.tscn
├── MenuBgCelebration      (Layer 1 — CanvasLayer, z_index -2)
│   ├── ShaderRect          (ColorRect with atmosphere shader)
│   └── GlyphPool           (Node2D container for bloom glyphs)
├── MenuTitleHeartbeat      (Layer 2 — Control node, z_index -1)
│   └── TitleLabels[]       (individual Label per character)
├── MenuContent             (Layer 3 foreground — existing menu layout)
│   ├── StudioLabel         ("A WESTOPOLI GAME")
│   ├── MenuItems           (VBoxContainer: NEW GAME, CONTINUE, etc.)
│   ├── KeyHint             ("Have an access key?...")
│   └── VersionLabel        ("v0.9.0")
└── ScanlineOverlay         (existing CanvasLayer, z_index top)
```

---

## Layer 1 — Slow Celebration Loop

**File:** `scenes/main_menu/menu_bg_celebration.gd`
**Extends:** `Node2D` (not `celebration_base.gd` — this is a continuous loop, not a one-shot celebration; it reuses the primitives but manages its own lifecycle)

### Concept

A 50-second choreographed loop that runs the same three-phase arc as the era unlock celebrations, but stretched to ambient speed and dialed to ~25% of celebration brightness. The loop is seamless — Phase 3's exit state is visually identical to pre-Phase 1, so the restart is invisible.

### Phase Breakdown

**Phase 1 — Field Populates (0s–18s)**

- **0s:** Shader (`starfield.gdshader`) begins fade-in from 0% to 15% opacity over 6 seconds. The starfield shader is chosen because it's era-neutral and complements the blue-black background.
- **0s–18s:** Dot glyphs (`·`) spawn at random screen positions, 1 every 0.8s. Each dot fades in to 6% opacity over 1.5s, drifts slowly (8px/sec, direction: slight upward-left diagonal — consistent across all dots for a sense of current), and pulses gently (5%–7% opacity, 0.4Hz sine). Dots persist through all phases — they are the ambient substrate.
- **8s:** First bloom_ring fires. Center: offset 60% right, 45% down from screen origin (away from menu text). 8 glyphs from the Settled Reach set, radius 120px, expand over 4s. Glyph opacity: 10%. Very slow, very faint.
- **14s:** Second bloom_ring. Center: offset 70% right, 30% down. 12 glyphs, radius 200px, expand over 5s. Opacity: 8%. Uses simpler glyphs (dots + small stars only).

**Phase 2 — Climax (18s–36s)**

- **18s:** Third bloom_ring, larger. Center: 55% right, 50% down. 16 glyphs, radius 280px, 6s expand. Opacity: 12%. This is the brightest moment.
- **20s:** bloom_scatter fires — 15 glyphs across a 300px radius from the same center. Each drifts outward 30px over 4s, opacity 10%, using the full Settled Reach glyph progression (simpler glyphs near center, complex glyphs at edges).
- **22s:** Background depth scatter — 30 dot glyphs (`·`) at 4% opacity, 450px radius, 6s lifetime. Creates a halo behind the foreground scatter.
- **24s:** Emit signal `celebration_climax` (Layer 2 listens to this — see below).
- **26s:** A single sweep_line draws across the lower third of the screen, left-to-right, 40 `─` characters, each fading in sequentially over 2s total. Opacity: 8%. Fades out over the next 4s.
- **30s:** Final bloom_ring — a slow shockwave. 20 glyphs, radius starts at 100px, expands to 350px over 6s. Opacity peaks at 10% then fades to 0 by the ring's edge. This is the "dispersal signal."

**Phase 3 — Dissolve (36s–48s)**

- **36s–42s:** All remaining bloom glyphs (rings + scatter) drift outward at 2× their normal speed and fade to 0 over 4s. This matches the celebration exit pattern (elements leave with direction, they don't just vanish).
- **38s:** Shader begins fade from 15% to 5% opacity over 6s.
- **42s–48s:** The ambient dot substrate continues unchanged (it never exits — it's the visual constant that makes the loop seamless). The field is now nearly bare: just slow-drifting dots at 6% opacity and the shader at 5%.

**Loop Transition (48s–50s)**

- **48s:** Shader begins fade from 5% back toward 15% (this IS Phase 1's shader fade-in for the next cycle). New bloom elements begin spawning at the Phase 1 schedule. The overlap means there's never a "blank" frame.
- **50s:** Reset internal timer to 0. The loop is now seamless.

### Implementation Notes

- Reuse `_make_glyph()`, `bloom_ring()`, `bloom_scatter()` logic from `celebration_base.gd` — either by extracting those into a shared utility, or by duplicating the core tween-based glyph spawning. Do NOT extend `celebration_base.gd` directly because it expects a finite `_run_sequence()` → `animation_finished` lifecycle.
- All bloom centers are expressed as fractions of viewport size, not absolute pixels. Recalculate on `_notification(NOTIFICATION_RESIZED)`.
- The glyph pool should have a hard cap of ~80 active Label nodes. Old dots that have been alive > 20s are recycled (fade out and reposition) rather than creating new ones.
- The shader uniform `color` should be set to the brand gold (`#D4A017`) tinted toward blue — suggest `#8A9BB8` (a muted blue-silver) for the starfield, so the stars don't compete with the gold foreground glyphs. Alternatively, use white at very low opacity — test both.
- **Signal:** Exposes `signal celebration_climax` — emitted once per loop at the 24s mark. Layer 2 connects to this.

### Glyph Set for Layer 1

Use the Settled Reach set as the default (it's the base game era):
```
["·", "✧", "✦", "✶", "✹", "✺", "✻", "✽"]
```

The ambient dots always use `·`. Bloom rings and scatter use the full set, with simpler glyphs (indices 0–3) appearing more frequently than complex ones (indices 4–7). Weight the random selection: 40% simple, 35% mid, 25% complex.

---

## Layer 2 — Departure Board Heartbeat

**File:** `scenes/main_menu/menu_title_heartbeat.gd`
**Extends:** `Control`

### Concept

The game title "OUROBOROS MANIFOLD" is rendered as individual `Label` nodes (one per character, including the space). In its resting state, all characters display their correct final letter in Newsreader (serif), `PRIMARY` color. At random intervals, individual characters briefly "un-resolve" — they flicker to a random glyph from a rotating era set, rendered in JetBrains Mono (monospace) in the brand gold color, then re-lock to their correct letter with a subtle brightness pulse.

This is the `resolve_title` primitive running in reverse, perpetually, at very low frequency.

### Resting State

- 18 characters (O-U-R-O-B-O-R-O-S-space-M-A-N-I-F-O-L-D), each a `Label` node.
- Font: Newsreader, 28px (matching `TITLE` typography from `theme_constants.gd`).
- Color: `PRIMARY` (`#e8e6e1`).
- Position: calculated from a center-left anchor matching the current menu layout. Characters are spaced using the Newsreader metrics (variable-width, not monospace-grid).
- All characters have a baseline subtle pulse: opacity oscillates between 0.92 and 1.0 on a slow sine (0.15Hz, phase-offset per character so they don't pulse in unison). This keeps the title "breathing" even between un-resolve events.

### Un-Resolve Behavior

**Trigger frequency:** Every 8–15 seconds (uniform random), 1–3 characters are selected for un-resolve. Selection is weighted random — characters near the center of the title are slightly more likely to be picked (creates a visual focal point). The space character is never selected.

**Un-resolve sequence per character:**
1. **Snap to mono:** Character switches from Newsreader to JetBrains Mono, color shifts from `PRIMARY` to brand gold (`#D4A017`). This happens in a single frame — the snap IS the visual event (same principle as the "font snap" in `resolve_title`, but in reverse).
2. **Glyph cycle:** For 0.15–0.25s (randomized), the character cycles through random glyphs from the current era set at 50ms intervals.
3. **Re-lock:** Character snaps back to its correct letter, font returns to Newsreader, color returns to `PRIMARY`. A brightness pulse (opacity jumps to 1.0 and the color briefly tints toward white `#FFFFFF` at 30% blend) decays over 0.3s back to normal.

**Era set rotation:** The glyph set used for the scramble cycles through eras on a slow timer — Roman glyphs for ~90 seconds, then Settled Reach, then 1980s, then back to Roman. The transition between sets is invisible (the un-resolve events are infrequent enough that the player won't notice the set changed). This is a subliminal preview of the era-agnostic nature of the game.

```
Era rotation order:
  Roman:         ["✦", "✧", "◆", "❖", "✶", "⬥", "◈", "✴"]
  Settled Reach: ["·", "✧", "✦", "✶", "✹", "✺", "✻", "✽"]
  1980s:         ["─", "━", "═", "▪", "▫", "◽", "◾", "■"]
```

### Climax Intensification

When Layer 1 emits `celebration_climax`:

- The next un-resolve event fires immediately (don't wait for the random timer).
- 4–6 characters un-resolve simultaneously instead of 1–3.
- Glyph cycle duration extends to 0.4s (longer tension).
- Re-lock brightness pulse is stronger (40% white tint instead of 30%).
- After this intensified event, normal frequency resumes.

### Implementation Notes

- Pre-calculate character positions on `_ready()` using Newsreader font metrics. Cache positions — they don't change.
- The glyph cycle uses a `Timer` node per active un-resolving character, not `await` or `tween_interval`. This keeps the system stateless per-character and avoids tween pile-up.
- JetBrains Mono characters are wider than Newsreader at the same pt size. During the glyph cycle, the character's `Label` should be center-anchored at its position so the width difference doesn't cause horizontal jitter. Alternatively, set a fixed `custom_minimum_size.x` equal to the JetBrains Mono character width and center-align the text within it.
- Connect to `MenuBgCelebration.celebration_climax` in `_ready()`.

---

## Layer 3 — Menu Item Reactivity

**File:** Modifications to existing `scenes/main_menu/main_menu.gd`

### Hover Bloom

When the player hovers (mouse) or focuses (keyboard/gamepad) a menu item:

- 2–4 tiny glyphs bloom outward from the left edge of the menu item text.
- Glyph set: brand accent only — use `✦` and `·` (one accent glyph, one dot).
- Spawn positions: clustered near the left edge of the text, offset randomly ±8px vertically.
- Drift: outward-left, 25–40px over 0.5s, with slight vertical spread.
- Opacity: fade in to 20% over 0.1s, hold, fade out over 0.3s. Gold color (`#D4A017`).
- Glyph count scales by item significance:
  - NEW GAME: 4 glyphs
  - CONTINUE: 3 glyphs
  - ERA LIBRARY: 3 glyphs
  - SETTINGS: 2 glyphs
  - QUIT: 2 glyphs
- Glyphs should be small (10–12px JetBrains Mono).
- On hover-exit, any in-flight glyphs continue their animation to completion (don't abruptly kill them).

### Click Burst

When a menu item is clicked/selected:

- A single fast bloom_ring fires from the center-left of the selected item.
- 6 glyphs, radius 30px, expand to 60px over 0.3s. Gold color, 25% opacity.
- This fires BEFORE the scene transition fade begins (the 0.3s ring animation overlaps with the 0.3s scene transition fade-out — the ring is visible for its first ~0.2s before the fade obscures it).
- "QUIT" skips the ring (immediate exit feels more decisive).

### Implementation Notes

- Menu items need `mouse_entered`, `mouse_exited`, and `focus_entered`, `focus_exited` signal connections.
- The glyph spawning can reuse the same `_make_glyph()` helper from Layer 1, or be a lightweight local function (it's just creating Labels with Tweens).
- Cap active hover glyphs at 12 — if the player rapidly mouses over items, old glyphs are not interrupted but no new ones spawn until the count drops.

---

## Performance Budget

The entire background animation system should use:
- **Label nodes:** ≤ 80 simultaneous (Layer 1 glyph pool) + 18 (Layer 2 title characters) + 12 (Layer 3 hover cap) = **≤ 110 Label nodes**.
- **Shader:** 1 full-screen fragment shader at ≤ 15% opacity. GPU cost is negligible.
- **Tweens:** ≤ 30 active Tweens at any given time (bloom rings + scatter + title pulses + hover effects). Each Tween is lightweight — Godot handles hundreds without issue.
- **No `_process()` polling.** All animation is Tween-driven or Timer-driven. The only per-frame work is the shader, which runs on the GPU.

---

## Files Created / Modified

### New Files
- `scenes/main_menu/menu_bg_celebration.gd` — Layer 1 slow celebration loop
- `scenes/main_menu/menu_title_heartbeat.gd` — Layer 2 departure board heartbeat

### Modified Files
- `autoload/theme_constants.gd` — New BASE/SURFACE/CARD/ELEVATED colors
- `scenes/main_menu/main_menu.tscn` — Add Layer 1 and Layer 2 nodes, restructure title
- `scenes/main_menu/main_menu.gd` — Add Layer 3 hover/click reactivity, update title text
- `shared.css` (website) — Update dark theme surface colors to match

### Unchanged Files
- `assets/celebrations/celebration_base.gd` — Not extended, but its primitives are referenced
- `assets/shaders/starfield.gdshader` — Used as-is by Layer 1
- All other menu screens — They inherit the new BASE color from `theme_constants.gd` automatically

---

## Verification Checklist

- [ ] Background color is `#0A0D12` on all menu screens (not just main menu).
- [ ] Title reads "A WESTOPOLI GAME" above "OUROBOROS MANIFOLD" — no duplicate title.
- [ ] Layer 1 loop runs continuously with no visible seam at the loop point.
- [ ] Layer 1 bloom elements are positioned right-of-center (away from menu text).
- [ ] Layer 1 total brightness never competes with menu text readability.
- [ ] Layer 2 title characters un-resolve at random intervals (8–15s baseline).
- [ ] Layer 2 un-resolve uses correct era glyph sets and rotates between them.
- [ ] Layer 2 intensifies when Layer 1 hits its climax signal.
- [ ] Layer 3 hover blooms fire on mouse hover AND keyboard/gamepad focus.
- [ ] Layer 3 click burst fires on selection (except QUIT).
- [ ] Total active Label nodes never exceed 110.
- [ ] No `_process()` functions in any of the three layers.
- [ ] Animation looks correct at 1920×1080, 2560×1440, and 1280×720.
- [ ] Scanline overlay renders on top of all three layers.
