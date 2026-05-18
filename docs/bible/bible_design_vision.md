# Ouroboros Manifold — Design Vision

> **⚠ SUPERSEDED BY HUB PIVOT 2026-05-18.** See `game_bible.md ## In Flux ### PIVOT 2026-05-18`. Lieutenant System + multi-era DLC + multiplayer + grand-strategy economy depth KILLED for Phase 1. Pause-tactical reframe locked. Content below preserved for history; not authoritative for Phase 1 ship.

> **Bible spoke. Companion to `game_bible.md`.** This file is part of the bible. The bible-wins-over-spec hierarchy applies. If this file conflicts with `game_bible.md` or another spoke, flag it for Westley — do not silently resolve.
>
> **Modification rule:** Same as the master bible — append-only unless Westley approves deletion.

---

## How To Read This File

This spoke contains two sections with **different binding status**. Read the labels carefully — they govern what the content means and how it should be used.

### Foundational Principles — BINDING

The principles below govern current and future design work. They are at the same authority level as the Sacred Design Principles in `game_bible.md`. Any feature, mechanic, or stage spec must be evaluated against them. A feature that contradicts a foundational principle is a design problem to be resolved, not a tradeoff to be accepted.

These principles do not introduce new mechanical specifications — they constrain how mechanics are designed. They are tests, not implementations.

### Endgame Targets — ASPIRATIONAL, NON-BINDING

The targets below describe the long-term post-launch experience the game is built toward. They are **not** scheduled, **not** required for launch, and **not** binding on current stage specs. They exist in the bible to preserve the vision across years and prevent drift, not to constrain implementation in flight.

Where an Endgame Target conflicts with current launch design, the launch design wins until the target is explicitly scheduled and re-decided. The targets shape future stage specs once they enter scope.

---

## Foundational Principles

### Principle 1 — Skill Ceiling As Design Target

The game is designed to reward mastery growth over hundreds of hours. A skilled player should play *differently* from a new player at the same difficulty — not because they memorized more rules, but because they read the situation more accurately and commit better under uncertainty.

This principle does not state a numeric target. It states a direction: every system should have headroom for skilled play that a new player will not access immediately and may not recognize as available.

The litmus test: *if the optimal play is the same play a new player would make, the system has no skill ceiling.*

This principle extends, but does not replace, the "low floor, high ceiling" heuristic in `game_bible.md` Design Decision Heuristics. That heuristic is binding for all design decisions; this principle elevates the ceiling half to first-class status.

### Principle 2 — Game-Theoretic Depth

Skill in this game means reading the opponent and committing under genuine uncertainty. The game rewards players who think about *what the opponent is likely to do* and *what the opponent thinks the player will do* — not players who execute mechanical sequences faster.

