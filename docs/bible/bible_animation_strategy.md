# Ouroboros Manifold — Animation Strategy Reference

> **Purpose:** This document defines the animation design language for all Ouroboros Manifold UI animations. It is the reference for designing new animations — celebration unlocks, screen transitions, UI feedback moments, or any future visual flourish. If you're creating a new animation, read this first.
>
> **Origin:** Developed during Stage 9 (UI Shell) after iterating on era unlock and key redemption celebration animations. The initial approach (building representational ASCII pictures — Roman columns from pipe characters, submarines from tildes) felt cheesy and artificial. The revised approach draws from Claude Code's terminal animations, which feel alive and precise despite extreme simplicity.

---

## The Core Principle

**Individual elements are simple. Composition and timing create the effect.**

A single Unicode glyph fading in is nothing. Twelve of them blooming outward in a ring with staggered timing is hypnotic. The animations in this game never try to *draw a picture* from text characters. They use abstract decorative glyphs as rhythmic visual elements — closer to musical notes in a composition than pixels in an illustration.

The reference point is Claude Code's thinking spinner: six glyphs (`·`, `✢`, `✳`, `∗`, `✻`, `✽`) cycling at 120ms intervals with reverse-mirroring. It feels organic because each glyph is slightly more complex than the last, the timing is precise, and the sequence loops smoothly. That's the entire trick — curated glyphs, precise timing, smooth transitions.

---

## The Two-Layer Architecture

Every animation in the game uses two layers that composite together:

### Layer 1 — Background Atmosphere

The background layer creates the emotional mood. Two approaches exist depending on context:

**Shader atmosphere (era celebrations, unlock screens):** A full-screen Godot fragment shader runs dimmed (20–30% opacity over the dark `BASE` background). Mathematical functions produce inherently smooth motion — sine waves, noise fields, particle simulations. Shaders run on the GPU with zero performance concern.

**3D particle structure (main menu):** The main menu uses a 3D particle galaxy rendered in a SubViewport behind the 2D UI at 70% opacity. The galaxy is built from ~5,200 particles across multiple GPUParticles3D nodes (12 orbital rings on tilted planes, 6 radial inflow streams, ambient dust, static starfield, central glow). Custom particle shaders drive orbital motion entirely on the GPU. An autonomous camera state machine cycles through 6 moods (Wide Orbit, Ring Follow, Approach, Drift, Pullback, Underside) with smooth 5-second transitions. The structure is a reusable scene (`scenes/shared/galaxy/galaxy_structure.tscn`) designed to also serve as the world view background during inter-mission time jumps. See `docs/stage_specs/main_menu_galaxy_spec.md` for full details.

**Design rules for atmosphere layers:**
- Keep the visual density low. The atmosphere should feel like ambient light, not a screensaver.
- Use only the era's accent color (or a tinted variant) as the color palette. No secondary colors. Exception: the galaxy uses 85% gold / 15% blue-white for depth.
- Motion should be slow and continuous. Nothing should snap, flash, or jitter. If you can perceive individual frames, it's too fast.
- Design for the dimmed state — what reads at low opacity? Contrast and motion read. Fine detail does not.
- Parameterize everything. Shaders expose uniforms for color, speed, density, and opacity. The galaxy exposes a public API for opacity, color, and camera control.

**Existing atmosphere shaders (as templates for new ones):**

| Shader | Visual | Mood | Key Technique |
|---|---|---|---|
| `ember_drift` | Warm particles rising | Ancient, torchlit, measured | Soft circles (smoothstep), upward drift with sine sway, gradient warmth at bottom |
| `starfield` | Twinkling point stars with parallax | Vast, calm, deep space | Pseudo-random positions from UV hash, sine-wave opacity twinkle, multi-speed parallax layers |
| `wave_surface` | Horizontal oscillating lines | Tense, military, sonar | Overlapping sine functions at different frequencies, thin lines, confined to bottom third |

**When designing a new atmosphere shader:** Ask "what does this era feel like if you close your eyes and just sense the environment?" Medieval might be flickering candlelight (similar to ember_drift but cooler, with occasional brighter flickers). Cyberpunk might be scrolling data rain (vertical character-like streaks, Matrix-inspired but abstract). Post-apocalyptic might be drifting ash (like ember_drift but gray, slower, downward). The shader captures *ambient sensation*, not literal imagery.

### Layer 2 — Glyph Bloom + Title Resolve (Foreground)

Unicode decorative characters rendered as `Label` nodes, animated with Godot's `Tween` system. These are the foreground visual events — they have clear choreography, precise timing, and use the era's accent color at full brightness.

