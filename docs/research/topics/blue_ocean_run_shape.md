---
name: Blue Ocean Run Shape
description: Blue Ocean tier map for run-shape options A-H feeding Design Lane WS5 Fork 1. Identifies which run shapes are commercially served, partially gapped, or uncontested at depth.
type: topic_brief
captured_at: 2026-05-17
contributor: Research Lane Q2 capture
---

# Blue Ocean — Run Shape Tier Map (Design Lane WS5 Fork 1)

## What this brief is

A Blue Ocean tier map for the eight run-shape options enumerated in Design Lane WS5 Fork 1 (see `/Users/westley/.claude/plans/gentle-rising-compass.md ## Session Pause — 2026-05-16` for the verbatim A–H option list). For each option, the brief identifies which commercial precedents serve that shape, which serve it partially, and which leave a market gap. The brief does not recommend a pick. The Design Lane decides.

## Method

The map is built from the 15-game competitor matrix captured as game cards in `docs/research/games/`. Each game was placed into a primary run-shape bucket based on observed gameplay structure, not marketing language. Tiers reflect commercial precedent density at depth — meaning a shape can be technically attempted by a small game (Tier 2) without being delivered at depth by a hit-quality precedent (which would be Tier 3 served).

## Tier definitions

- **Tier 1 — uncontested at depth.** No commercial game delivers this run shape at hit quality and at the genre scale Ouroboros targets. May have small-scale or adjacent-scale precedents.
- **Tier 2 — partial gap.** Some commercial game serves this shape but with one or more structural mismatches (wrong scale, wrong genre, wrong tactical atom) such that Ouroboros could enter without head-on collision.
- **Tier 3 — served.** One or more hit-quality commercial games own this shape at the relevant scale. Entering means head-on competition.

## Tier map

### Option A — Single continuous run across all eras

**Tier 3 — served.** Owned by Crusader Kings 3 at multi-million-unit hit scale; supported by Old World, Battle Brothers, Star Dynasties at smaller scale. Norland sits here despite being misclassified as F by prior session web AI (see `docs/research/games/norland.md` for the correction). Generational/legacy tribe primary expectation. Entering A means head-on with CK3.

### Option B — Discrete chapters per era

**Tier 3 — served.** Owned by Wildermyth in the narrative-chapter register; King Arthur: Knight's Tale crowds the tactical-chapter register. Different time-scale than Ouroboros' centuries register but commercial precedent is dense.

### Option C — Campaign + sandbox split

**Tier 3 — served.** Owned by Stellaris in the long-game grand-strategy register; common 4X pattern across the genre. Doubles design surface — every game implementing this ships two progression spines. Substrate cost is the gating factor, not market gap.

### Option D — Episodic generational runs (commander lifetime)

**Tier 2 — partial gap.** Closest precedent is Menace at squad-tactical scale (91% / 7,081 reviews on Steam, mid-May 2026, single-campaign-scope). Battle Brothers' company-lifetime structure is adjacent at procedural-roster scale. Massive Chalice attempted this shape at squad scale and underperformed on the dynasty-depth layer, leaving the depth gap open.

### Option E — Persistent world with page-turns

**Tier 3 — served.** Owned by RimWorld at $300M+ lifetime scale; sandbox-sim genre standard. Matches Ouroboros' currently-built code shape but does not deliver a completion beat.

### Option F — Run = full collapse-rebuild ouroboros cycle

**Tier 1 — uncontested at depth, with caveats.** No hit-quality commercial game delivers this run shape at civilization scale. Three relevant data points:

1. **Epoch Cycle** (released January 2026, 73% / ~52 reviews on Steam) attempted F-territory and underperformed on polish + inter-cycle progression depth. Proves the shape is technically contested but not commercially bested.
2. **Massive Chalice** (Double Fine, 2015, 72% / ~1,232 reviews on Steam, ~142k units) attempted dynasty-and-bloodline depth at squad scale; underperformed on the carry-forward depth layer specifically. The mechanism that would make cycle N+1 feel richer than cycle N is the open design problem the prior attempts did not solve.
3. **Against the Storm** (Eremite Games, 2023, **omitted from prior session web AI research**) validates carry-forward-between-runs commercially at city-builder scale. Proof that the carry-forward mechanic can be made to pay off at smaller scale.
4. **Reigns** (Nerial / Devolver, 2016) ships dynasty cycles at card-game scale — closest F precedent in shape but radically smaller in scope, not a competitor in Ouroboros' niche.

F is the largest unmet-need shape in the run-shape fork. The open design problem (carry-forward depth) is real and unsolved at civ scale; the small-scale carry-forward precedent (Against the Storm) is the closest existing template for the mechanism.

### Option G — Time-window run

**Tier 3 — served.** Owned by Battle Brothers (company-lifetime day-counter); Darkest Dungeon ships a crusade-completion variant; common in deterministic-ish run-based games. Arbitrary-cutoff complaint is a known weakness in the shape.

### Option H — Multi-civ relay

**Tier 2 — partial gap.** No direct commercial precedent at civ scale. Foundation-tribe register fits but breaks lieutenant-continuity hardest (lieutenants die when their civ dies). Substrate compatibility with the locked Lieutenant System is the gating concern, not market gap.

## Cross-cutting findings

- **F is the only Tier-1 option.** Every other run shape has at least one hit-quality commercial precedent at relevant scale. F has small-scale attempts and adjacent-scale precedents only.
- **F's open design problem is carry-forward depth.** The shape's commercial failures (Massive Chalice, Epoch Cycle) failed on carry-forward depth specifically, not on the collapse-rebuild concept. A successful F-shape Ouroboros depends on solving what carries forward across collapses.
- **Web AI corrections to prior research.** Prior session web AI made three classification errors: (1) Norland classified as F when it is A; (2) Norland review count overstated 3–4×; (3) Against the Storm omitted entirely from carry-forward precedent analysis. All three are corrected in this brief and in the corresponding game cards.
- **The lieutenant + chronicle substrate already built provides a candidate carry-forward mechanism.** Locked Lieutenant System (`docs/bible/game_bible.md ## In Flux`, 2026-05-16) + chronicle persistence (gated on Q3 chronicle extension cost) could carry forward the lieutenant-narrative layer across cycles. Whether this resolves F's open design problem at depth is a Design Lane question, not a Research Lane recommendation.

## Caveats and confidence

- **Uncontested ≠ proven demand.** Two F-territory attempts (Massive Chalice, Epoch Cycle) underperformed. Blue Ocean does not guarantee a market; it guarantees the absence of head-on commercial competition.
- **Niche-target collision.** Generational/legacy tribe (CK3 + Wildermyth + Battle Brothers + FoG: Empires) primary preference cluster sits at A and F. Foundation/hard-SF tribe preference cluster sits at F and H. F is the only option both clusters support; A serves only the primary cluster.
- **Confidence on each tier classification:** VERIFIED for games with current Steam metrics captured; REPORTED for sales figures (no public per-title audit); ESTIMATED for Battle Brothers and RimWorld lifetime revenue. Individual game cards in `docs/research/games/` carry per-claim confidence tags.

## Feeds Design Lane

This brief feeds Design Lane WS5 Fork 1 directly. It does not pick a Fork 1 option. The Design Lane decides which option to lock; this brief surfaces the commercial landscape that informs the decision.

If Fork 1 lands on F, sub-forks F.1 (carry-forward content) and F.2 (carry-forward mechanism) become the next live design questions, and Against the Storm becomes the most directly relevant precedent for F.2 mechanism design.