This is a separate principle from skill ceiling because it specifies the *kind* of skill the ceiling is built around. A game can have a high skill ceiling that rewards APM (StarCraft 2's mechanical layer) or memorization (build orders). This game's skill ceiling is built around decision quality under incomplete information.

The litmus test: *would the optimal play change if the player knew exactly what the opponent was going to do?* If no, the system isn't game-theoretic. If yes, it is.

Sacred Design Principle #1 in `game_bible.md` (Genuine stochasticity) is a precondition for this principle — without real uncertainty, there's no game-theoretic substance to reward.

### Principle 3 — Opt-In Complexity

The game must be playable by a casual player who engages only with surface systems, while remaining mechanically deep for a player who engages with everything. Complexity that is not opt-in either excludes casuals or compromises depth — both are design failures.

This principle is already implicit in the bible (Immortal: Gates of Pyre as named design inspiration; "accessible floor" in Design Decision Heuristics). It is elevated here to a named principle so future features can be evaluated against it explicitly.

The litmus test: *can a player who ignores this system still play the game competently? Can a player who masters this system play meaningfully better?* If both answers are yes, the system is opt-in complexity. If either is no, the system is broken.

### Principle 4 — Positional Thinking Over Command Shortcuts

The game's core skill is managing attention across multiple engagements in different locations. Features that allow the player to bypass positional thinking — to command the entire force as a single entity, to ignore where units are while issuing orders — are excluded from the design at all difficulty levels.

This principle bans the all-army hotkey from the base game. It also constrains future features: any UI feature that lets the player command units without thinking about their position is excluded by this principle, regardless of how convenient it would be. Accessibility for new players comes from other affordances (parity tuning, opponent behavior at low difficulties, opt-in assistive toggles labeled as such), not from features that flatten the spatial dimension of play.

Control group exclusive membership (already implemented per `game_bible.md` Track B/B3) is the canonical instance of this principle in the current design. The principle generalizes the rule.

The litmus test: *does this feature let the player issue an order without thinking about where their units are?* If yes, it violates this principle.

**Implementation consequence:** The Stage 8 all-army hotkey decision is flagged for re-opening per this principle. See `bible_combat.md` for the re-open flag. Removal is not scheduled — the launch implementation continues with the all-army hotkey present until a future stage explicitly addresses the conflict.

---

## Endgame Targets

The targets below describe the post-launch game the design is built toward. None are currently scheduled. They are recorded here to preserve the vision and to allow future stage specs to reference a stable target.

### Target 1 — Multi-Perspective Camera System

The current launch design uses a fixed-angle top-down camera. The endgame target is a multi-perspective camera system that lets the player read the battle from whichever angle reveals the situation best.

**Camera presets (target):** top-down, 45° overhead, horizontal, 45° upward, and individual unit POV. Switchable via hotkey, with rapid transitions so the player can re-orient quickly mid-engagement.

**Camera-layer relationship (target):** the camera is **layer-independent**. It can focus on or emphasize a specific layer in view, but it is not bound to any layer. The player chooses what to view; the layer system is spatial state the camera observes. This distinction matters — coupling the camera to a layer would conflate viewing and being, and would break the "commander observing" stance the game requires.

**Design problem deferred:** the control scheme for layer-independent multi-angle cameras is genuinely hard. Solving it is part of the work when this target is scheduled.

**Inspiration:** Ender's Game (the Battle School observation deck — Ender reading the battle from many angles).

**Conflict with current bible:** `game_bible.md` Stage 8 specifies "fixed-angle top-down RTS camera." That decision stands for launch. This target supersedes it only when explicitly scheduled.

### Target 2 — Intelligent Opponent Behavior

The current launch design uses procedural JSON state-machine enemy macro behavior with reactive hooks (`bible_combat.md` Enemy Macro Behavior). The endgame target is opponent behavior that *feels* intelligent at the macro decision layer — feels like the AI is reading the player and committing under uncertainty, not running a script.

**Scope (target):** macro decisions only. When to attack. Where to commit forces. How to react to the player's tempo and positional choices. *Not* unit-level micro behavior, which stays procedural for the foreseeable future. (Micro-level intelligence — taking cover, suppressing, retreating when outflanked, ARMA-style situational behavior — is a possible later expansion of this target. It is not part of the current target scope.)

**Architecture (deliberately not specified):** the target is the *experience*, not the implementation. A learned model (small neural network or similar), an expanded behavior tree system, a hybrid scripted-plus-learned approach, or something else may all be valid paths. The architecture decision belongs to the stage spec that schedules this target, not to this vision document.

**Inspiration:** ARMA's AI behavior at macro tempo. Tron Bike Wars community-level high-skill play (an existence proof that simple-rules + intelligent opposition can sustain a serious skill ceiling).

**Conflict with current bible:** `bible_combat.md` Enemy Macro Behavior specifies the procedural state-machine architecture. That architecture stands for launch and remains the working baseline. This target supersedes it only when explicitly scheduled.

---

## Document Maintenance

### Adding to this spoke

- **Foundational principles** added here must pass the same scrutiny as Sacred Design Principles in `game_bible.md`. They are binding on all current and future work. New principles require Westley's explicit approval.
- **Endgame targets** added here must be clearly aspirational and must explicitly note any conflict with current bible content. New targets do not require re-opening current decisions — they sit alongside them, marked as aspirational.

### Re-opening current bible content

A foundational principle in this spoke may imply that an existing bible decision should be re-opened. When that happens:

1. The implication is documented here in the principle text (see Principle 4's reference to the all-army hotkey).
2. A re-open flag is written into the affected spoke (e.g., `bible_combat.md`).
3. The launch implementation is **not** automatically changed. The flag is a marker for future scheduled work.

### Promoting an endgame target

When an endgame target is scheduled for implementation:

1. The conflicting current bible content is formally re-opened (with Westley's explicit approval per the modification rule).
2. The target is moved from this spoke to its natural home in the bible (e.g., camera system to `bible_combat.md`, AI architecture to a relevant spoke).
3. The Endgame Targets section here is updated — the target is removed and replaced with a back-reference noting where the now-decided design lives.

This keeps the Endgame Targets section honest. Targets in this section are *not yet decided*; targets that have been promoted live in the rest of the bible as decided design.