**Why Unicode glyphs instead of ASCII art:** Traditional ASCII art tries to make characters look like something they're not (a submarine made of tildes). The result always looks like "someone tried to draw with text." Abstract decorative glyphs don't pretend to be anything — they're pure visual punctuation. A `✦` is just a beautiful shape. Twelve of them arranged in a ring and blooming outward is a visual event, not a picture. The brain reads it as *pattern and motion*, not as *a failed drawing*.

**Design rules for glyph work:**
- Every glyph in a set should be visually related but progressively more complex. This creates a natural "small → large" or "simple → ornate" gradient when you sequence through them.
- Glyph sets should have 6–10 entries. Fewer feels repetitive. More becomes noise.
- All glyphs render in JetBrains Mono (the game's monospace font). They are always monospace — the fixed width is part of the aesthetic.
- Accent color at full brightness for primary glyphs. 15–40% opacity for secondary/depth glyphs.
- Glyphs never stay on screen without animating. They are always fading in, drifting, pulsing, or fading out. A static glyph is a dead glyph.

---

## The Glyph Vocabulary

Each era has a curated glyph set that reflects its personality. The glyphs are abstract — they evoke a *feeling*, not a literal image.

### Existing Glyph Sets

**Roman** — Angular, gem-like. Carved stone and metalwork.
```
["✦", "✧", "◆", "❖", "✶", "⬥", "◈", "✴"]
```
Progression: small star → outlined star → solid diamond → ornate diamond → six-pointed → filled diamond → framed diamond → eight-pointed. The shapes suggest precision craftsmanship.

**Settled Reach (Sci-Fi)** — The Claude Code spinner set, extended. Dot-to-bloom.
```
["·", "✧", "✦", "✶", "✹", "✺", "✻", "✽"]
```
Progression: dot → small star → solid star → six-pointed → larger star → even larger → bloom → full flower. Each glyph is organically more complex than the last. Feels like stars resolving from noise into clarity.

**1980s** — Geometric, military, precise. No curves.
```
["─", "━", "═", "▪", "▫", "◽", "◾", "■"]
```
Progression: thin line → thick line → double line → small filled square → small empty square → medium empty square → medium filled square → large filled square. Everything is horizontal or square. Radar blips and sonar returns.

### Designing a New Glyph Set

1. **Start with the era's personality in three words.** Roman: *precise, ornamental, authoritative*. Settled Reach: *vast, organic, crystallizing*. 1980s: *geometric, military, tense*.

2. **Pick a visual family.** Stars and diamonds for ornamental eras. Dots and blooms for organic eras. Lines and blocks for mechanical eras. Circles and rings for mystical eras. Arrows and chevrons for aggressive eras.

3. **Build a progression of 6–10 glyphs.** Start with the simplest member of the family (a dot, a thin line, a small diamond). End with the most complex or largest. Each intermediate glyph should be visually "one step more" than the previous. Test by lining them up: `· ✧ ✦ ✶ ✹ ✺ ✻ ✽` — can you see the growth? If not, reorder or swap glyphs.

4. **Test at the target font size.** Some Unicode glyphs look great at 24px and invisible at 10px. Render the full set in JetBrains Mono at the sizes you'll actually use (typically 14–28px) and verify they're all legible and visually distinct.

**Useful Unicode blocks for glyph sourcing:**
- Dingbats: `✦ ✧ ✶ ✷ ✸ ✹ ✺ ✻ ✼ ✽ ✾ ✿ ❀ ❁ ❂ ❃ ❇ ❈ ❖`
- Geometric shapes: `◆ ◇ ◈ ○ ● ◐ ◑ ◒ ◓ ◔ ◕ ◖ ◗ ■ □ ▪ ▫ ▬ ▮ ▰ ▲ △ ▶ ▷ ◽ ◾ ⬥ ⬦ ⬧`
- Box drawing: `─ ━ │ ┃ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ═ ║ ╔ ╗ ╚ ╝`
- Arrows: `← → ↑ ↓ ↗ ↘ ↙ ↖ ⇐ ⇒ ⇑ ⇓ ➤ ➜ ➝ ➞`
- Miscellaneous symbols: `⚡ ⚙ ⚛ ⚜ ♦ ♢ ⟐ ⟡ ⌘ ⏣ ⏥`
- Mathematical: `∗ ∘ ∙ ≡ ≈ ∴ ∵ ⊕ ⊗ ⊙`

---

## Animation Primitives

These are the building blocks. All complex animations are composed from combinations of these primitives. They're implemented in `celebration_base.gd` and available to all celebration scripts.

### bloom_ring

Places glyphs evenly spaced in a ring around a center point. Each glyph fades in with a slight scale-up (0.5× → 1.0×), holds briefly, then fades out. The ring itself expands slightly (radius grows 10–15%) during the animation. Glyphs enter with a clockwise stagger — each one's fade-in is offset from the previous, creating a sweep effect rather than all appearing simultaneously.

**Parameters:** center position, glyph set, count, radius, delay before start, total duration.

**When to use:** Ornamental framing, expanding shockwaves, decorative seals, sonar pings. Works best at 6–14 glyphs per ring. Multiple concentric rings at different radii and timings create layered depth.

**Layering technique:** Stack 2–3 rings at different radii, stagger their start times by 0.2–0.3s, and give outer rings more glyphs and slower timing. Inner rings are fast and bright. Outer rings are slower, more numerous, and can use dimmer opacity.

### bloom_scatter

Places glyphs at random positions within a radius of a center point. Each glyph fades in, drifts outward slightly (10–20px), and fades out. Organic and particle-like.

**Parameters:** center position, glyph set, count, radius, delay before start, total duration.

**When to use:** Ambient sparkle, atmospheric particles, creating a "field" of activity around a focal point. Higher counts (15–30) at low opacity create atmosphere. Lower counts (5–10) at full opacity create intentional visual events.

**Layering technique:** Run two scatter layers simultaneously — one with full-brightness glyphs using the era's primary set, one with `·` dots at 15–20% opacity at 1.5× the radius. The dim layer creates depth behind the bright layer. Use the glyph progression — early scatter waves use simpler glyphs (dots, small stars), later waves use more complex ones (blooms, ornate shapes). This creates a sense of crescendo.

### resolve_title

The signature title reveal. Each character position starts by cycling through random glyphs from the era's set at 60ms intervals (the "departure board" scramble). After a configurable scramble duration, each position locks to its final letter. Characters lock left-to-right with a stagger interval between each.

**Parameters:** text string, center position, delay before start, per-character stagger interval, scramble duration per character.

**Key detail — the font snap:** Scramble characters render in JetBrains Mono (monospace). The final locked letter renders in Newsreader (serif) at a slightly larger size. The visual "snap" from monospace to serif when a letter locks is part of the reveal — it signals "this one is decided." This font transition is a core part of the effect and should not be removed.

**When to use:** Any moment where a title, label, or important text needs a dramatic entrance. Not just for era names — could be used for chapter titles, commander names, achievement labels, or any text that deserves ceremony.

**Tuning guide:** 
- `char_interval` controls pacing. 0.08s feels rapid and energetic (good for long titles). 0.15s feels deliberate and military (good for short titles or single words).
- `scramble_duration` controls tension. 0.3s is snappy. 0.6s builds anticipation. Over 0.8s starts to feel sluggish.
- The scramble should use glyphs from the era's set, not random Unicode. This means the scramble itself has visual coherence with the surrounding bloom effects.

### Supporting Primitives

**sweep_line** — A horizontal line of `─` characters drawn across the screen one character at a time. Used for framing, underlining, or creating radar-sweep effects. Can draw left-to-right, right-to-left, or outward-from-center.

**pulse** — A single element's opacity oscillates (sine wave between two values). Used to make elements feel alive while they hold position. Subtle pulse (0.6–1.0 opacity, 2Hz) keeps an element present without drawing too much attention.

**shimmer** — A bright highlight sweeps across a row of elements left-to-right. Each element briefly brightens to white then returns to accent color as the wave passes. Duration of the full sweep is typically 0.2–0.3s. Creates a satisfying "confirmation" feeling.

**drift** — An element's position tweens slowly in a direction. Used for persistent background elements (stars, embers) that should feel alive. Speed is typically 5–15px per second. Combined with pulse, creates ambient particle behavior.

---

## Choreography Principles

These rules govern how primitives are composed into complete animations.

### 1. Three-Phase Structure

Every celebration animation follows a three-phase arc:

- **Phase 1 — Atmosphere builds.** The shader fades in. Initial bloom rings or scatter waves establish the visual field. No text yet. Duration: ~30–40% of total.
- **Phase 2 — Title resolves.** The departure-board effect reveals the title. Supporting bloom elements fire during the resolve, reacting to the text appearing. This is the climax. Duration: ~40–50% of total.
- **Phase 3 — Elements disperse.** Everything exits with intention. Glyphs scatter outward, fade, collapse inward, or accelerate away. The title holds longest and fades last. The shader dims. Duration: ~20–30% of total.

### 2. Nothing Is Static

Every element on screen is either entering, holding with a subtle animation (pulse, drift), or exiting. If an element is completely still for more than 0.5s, it's dead weight. Add a pulse or a slow drift.

### 3. Enter and Exit With Intention

Elements don't just fade in and fade out. They have *direction*:
- Bloom rings expand outward (enter) and collapse inward or scatter outward (exit).
- Scatter glyphs drift outward during their lifetime.
- Sweep lines draw in a direction.
- The title resolve moves left-to-right.

Every element's motion should have a clear vector. Random motion (jittering, bouncing) is never used — it reads as broken, not organic.

### 4. Stagger Everything

Never fire two things at the same instant. Offset by 0.1–0.3s. This creates rhythm. Two bloom rings firing simultaneously look like one messy ring. Two rings firing 0.2s apart look like a deliberate one-two beat. This is the single most impactful technique.

### 5. Create Depth With Opacity Layers

Run two versions of the same primitive simultaneously:
- **Foreground:** Full accent brightness, smaller count, focused radius.
- **Background:** 15–25% opacity, larger count, 1.5× radius, using simpler glyphs (dots).

The background layer creates a halo/aura effect that makes the foreground layer feel richer without adding visual clutter. This is cheap (just more Label nodes at lower opacity) and dramatically improves perceived quality.

### 6. Reactive Moments

When the title resolve hits a milestone (first letter locks, last letter locks, or all letters locked), fire a secondary visual event — a bloom ring shockwave, a shimmer sweep, or a brightness pulse on background elements. These reactive moments make the animation feel like a system rather than a scripted sequence. The glyphs "respond" to the title appearing.

### 7. Total Duration Budget

- **Era unlock celebrations:** 3.0–3.8 seconds. Long enough to feel momentous (this is a rare event — the player just gained access to an entire era). Short enough to not become a loading screen.
- **Key redemption animations:** 1.5–2.0 seconds. Quick and punchy. These happen in context (the player is in the middle of redeeming a code) and shouldn't break flow.
- **Future UI moments** (chapter title reveals, commander death notifications, achievement popups): 1.0–2.0 seconds depending on significance.

Adding more elements does NOT extend the duration. More elements fill the existing time budget with more layers, not more seconds.

---

## Designing a New Animation — Step by Step

1. **Identify the moment.** What is happening in the game? What emotion should the player feel? (Triumph, awe, tension, warmth, finality.)

2. **Pick or create an atmosphere shader.** Does an existing shader fit, or does this moment need a new one? Reuse when possible — a shader per era is usually sufficient.

3. **Pick or create a glyph set.** Same question. Most animations within an era reuse the era's glyph set.

4. **Decide the duration budget.** How significant is this moment? 1s for minor, 2s for moderate, 3.5s for major.

5. **Sketch the three phases.** What builds in Phase 1? What's the climax in Phase 2? How does Phase 3 exit? Write this in plain language before touching code.

6. **Assign primitives to each phase.** Phase 1 often uses `bloom_scatter` and `bloom_ring`. Phase 2 uses `resolve_title` plus reactive `bloom_ring` shockwaves. Phase 3 uses drift-and-fade on remaining elements.

7. **Layer for depth.** Add a background opacity layer to your main bloom elements. Add persistent drifting glyphs that span all three phases.

8. **Add reactive moments.** Where do milestones happen in Phase 2? Add shockwaves or pulses at those moments.

9. **Set stagger timings.** Offset every simultaneous-feeling element by 0.1–0.3s. Check that no two primitives share the same start time.

10. **Test and escalate.** Run it. If it looks messy or cluttered, don't tweak blindly — the choreography might need restructuring, not parameter adjustment. Escalate for design review.

---

## Reference: Claude Code Animations

The original inspiration for this system.

**Thinking spinner:** `·` `✢` `✳` `∗` `✻` `✽` cycling at 120ms intervals with reverse-mirroring. Six glyphs, each one step more complex. The reverse-mirror (blooming then un-blooming) creates a breathing rhythm. The entire animation is one primitive — a sequential glyph cycle — executed with perfect timing.

**Buddy idle fidgets:** 5-line, 12-character-wide ASCII sprites with 3 animation frames on a 500ms tick timer. The frames differ by only 1–3 characters. The subtlety is the point — the creature appears to breathe or shift weight, not perform actions. The eye is drawn because *something changed*, but the brain can't immediately identify *what* changed. This creates a sense of life.

**Key takeaway:** Both animations succeed through *restraint and precision*, not complexity. The game's celebration animations are more elaborate than these references because celebrations are rare, momentous events. But the underlying principle is the same: simple elements, precise timing, meaningful composition.
