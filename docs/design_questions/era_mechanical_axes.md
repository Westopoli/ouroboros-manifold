# Era Mechanical Axes — Mix-and-Match Identity Matrix

> **Transient working doc.** Drafted to resolve "how do we design hallmark
> and work eras without inventing a new system per era." The deliverable
> is a small set of orthogonal mechanical dials, a matrix positioning the
> 3 launch eras on every dial, and an annotation of which dial positions
> are **Branch DNA** (shared by all eras in a branch) vs. **hallmark-exclusive**
> (reserved for the branch's apex era). Once the matrix stabilizes, its
> content lands in `bible_monetization.md` (Branch System extension) and
> feeds work-era design + Sloyd prompts. This file is deleted when captured.
>
> **Capture targets:** `bible_monetization.md` (Branch System subsection),
> `bible_combat.md` (per-era parameterization re-opens from Session 6),
> `bible_world.md` (map generation gradient consequences).
>
> **Non-goals.** This doc does not invent new engine systems. Every axis
> proposed here must be expressible as per-era config the engine consumes
> uniformly (Sacred Principle #3). Axes that would require engine branching
> on era identity are rejected on sight.

---

## Production Constraints — Apply To Every Axis

These constraints filter which axes survive the pruning pass. Any axis
that violates one of these is cut or rewritten.

- **Solo developer, 20-era catalog.** An axis that costs 20 hours of
  authoring per era per position does not scale. Dial settings must be
  cheap to set — config values, not bespoke systems.
- **Sacred Principle #3.** No engine code branches on era. Dial positions
  must live in per-era config. If a dial requires `if era == "..."` in
  engine code, it's rejected.
- **Must produce noticeably different missions.** An axis whose different
  positions feel like "slightly different stats" is not an axis, it's a
  tuning parameter. Each dial must pass the test: can a player describe
  the difference without looking at numbers?
- **Must be teachable.** The axis vocabulary should be small enough that
  a player learns it once and recognizes it across all eras. Aim for
  5–7 axes total.

---

## Proposed Axis List (first pass)

Seven candidate axes. First three are already locked in `bible_monetization.md`
Branch System. Axes 4–7 are new proposals drafted in this session.

1. **Tempo** *(locked — Branch System)* — engagement duration, movement speed,
   action density per unit time. Fast / medium / slow.

2. **Information warfare** *(locked — Branch System)* — fog density, sensor
   range, cross-layer sight, scout-dependency vs. sensor-dominance.
   Near-total awareness / partial asymmetry / heavy fog.

3. **Attrition / economy** *(locked — Branch System)* — reinforcement rate,
   production density, force preservation value. Rapid recovery / industrial
   replacement / slow reinforcement.

4. **Layer access** *(new — Westley-introduced)* — which unit types can
   physically occupy which layers. Free traversal (SR) / strict lock
   (1980s subs-surface-air) / ground-only (Roman). This is about *where
   units can be*, not about *what units can see* (which is axis 2).

5. **Force scale** *(new — proposed)* — how many units on the field at
   mission peak. Squad (10–20) / company (30–50) / legion (60+). This
   axis controls mission feel in a way nothing else captures — a 15-unit
   skirmish and an 80-unit campaign are different *games*, not different
   missions of the same game.

6. **Terrain expressiveness** *(new — proposed)* — how much map geography
   shapes tactics. Minimum (open space) / mixed (naval archipelago + land
   corridors) / maximum (passes, rivers, defiles dominate). This is the
   axis that lets Roman earn a mechanical identity Branch 1 can't touch
   without contradicting its own branch DNA.

7. **Environmental threat** *(new — proposed, most speculative)* — does
   the environment itself damage or kill units over time, independent of
   enemy action? Vacuum breach, radiation, sonar conditions, heat, cold.
   Low / medium / high. The newest axis and the one I'd most expect you
   to challenge — it's where SR's "magnum opus" status could genuinely
   shine, since environmental hazards in space combat are underused in
   the genre.

---

## What's Coming In Subsequent Batches

Once you react to the axis list (approve / cut / add / rename / reorder):

- **Batch 2:** Flesh out each axis — definition, what different positions
  produce mechanically, implementation cost estimate per position, cross-axis
  interaction risks.
- **Batch 3:** The 7-axis × 3-era matrix. Position Roman / 1980s / Settled
  Reach on every axis with a one-line rationale per cell.
- **Batch 4:** Branch DNA vs. hallmark-exclusive annotations. Which axis
  positions cascade to work eras (Branch 1 DNA) and which are reserved for
  Settled Reach / 1980s only.
- **Batch 5:** Rejected axes (candidates I pruned) + experimental stretch
  axes (ideas that are too novel for the locked set but worth flagging).
  This is where the maximum-creativity proposals live — temporal distortion,
  supply-line tactics, civilian presence, reinforcement topology, and a
  few others.

---

## Questions For Westley Before I Proceed

1. **Do all 7 proposed axes survive, or do you want to cut any on sight?**
   The most speculative is #7 (environmental threat). The most structural
   is #5 (force scale — it has real force-allocator implications).
2. **Any axes I missed entirely** that you already have in mind?
3. **Is the "1 hallmark + 2 work eras" Branch 1 composition the right
   scope for the DNA vs. hallmark-exclusive annotation**, or should I
   also speculate about Branch 1 post-launch eras (4th, 5th era) to
   pressure-test the hallmark-exclusive axis positions?
