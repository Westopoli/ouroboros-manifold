# Stage 9 — UI Shell: Main Menu, Era Library, Mission Briefing, and Game Management

> **LEGACY MONETIZATION MODEL — Replaced 2026-05-09**
>
> Subscription, browser-redirect Stripe checkout, "Manage Subscription" UI, "$2.99 /
> $3–5/mo" pricing, and the key-redemption screen described below have been **scrapped**.
> Steam does not permit linking out to external payment websites from in-game.
>
> **Current model (as of 2026-05-09):**
> - Buy-once base game grants the starting (era 1) civilization of every branch.
> - Additional eras within each branch ship as paid Steam DLC.
> - No subscription, no Stripe, no external website checkout, no in-game key redemption.
> - In-game "Purchase" buttons open the Steam overlay (currently stubbed).
>
> See `docs/bible_history/game_bible_1_23.md (formerly bible_monetization.md, folded into the hub 2026-05-31)` "Current Monetization Model" section for the
> authoritative spec. Stage 9 content below is preserved as implementation history;
> the runtime no longer matches it.

## Goal

Prove that the game's non-combat UI screens are fully navigable, visually polished to the "Terminal Meets Glass" aesthetic spec, and structured with clean data interfaces so the Python backend plugs in with zero visual rework. Every screen renders with mock data, transitions smoothly between scenes, and demonstrates the animation philosophy (staggered fade-slide-in, stat bar growth, blinking cursor heartbeat) at production quality. The UI shell is a complete frontend that a player could walk through end-to-end — Main Menu → New Game → Era Library → Mission Briefing → back — without any backend running.

This is the stage where the game starts *looking* like a product. Stages 1–7 proved that the simulation, narrative, and tactical systems work. Stage 8 proves the tactical renderer works. Stage 9 proves that the screens wrapping around tactical gameplay — the screens the player sees before and after every mission — look and feel like the game described in the bible.

**Architecture: Godot scenes consuming mock data through a data bus.** Every screen reads its display data from a single `UIDataBus` autoload — a GDScript singleton that today returns hardcoded mock data and tomorrow returns live data from the Python backend. No screen ever constructs its own fake data inline. The data bus is the seam. When the backend ships, the bus implementation changes; the scenes don't.

**Out of scope:** Chronicle scroll (requires split-screen world view — deferred to post-backend integration), mission debrief/outcome screen (mid-game mechanism — deferred), tactical HUD (Stage 8), galaxy/world view (deferred), actual payment processing (browser-redirect to Stripe — stubbed, see Security section), server-side entitlement checks (stubbed), actual save file serialization (stubbed — save slots are in-memory mock data).

## Bible References

Read these sections before implementing:

- **`bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/)**: Full file — "UI Aesthetic — Terminal Meets Glass" (core aesthetic principles, animation philosophy, reference mockup), "UI Personality — Celebration Animations and Flavor Text" (key redemption personality, era unlock celebrations, design principles for personality layer), "In-Game Era Library" (storefront description), "Monetization Model" (free tier, trial, subscription, one-time purchase — needed to understand what the Era Library displays), "Access Key System" (three key types — needed for redemption UI), "Player Progression System" (tier progression, era mastery — needed for Era Library per-era detail display), "Marketing Strategy — Product-Led Growth" (UI as marketing — context for polish expectations)
- **`docs/bible_history/bible_2_00_missions.md`**: "Mission Briefing" (three-section structure: situation, objective, assets), "Mission Outcome Resolver" (context only — understanding what data the briefing references)
- **`game_bible.md` (hub)**: "Sacred Design Principles" (era-agnostic architecture — all UI must be theme-neutral with era-specific accent colors injected), "Force and Combat Design" (unit roster summary — needed for mission briefing force display), "Implementation Stage Roadmap" (Stage 9 context)
- **`dev_rules.md`**: Full file — stage spec format, checkpoint discipline, isolation principles

## Cross-Stage References

- **Stages 1–4** established the simulation state model (regions, factions, tech levels, lifecycle phases). The mission briefing screen displays simulation-derived data (region state, faction assessment, commander lineage) — Stage 9 renders this from mock data shaped to match the simulation's actual output format.
- **Stage 5** established the chronicle pipeline, coherence ledger, and naming system. Commander names in the mission briefing come from the ledger. Era Library flavor text references chronicle-quality prose. Stage 9 uses mock names and prose that match the real system's output shape.
- **Stage 5.5** established the mission generator and force allocation. The mission briefing screen displays force composition allocated by Stage 5.5's algorithm. Stage 9 mocks this as a unit type/count list.
- **Stage 6** established the tactical engine and unit roster. The mission briefing's "Your Force" card displays unit types from the 6-unit roster. Stage 9 references unit type names abstractly (the era skin provides display names).
- **Stage 8** established the Godot renderer and WebSocket bridge. Stage 9 scenes coexist with Stage 8's tactical renderer — the mission briefing's "Deploy Forces" button will eventually trigger the transition into Stage 8's combat scene. Stage 9 stubs this transition.

## What to Build

### Architecture Overview

```
res://
├── autoload/
│   ├── ui_data_bus.gd          ← Singleton: all mock data lives here
│   ├── scene_router.gd         ← Singleton: all scene transitions
│   ├── theme_constants.gd      ← Singleton: colors, fonts, timing values
│   └── input_sanitizer.gd      ← Singleton: all user input validation
├── theme/
│   ├── terminal_glass_theme.tres  ← Godot Theme resource
│   ├── fonts/
│   │   ├── JetBrainsMono-*.ttf    ← Monospace family
│   │   └── Newsreader-*.ttf       ← Serif family
│   ├── shaders/
│   │   ├── scanline.gdshader      ← Full-screen CRT overlay
│   │   └── fade_slide.gdshader    ← Reusable entrance animation
│   └── components/
│       ├── tm_card.tscn           ← Reusable card component
│       ├── tm_button.tscn         ← Primary/secondary button styles
│       ├── tm_progress_bar.tscn   ← Animated stat bar
│       ├── tm_section_label.tscn  ← "INTELLIGENCE REPORT" style label
│       ├── tm_divider.tscn        ← Animated horizontal divider
│       └── tm_blinking_cursor.tscn ← The heartbeat cursor
├── scenes/
│   ├── main_menu/
│   │   └── main_menu.tscn + .gd
│   ├── new_game/
│   │   └── new_game.tscn + .gd
│   ├── load_game/
│   │   └── load_game.tscn + .gd
│   ├── era_library/
│   │   ├── era_library.tscn + .gd
│   │   ├── era_detail.tscn + .gd
│   │   └── key_redemption.tscn + .gd
│   ├── mission_briefing/
│   │   └── mission_briefing.tscn + .gd
│   └── settings/
│       └── settings.tscn + .gd
└── assets/
    ├── shaders/
    │   ├── starfield.gdshader        ← Settled Reach atmosphere
    │   ├── ember_drift.gdshader      ← Roman atmosphere
    │   └── wave_surface.gdshader     ← 1980s atmosphere
    └── celebrations/
        ├── celebration_base.gd       ← Base class: shader + glyph bloom system
        ├── roman_unlock.gd           ← Roman era unlock
        ├── settled_reach_unlock.gd   ← Settled Reach era unlock
        ├── era_1980s_unlock.gd       ← 1980s era unlock
        └── key_redemption.gd         ← Key redemption animations
```

### Security Architecture

The game client will handle microtransactions and sensitive entitlement data. Security is designed in from the start, not bolted on later. Three principles govern all security decisions in this stage:

**Principle 1 — The game client never touches payment.** All purchases (era packs, subscriptions, tier skips) use a browser-redirect flow. The game requests a checkout session from the server, the server creates a Stripe Checkout Session and returns the opaque Stripe-generated URL, the game opens the user's default browser to that URL. No session tokens, player IDs, or purchase parameters appear in the URL — the Stripe checkout URL is opaque and server-side-bound. After the user completes (or cancels) checkout, the game polls for entitlement changes on regain-focus. The game never sees card numbers, payment tokens, or Stripe API keys. PCI compliance is entirely Stripe's responsibility. In Stage 9 (mock mode), purchase buttons call `UIDataBus.initiate_purchase()` which simulates this flow by logging the request and showing a placeholder modal. The real implementation replaces this with the server call + `OS.shell_open()`.

**Principle 2 — All user input is sanitized at the boundary.** Every text field the user can type into (save slot names, key redemption codes) passes through `InputSanitizer` before the value is used anywhere. No raw user input is ever concatenated into file paths, passed to OS functions, stored unsanitized, logged verbatim, or displayed without validation. The sanitizer is a single autoload — every input field in the game calls it, no exceptions.

**Principle 3 — The client leaks nothing about its internals.** Error messages shown to the player are generic and pre-authored — never generated from exception text, stack traces, file paths, server responses, or internal state. Debug/diagnostic logging is disabled in release builds via a compile-time flag. No internal data structures (entitlement tokens, server URLs, API endpoints, session state, internal IDs beyond what's needed for display) are exposed through the UI, stored in user-accessible files, or printed to the Godot console in release mode. The settings file on disk (`user://settings.cfg`) contains only display/audio preferences — never entitlement data, session tokens, or player account information.

**Purchase flow architecture (stubbed in Stage 9, real in backend integration):**

```
Player clicks "Purchase" in Era Detail
        │
        ▼
UIDataBus.initiate_purchase(era_id)
        │
        ├── [MOCK MODE — Stage 9] Show placeholder modal:
        │   "This will open your browser for secure checkout."
        │
        └── [LIVE MODE — future] Game client calls server:
            POST /api/checkout/create
            Body: {era_id, auth_credential}
            (auth_credential is a short-lived token from the
            session, never a password or long-lived secret)
                    │
                    ▼
            Server creates Stripe Checkout Session
            Returns: {checkout_url: "https://checkout.stripe.com/c/pay/cs_live_..."}
            (Stripe URL is opaque — no player data in URL)
                    │
                    ▼
            Game calls OS.shell_open(checkout_url)
            Browser opens, player completes checkout on Stripe's page
                    │
                    ▼
            Stripe webhook → server updates entitlement DB
                    │
                    ▼
            Game polls UIDataBus.refresh_entitlements() on window focus
            Era Library updates to reflect new access
```

**Subscription management** follows the same pattern — "Manage Subscription" opens the browser to a server-hosted account management page. The game client never renders subscription modification UI.

### Input Sanitization Rules

All user-facing text inputs in the game follow these rules, enforced by `InputSanitizer`:

**Save slot names:**
- Maximum length: 64 characters (enforced at the LineEdit level via `max_length` and validated again by the sanitizer).
- Allowed characters: Unicode letters, digits, spaces, hyphens, and em-dashes. Everything else is stripped.
- Specifically blocked: path separators (`/`, `\`), null bytes, control characters (0x00–0x1F), angle brackets (`<`, `>`), quotes (`"`, `'`), backticks, semicolons, pipe characters, dollar signs, percent signs, braces, brackets, ampersands, equals signs.
- Leading/trailing whitespace is trimmed.
- Empty string after sanitization is rejected — the UI falls back to the default name.
- The sanitized name is what gets stored. The user sees the sanitized version in real time as they type (blocked characters are silently dropped, not replaced with placeholder text).

**Key redemption codes:**
- Maximum length: 32 characters.
- Allowed characters: A–Z, 0–9, hyphens. All lowercase input is uppercased. Everything else is stripped.
- This is a strict alphanumeric-plus-hyphen format — no possibility of injection through this field.

**General sanitization function:** `InputSanitizer.sanitize(raw: String, rule: String) → String` where `rule` is one of `"save_name"`, `"key_code"`. The function applies the appropriate rule set and returns the cleaned string. All text input nodes call this in their `text_changed` signal handler.

### Information Exposure Rules

These rules apply to every screen in Stage 9 and carry forward to all future stages:

**Error messages are pre-authored, never dynamic.** When something fails, the player sees one of a fixed set of error strings. Examples:
- Key redemption failure: "Invalid key. Check the code and try again." — never "Server returned 404" or "KeyError: code not found in database" or any server/internal detail.
- Purchase flow failure: "Unable to connect to the store. Please try again later." — never a URL, endpoint, or HTTP status code.
- Save slot creation failure: "Could not create save. Please try a different name." — never a file path or OS error.
- Generic fallback: "Something went wrong. Please try again."

The error string set is defined in `ThemeConstants` (or a dedicated `error_messages.gd` resource) so they're centralized and auditable. No screen constructs error messages from dynamic data.

**No internal IDs in player-visible UI.** The `mission_id_label` field in mission briefings (e.g., "OP-2741") is a display-only label generated for flavor — it is not the internal mission ID used by the engine. Internal IDs (UUIDs, database keys, slot array indices) never appear in rendered UI text, even in debug builds. The `UIDataBus` maps between internal IDs and display labels; scenes only see display labels.

**Logging discipline:**
- A compile-time constant `IS_RELEASE_BUILD: bool` in `ThemeConstants` (default `false` during development, set to `true` for distribution builds).
- All `print()` calls in UI code are wrapped: `if not ThemeConstants.IS_RELEASE_BUILD: print(...)`. In release builds, the game prints nothing to the Godot console.
- Even in debug mode, `print()` calls never include: raw user input (print the sanitized version), entitlement tokens or session data, server URLs or API endpoints, file paths outside the project directory, stack traces (use Godot's built-in error reporting, which is suppressed in release builds).

**Settings file security:**
- The settings file (`user://settings.cfg`) is a Godot `ConfigFile` containing only: display settings (resolution, fullscreen, vsync) and audio volumes. It is human-readable on purpose — there is nothing sensitive in it.
- Entitlement data, subscription status, session tokens, and player account information are **never** written to any local file. All entitlement state is queried from the server at runtime (in live mode) or from in-memory mock data (in Stage 9 mock mode). If the game crashes, no sensitive state persists on disk.
- Save slot metadata (name, era, template, chapter, generation, playtime) is stored locally but contains no sensitive information — it's the same data the player sees on screen.

**Scene router param safety:**
- The `SceneRouter.go_to(scene_name, params)` function validates `scene_name` against the hardcoded scene registry. If `scene_name` is not in the registry, the call is silently ignored (no error message, no crash, no fallback to a default scene that might expose state). This prevents any hypothetical injection through navigation params.
- The `params` dictionary is never serialized to disk, never logged in release builds, and never exposed to the player. It exists only in memory for the duration of a scene transition.

### Files to create

**`autoload/theme_constants.gd`** — The single source of truth for all visual values. Contains:
- **Background colors:** `BASE` (#0a0a0c), `SURFACE` (#111114), `CARD` (#18181c), `ELEVATED` (#1f1f24).
- **Text colors:** `PRIMARY` (#e8e6e1), `SECONDARY` (PRIMARY at 55% opacity), `TERTIARY` (PRIMARY at 30% opacity).
- **Semantic colors:** `DANGER` (#c44a3f), `INFO` (#5a8fbf), `HEALTHY` (#4a9e6e).
- **Era accent colors:** A dictionary keyed by era ID string. `"roman"` → `#c9a84c` (warm gold). `"settled_reach"` → `#4a9eb8` (cool blue-teal). `"1980s"` → `#8b9a3c` (military olive). Each era also defines an `ACCENT_DIM` variant (accent at 15% opacity for backgrounds) and `ACCENT_BORDER` (accent at 30% opacity for borders).
- **Border values:** `BORDER_WIDTH` (0.5px equivalent — Godot uses integer pixels, so 1px with low-opacity color), `BORDER_COLOR` (white at 8% opacity), `BORDER_RADIUS` (6px).
- **Typography sizes:** `CLASSIFICATION_LABEL` (10px mono, letter-spacing 3px), `SECTION_LABEL` (9px mono, letter-spacing 2.5px), `ERA_BADGE` (9px mono), `TITLE` (28px serif, weight 400), `SUBTITLE` (14px serif italic), `BODY_NARRATIVE` (14.5px serif, weight 300, line-height 1.75), `BODY_DATA` (12px mono), `BODY_DATA_SMALL` (11px mono), `HINT_TEXT` (10px mono), `BUTTON_PRIMARY` (11px mono, weight 500), `BUTTON_SECONDARY` (11px mono).
- **Animation timing:** `STAGGER_BASE_DELAY` (0.2s), `STAGGER_INCREMENT` (0.15s), `ELEMENT_ANIM_DURATION` (0.5s), `EASE_CURVE` (Godot ease type — cubic ease-out), `STAT_BAR_DURATION` (1.0s), `CURSOR_BLINK_INTERVAL` (1.0s), `DIVIDER_EXPAND_DURATION` (0.5s).
- **Font loading:** Preloaded font resources for JetBrains Mono (Regular, Medium, Bold) and Newsreader (Regular, Light, Italic, Medium).
- Helper function: `get_era_accent(era_id: String) → Color` — returns the accent color for the given era, defaulting to a neutral gray if era ID is unrecognized.
- Helper function: `get_era_accent_dim(era_id: String) → Color` — returns the dim accent variant.

**`autoload/input_sanitizer.gd`** — Input validation singleton. Contains:
- `sanitize(raw: String, rule: String) → String` — Main entry point. Applies the rule set identified by `rule` and returns the cleaned string. Unrecognized rule names return an empty string (fail closed, not open).
- Rule `"save_name"`: strips all characters not matching `[\\p{L}\\p{N}\\s\\-—]` (Unicode letters, digits, whitespace, hyphens, em-dashes), trims leading/trailing whitespace, truncates to 64 characters. Returns empty string if result is only whitespace.
- Rule `"key_code"`: uppercases, strips all characters not matching `[A-Z0-9\\-]`, truncates to 32 characters.
- `is_valid(raw: String, rule: String) → bool` — Returns true if `sanitize(raw, rule)` produces a non-empty string. Convenience method for enable/disable logic on buttons.
- All sanitization is pure string manipulation — no regex engine dependency, no eval, no dynamic code execution. Implemented with character-by-character filtering loops.
- **No logging of raw input.** Even in debug mode, the sanitizer never prints the unsanitized string. It may print the sanitized output for debugging, gated behind `IS_RELEASE_BUILD`.

**`autoload/scene_router.gd`** — Scene transition manager. Contains:
- **Scene registry:** A dictionary mapping scene names to file paths:
  ```
  "main_menu"        → "res://scenes/main_menu/main_menu.tscn"
  "new_game"         → "res://scenes/new_game/new_game.tscn"
  "load_game"        → "res://scenes/load_game/load_game.tscn"
  "era_library"      → "res://scenes/era_library/era_library.tscn"
  "era_detail"       → "res://scenes/era_library/era_detail.tscn"
  "key_redemption"   → "res://scenes/era_library/key_redemption.tscn"
  "mission_briefing" → "res://scenes/mission_briefing/mission_briefing.tscn"
  "settings"         → "res://scenes/settings/settings.tscn"
  ```
- **Transition function:** `go_to(scene_name: String, params: Dictionary = {})` — Validates `scene_name` against the scene registry (rejects unregistered names silently — no error message, no crash). Fades current scene out (0.3s opacity tween), loads new scene, passes `params` to the new scene's `setup(params)` method if it exists, fades in (0.3s opacity tween). The params dictionary carries context: `go_to("era_detail", {"era_id": "roman"})`, `go_to("mission_briefing", {"mission_id": "mock_001"})`. Params are never serialized to disk or logged in release builds.- **Back stack:** `go_back()` pops the last scene from a navigation stack and transitions to it. Every `go_to` call pushes the current scene onto the stack. The Main Menu clears the stack.
- **Transition overlay:** A full-screen `ColorRect` in the autoload's canvas layer, used for the fade animation. Always on top.

**`autoload/ui_data_bus.gd`** — Mock data provider. The seam between UI and backend. Contains:
- All data-fetching functions return typed dictionaries matching the shapes defined in "Input/Output Shapes" below.
- **MOCK_MODE flag:** `const MOCK_MODE: bool = true` — When true, all functions return hardcoded mock data. When false, they query the backend. The kill switch for backend integration.
- **IS_RELEASE_BUILD flag:** References `ThemeConstants.IS_RELEASE_BUILD` for logging discipline. In mock mode with release build off, data bus functions may print sanitized debug info. In release mode, nothing is printed.
- **Era data:** `get_all_eras() → Array[Dictionary]`, `get_era_detail(era_id: String) → Dictionary`. Returns mock data for 3 eras (Roman, Settled Reach, 1980s) with all fields populated: id, name, description, accent_color, is_free, is_owned, is_trial, trial_missions_remaining, subscription_required, tier_progress (current tier, progress percentage), mastery_progress (percentage), unit_roster (list of 6 unit type entries with abstract type, era display name, category, tier), sample_chronicle_text.
- **Save slot data:** `get_save_slots() → Array[Dictionary]`, `create_save_slot(era_id: String, template_id: String, name: String) → Dictionary`, `delete_save_slot(slot_id: String) → bool`. The `name` parameter is sanitized through `InputSanitizer.sanitize(name, "save_name")` before use — the data bus never stores unsanitized input. Mock save slots stored in an in-memory array. Each slot: id, name, era_id, template_id, chapter (int), generation (int), playtime_seconds (int), last_played_timestamp (String), era_accent_color. The `id` field is a generated UUID, never exposed in UI — scenes use it internally for data bus lookups but display the `name` field.
- **Template data:** `get_starting_templates() → Array[Dictionary]`. Returns 3 templates: Isolated Start, Twin Colony, Archipelago. Each: id, name, description (one-sentence summary of the topology and feel).
- **Mission briefing data:** `get_mission_briefing(mission_id: String) → Dictionary`. Returns a single mock briefing with all fields from the reference mockup: mission_title, mission_subtitle, mission_id_label (display-only flavor label — not the internal ID), chapter, generation, era_id, situation_text, objective_primary (text + archetype + success_spectrum_label), objectives_secondary (array), enemy_assessment (faction_name, archetype_label, military_stat, military_stat_max, tech_tier, behavior_tag), player_force (parity_percentage, unit_list: array of {type_abstract, type_display_name, category, count}), region_state (name, tier, economy, military, tension — each with value and max), commander_lineage (name, generation_number, predecessor_name, predecessor_status), reinforcement_note.
- **Entitlement data:** `get_subscription_status() → Dictionary` — Returns mock subscription state: {active: bool, plan_name: String, renewal_date: String}. `is_era_accessible(era_id: String) → bool` — mock entitlement check. `refresh_entitlements() → void` — In mock mode, no-op. In live mode, polls the server for updated entitlements and refreshes cached access state. Called on window focus regain after a browser-redirect purchase flow.
- **Purchase flow:** `initiate_purchase(era_id: String, purchase_type: String) → void` — `purchase_type` is one of `"era_pack"`, `"subscription"`, `"tier_skip"`, `"manage_subscription"`. In mock mode: shows a placeholder modal "This will open your browser for secure checkout. (Mock mode — no purchase processed.)" In live mode: calls the server's checkout session endpoint, receives the opaque Stripe checkout URL, calls `OS.shell_open(url)`. The function never constructs URLs from parameters — the server returns the complete URL. No player ID, session token, era ID, or price appears in any URL.
- **Key redemption:** `redeem_key(code: String) → Dictionary` — The `code` parameter is sanitized through `InputSanitizer.sanitize(code, "key_code")` before use. Mock redemption accepts specific hardcoded test codes ("TESTPERM001" → permanent Roman unlock, "TESTTIME001" → 30-day all-access, "TESTTRIAL01" → 5-mission 1980s trial). Returns {success: bool, key_type: String, era_ids: Array[String], era_names: Array[String], duration_label: String, missions_granted: int, flavor_message: String}. Any other code returns {success: false, error_display: "Invalid key. Check the code and try again."} — note the field is `error_display`, a pre-authored user-facing string, never a raw server error.
- **Settings data:** `get_settings() → Dictionary`, `save_settings(settings: Dictionary)`. Settings stored via Godot `ConfigFile` at `user://settings.cfg`. Contains only: {master_volume: int, music_volume: int, sfx_volume: int, narration_volume: int, resolution_index: int, fullscreen: bool, vsync: bool}. **No sensitive data is ever written to this file** — no entitlements, no tokens, no account info, no player ID. The `save_settings` function validates all values are within expected ranges before writing (volumes 0–100, resolution_index within bounds, booleans are booleans). Out-of-range values are clamped, not rejected — defense in depth against corrupted config files.
- **Error handling pattern:** All data bus functions that can fail return a dictionary with a `success` boolean. On failure, the dictionary includes an `error_display` field containing a pre-authored, player-safe error message. Functions never propagate raw exceptions, server responses, or internal error details to the calling scene.

**`theme/terminal_glass_theme.tres`** — Godot Theme resource. Contains:
- Base style overrides for all standard Godot control nodes (Panel, Button, Label, HScrollBar, VScrollBar, ProgressBar, LineEdit) using the colors and fonts from `theme_constants.gd`.
- Panel: `CARD` background, `BORDER_COLOR` border at 1px, `BORDER_RADIUS` corner radius.
- Button (normal): transparent background, `SECONDARY` text, 1px `BORDER_COLOR` border, `BORDER_RADIUS` corners. Button (hover): border brightens to white at 15% opacity, text brightens to `PRIMARY`. Button (pressed): background `SURFACE`, text `PRIMARY`.
- Label: `PRIMARY` color, JetBrains Mono Regular, 12px default.
- LineEdit: `SURFACE` background, `PRIMARY` text, 1px `BORDER_COLOR` border, JetBrains Mono Regular.
- ProgressBar: `SURFACE` background, `INFO` fill by default (overridden per-instance with semantic colors).

**`theme/shaders/scanline.gdshader`** — Full-screen post-processing overlay. Contains:
- A fragment shader that draws faint alternating horizontal lines: transparent / rgba(0,0,0,0.03) at 2px/4px intervals based on screen-space UV coordinates.
- Applied as a `CanvasLayer` with a full-screen `ColorRect` in every scene (or as a persistent autoload overlay).
- Parameterized: `uniform float opacity : hint_range(0.0, 0.1) = 0.03` so intensity is tunable.

**`theme/components/tm_card.tscn`** — Reusable card component. Contains:
- A `PanelContainer` with `CARD` background, 1px border at `BORDER_COLOR`, `BORDER_RADIUS` corners, 14px horizontal / 16px vertical padding (matching the bible mockup spec).
- Exported properties: `card_title: String` (rendered as a `SECTION_LABEL` at the top), `show_title: bool`.
- A `VBoxContainer` child for content injection — card users add children to this container.
- Entrance animation method: `animate_in(delay: float)` — fades from 0 opacity + 8px Y offset to final position over `ELEMENT_ANIM_DURATION` after the specified delay.

**`theme/components/tm_button.tscn`** — Button component with two variants. Contains:
- Exported enum property: `style: {PRIMARY, SECONDARY}`.
- PRIMARY: accent-colored background (set per-instance via `accent_color` export), dark text (#0a0a0c), 11px JetBrains Mono Medium, 3px border-radius, 10px horizontal / 8px vertical padding.
- SECONDARY: transparent background, `SECONDARY` text, 1px `BORDER_COLOR` border, same typography and padding.
- Hover: PRIMARY brightens background 10%, SECONDARY brightens border and text.
- Click animation: brief scale pulse (0.97× over 0.05s, back to 1.0× over 0.1s).

**`theme/components/tm_progress_bar.tscn`** — Animated stat bar. Contains:
- A custom `Control` node (not Godot's built-in ProgressBar — custom drawing for precise control).
- Exported properties: `value: float` (0.0–1.0), `max_display_value: float` (for the label), `bar_color: Color`, `label_text: String`, `show_label: bool`, `show_value: bool`.
- On `animate_in(delay: float)`: bar width scales from 0 to target over `STAT_BAR_DURATION` with ease timing, starting after the delay.
- The bar background is `SURFACE`, the fill is `bar_color`, height is 4px, with 2px border-radius.
- When `show_value` is true, the numeric value renders to the right of the bar in `BODY_DATA_SMALL` monospace, and counts up from 0 to the target value synchronized with the bar animation.

**`theme/components/tm_section_label.tscn`** — Section header label. Contains:
- A `Label` styled as `SECTION_LABEL`: 9px JetBrains Mono, `TERTIARY` color, letter-spacing 2.5px, all-uppercase transform.
- Exported property: `text: String`.

**`theme/components/tm_divider.tscn`** — Animated horizontal line. Contains:
- A `ColorRect` with height 1px, color white at 8% opacity.
- On `animate_in(delay: float)`: horizontal scale from 0 (centered) to full width over `DIVIDER_EXPAND_DURATION` after the delay.

**`theme/components/tm_blinking_cursor.tscn`** — The heartbeat indicator. Contains:
- A `ColorRect` 1px wide, 14px tall (matching body text line height), colored with the current era's accent color.
- Blinks with a step function: 1.0 opacity for 0.5s, 0.0 for 0.5s, repeating infinitely.
- Exported property: `cursor_color: Color` (defaults to accent, overridable).

---

**`scenes/main_menu/main_menu.tscn + .gd`** — The game's entry point. Contains:

*Layout:*
- Full-screen `BASE` background.
- Center-left composition (content at ~35% from left edge, vertically centered).
- Game title "OUROBOROS MANIFOLD" in `CLASSIFICATION_LABEL` style (10px mono, letter-spacing 3px, `TERTIARY` color) above a large serif title rendering of the game name or a stylized logotype (28px+ Newsreader, `PRIMARY`).
- Below the title: a vertical stack of menu items, each rendered in 14px JetBrains Mono Regular, `SECONDARY` color, with 20px vertical spacing:
  - "NEW GAME"
  - "CONTINUE" (grayed out / hidden if no save slots exist — check `UIDataBus.get_save_slots()`)
  - "ERA LIBRARY"
  - "SETTINGS"
  - "QUIT"
- Below the menu stack, separated by spacing: a subtle prompt in `HINT_TEXT` style — "Have an access key? Visit the Era Library to redeem it." — in `TERTIARY` color. This is the key redemption nudge.
- Bottom-right corner: version number in `HINT_TEXT` style, `TERTIARY` color.

*Interaction:*
- Menu items highlight on hover: text color transitions to `PRIMARY`, a faint horizontal accent line (2px wide, era accent color — use a default accent for the menu since no era is active; use `SECONDARY` as the neutral accent) slides in from the left of the hovered item.
- Click triggers `SceneRouter.go_to()` with the appropriate target.
- "QUIT" calls `get_tree().quit()`.

*Animation:*
- On scene load: staggered fade-slide-in per the bible spec. Title first (0.2s delay), then menu items cascade (each +0.15s), then the key hint (last), then version number.
- Scanline overlay active.

---

**`scenes/new_game/new_game.tscn + .gd`** — New game configuration. Contains:

*Layout:*
- Full-screen `BASE` background.
- Header: "NEW GAME" in `CLASSIFICATION_LABEL` style, top-left.
- Two-step flow rendered as a single screen with two columns (or a two-step wizard — see below):

*Step 1 — Era Selection (left column or first step):*
- Section label: "SELECT ERA".
- A vertical list of unlocked era cards (pulled from `UIDataBus.get_all_eras()`, filtered to accessible eras via `UIDataBus.is_era_accessible()`).
- Each era card: a `tm_card` showing era name in serif (accent-colored), one-line description in `SECONDARY` mono, and an era badge (e.g., "FREE", "TRIAL — 3 MISSIONS LEFT", "SUBSCRIBED") in `ERA_BADGE` style.
- Locked eras shown below with reduced opacity and a lock indicator + "Visit Era Library" hint.
- Clicking an unlocked era card selects it (highlight border shifts to that era's accent color).

*Step 2 — Template Selection (right column or second step, visible after era is selected):*
- Section label: "SELECT STARTING TEMPLATE".
- Three template cards (from `UIDataBus.get_starting_templates()`), each a `tm_card`:
  - Template name in 14px mono, `PRIMARY`.
  - Template description in 12px serif, `SECONDARY`.
  - A simple ASCII topology diagram rendered in monospace showing the template's region layout (e.g., `[H]--[F]--[F]--[ ]--[ ]` for Isolated Start). These are hardcoded per template — 3 small ASCII art pieces.
- Clicking a template card selects it.

*Game naming:*
- Below the template selection: a `LineEdit` for naming the save slot. `max_length` set to 64. Placeholder text: "Name this campaign..." in `TERTIARY`. Default: "{Era Name} — {Template Name}".
- The `text_changed` signal handler calls `InputSanitizer.sanitize(text, "save_name")` and writes the sanitized result back to the `LineEdit`. Blocked characters are silently dropped in real time.
- The "BEGIN" button is disabled if the sanitized name is empty.

*Footer:*
- "BEGIN" button (`tm_button` PRIMARY style, accent-colored to the selected era) — enabled only when era + template are both selected. Clicking calls `UIDataBus.create_save_slot()` and then `SceneRouter.go_to("mission_briefing", {mission_id: "mock_001"})` (stubbed — in the real game this would trigger the simulation and first mission generation).
- "BACK" button (`tm_button` SECONDARY) → `SceneRouter.go_back()`.
- Keyboard hint: "ESC to return" in `HINT_TEXT`.

*Animation:*
- Staggered entrance per standard. Era cards cascade. Template cards cascade after era selection with a brief delay.

---

**`scenes/load_game/load_game.tscn + .gd`** — Save slot browser. Contains:

*Layout:*
- Full-screen `BASE` background.
- Header: "CONTINUE" in `CLASSIFICATION_LABEL` style.
- A vertical scrolling list of save slot cards (from `UIDataBus.get_save_slots()`).
- Each save slot card is a `tm_card` with the slot's era accent color as a 2px left border:
  - Top line: save name in 14px mono, `PRIMARY`.
  - Second line: era name (era accent color) + template name in 12px mono, `SECONDARY`.
  - Third line: "Chapter {N}, Generation {N}" in 11px mono, `TERTIARY`.
  - Right-aligned: playtime (formatted as "12h 34m") and last played date ("3 days ago" or "Apr 5, 2026") in 10px mono, `TERTIARY`.
  - A delete button (small, `DANGER` color, "×" or trash icon) at the far right. Clicking triggers a confirmation modal: "Delete this save? This cannot be undone." with "DELETE" (`DANGER` background) and "CANCEL" (secondary) buttons. Confirming calls `UIDataBus.delete_save_slot()`.
- If no save slots exist: centered message in `SECONDARY` serif — "No saved campaigns. Start a new game to begin."

*Interaction:*
- Clicking a save slot card (outside the delete button) loads it — `SceneRouter.go_to("mission_briefing", {slot_id: slot.id})` (stubbed).
- "BACK" button and ESC → `SceneRouter.go_back()`.

*Animation:*
- Staggered entrance: header, then save slot cards cascade top to bottom.

---

**`scenes/era_library/era_library.tscn + .gd`** — The in-game storefront. Contains:

*Layout:*
- Full-screen `BASE` background.
- Header zone:
  - "ERA LIBRARY" in `CLASSIFICATION_LABEL` style, top-left.
  - Subscription status badge, top-right: if active, "SUBSCRIBED — {plan_name}" in `HEALTHY` color mono with a subtle green-tinted background. If inactive, "FREE TIER" in `SECONDARY` mono. Below it: "Manage Subscription" link in `HINT_TEXT` — clicking calls `UIDataBus.initiate_purchase("", "manage_subscription")` which in mock mode shows a placeholder modal and in live mode opens the browser to the account management page.
  - Divider below header.

*Era grid:*
- A responsive grid of era cards (2–3 per row depending on window width). Each era card is a `tm_card` sized approximately 300×400px:
  - Top section: a colored banner area (60px tall) filled with the era's `ACCENT_DIM` background, containing the era name in serif (accent color, 20px) and an era badge beneath it.
  - Era badges (mutually exclusive, in `ERA_BADGE` style):
    - Free era: "FREE" in `HEALTHY` on `HEALTHY`-dim background.
    - Owned (purchased): "OWNED" in accent on accent-dim background.
    - Subscribed (access via subscription): "SUBSCRIBED" in `INFO` on `INFO`-dim background.
    - Trial: "TRIAL — {N} MISSIONS LEFT" in accent on accent-dim background.
    - Locked: "LOCKED" in `TERTIARY` on `SURFACE` background.
  - Body: 2–3 line thematic description in 12px serif, `SECONDARY`.
  - Bottom section:
    - Tier progression: "TIER {N}/3" with a `tm_progress_bar` showing tier progress (accent color fill).
    - Mastery: "MASTERY" with a `tm_progress_bar` (accent color fill, dimmer).
    - For locked eras: a price indicator ("$2.99" or "Included with subscription") in 11px mono, `SECONDARY`.
  - Clicking an era card navigates: `SceneRouter.go_to("era_detail", {era_id: era.id})`.

*Key redemption entry point:*
- Below the era grid or in a fixed bottom bar: a `tm_card` styled distinctively — slightly different border (accent-colored, dashed or dotted) with an icon or ASCII decoration:
  - "REDEEM ACCESS KEY" in 12px mono, `PRIMARY`.
  - Subtext: "Enter a key code to unlock eras, trials, or subscription time." in 10px mono, `TERTIARY`.
  - Clicking navigates: `SceneRouter.go_to("key_redemption")`.

*Footer:*
- "BACK" button → `SceneRouter.go_back()`.
- Keyboard hint: "ESC to return".

*Animation:*
- Header + subscription badge stagger in, divider expands, era cards cascade in grid order (left-to-right, top-to-bottom), key redemption card last.

---

**`scenes/era_library/era_detail.tscn + .gd`** — Individual era deep-dive. Receives `{era_id}` param. Contains:

*Layout:*
- Full-screen `BASE` background.
- The entire screen uses the selected era's accent color as the active accent.
- Header: era name in `TITLE` serif (accent color), era badge below. "ERA DOSSIER" classification label above the title.
- Divider.

*Two-column layout:*

*Left column — narrative and preview:*
- Section: "THEMATIC OVERVIEW" — 3–5 sentences of era description in `BODY_NARRATIVE` serif. This is marketing prose — it should sell the era's fantasy.
- Section: "SAMPLE CHRONICLE" — a mock chronicle entry rendered in the full Terminal Meets Glass style (opening + detail fragment, variable slots filled with era-appropriate mock data). Demonstrates what the narrative looks like in this era.
- Section: "UNIT ROSTER" — a list of the 6 unit types for this era. Each entry: abstract category icon/label (Strike/Line/Siege) in `TERTIARY`, era display name in mono `PRIMARY` (e.g., "Legionary" for Roman Vanguard, "Destroyer" for 1980s Vanguard), one-line role description in `SECONDARY`. Tier badge (Tier 1/2/3) next to names, with locked tiers shown dimmed.

*Right column — progression and purchase:*
- Card: "TIER PROGRESSION" — visual tier display. Three tier slots (1, 2, 3) shown as horizontal segments. Unlocked tiers are accent-colored and filled. Locked tiers are `SURFACE` with a lock indicator. Current progress toward next tier shown as a `tm_progress_bar` below. If all tiers unlocked: "ALL TIERS UNLOCKED" in accent. Tier skip purchase option: "Skip to Tier 3 — ~$1" button (stubbed).
- Card: "ERA MASTERY" — mastery progress bar (long bar, accent fill) with percentage label. Below it: a brief description of mastery rewards in `HINT_TEXT` ("Earn cosmetic rewards, achievement badges, and era-specific doctrines through sustained play.").
- Card: "ACCESS" — shows how the player has access:
  - If free: "This era is free for all players." in `HEALTHY`.
  - If owned: "You own this era permanently." in `HEALTHY`.
  - If subscribed: "Included with your subscription." in `INFO`. Below: "Purchase permanently — $2.99" button.
  - If trial: "Trial — {N} missions remaining." in accent. Below: "Subscribe for full access" and "Purchase — $2.99" buttons.
  - If locked: "Subscribe for full access — $3–5/mo" and "Purchase — $2.99" buttons.
  - All purchase/subscribe buttons call `UIDataBus.initiate_purchase(era_id, purchase_type)`. In mock mode, this shows a modal: "This will open your browser for secure checkout. (Mock mode — no purchase processed.)" styled as a centered `tm_card` overlay with a dismiss button. In live mode, this opens the user's browser to the Stripe checkout page — no payment UI ever renders inside the game.
  - "Manage Subscription" (visible when subscribed) calls `UIDataBus.initiate_purchase("", "manage_subscription")` — same browser-redirect pattern to the account management page.

*Footer:*
- "BACK TO ERA LIBRARY" button → `SceneRouter.go_back()`.
- Keyboard hint.

*Animation:*
- Full stagger sequence per the bible reference mockup timing: classification label (0.2s) → title (0.4s) → subtitle/badge (0.55s) → divider (0.5s) → left column content (0.65s) → right column cards cascade (0.7s, 0.85s, 1.0s) → footer (1.15s).

---

**`scenes/era_library/key_redemption.tscn + .gd`** — Key redemption with personality layer. Contains:

*Layout:*
- Full-screen `BASE` background.
- Centered content area (max-width ~500px, vertically centered).
- "REDEEM ACCESS KEY" in `CLASSIFICATION_LABEL` style above.
- A large `LineEdit` for the key code input: monospace, 16px, accent-colored text, `SURFACE` background, 1px border, letter-spacing 2px. `max_length` set to 32. Placeholder: "ENTER-YOUR-KEY-HERE".
- The `text_changed` signal handler calls `InputSanitizer.sanitize(text, "key_code")` and writes the sanitized, uppercased result back to the `LineEdit`. Non-alphanumeric/non-hyphen characters are silently dropped.
- "REDEEM" button (`tm_button` PRIMARY) below the input. Disabled while `InputSanitizer.is_valid(text, "key_code")` returns false.
- "BACK" button (`tm_button` SECONDARY).

*Redemption flow — success:*
1. Player enters code, clicks REDEEM.
2. `UIDataBus.redeem_key(code)` called. Brief loading state (blinking cursor animation in the center, "VALIDATING..." in `TERTIARY` mono).
3. On success, the input and buttons fade out.
4. **Celebration animation plays** (see "Celebration Animation System" section below). For key redemptions: a smaller, quicker animation from the `key_redemption.gd` variant pool (1.5–1.8s, no shader background, plays within the content area). For era unlocks triggered by the key: the full era celebration animation plays after the key redemption animation.
5. After the animation completes (~3 seconds): the flavor message renders in mono, accent-colored, with a typewriter effect (one character at a time, 30ms per character). Example: *"huh — you must know somebody"* for a permanent key.
6. Beat (0.5s pause).
7. Standard confirmation renders below in `PRIMARY` mono: "1980s Era — permanently unlocked." (or time/mission details for other key types).
8. "CONTINUE" button appears, returning to Era Library. The newly unlocked era's card will now show the updated badge.

*Redemption flow — failure:*
1. Input border briefly flashes `DANGER` color.
2. The `error_display` string from the response is rendered below the input in `DANGER` mono. This is always a pre-authored message (e.g., "Invalid key. Check the code and try again.") — never a raw server error or internal detail.
3. Input remains editable for retry.

*Animation:*
- Entrance: staggered as standard. The input field has a focus animation — border transitions to accent color when focused.

---

**`scenes/mission_briefing/mission_briefing.tscn + .gd`** — The hinge screen. Receives `{mission_id}` or `{slot_id}` param. Contains:

This screen is implemented pixel-accurately to the reference mockup in `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/), section "Reference mockup — Mission Briefing Screen (Roman era)." All values below are from that spec.

*Header zone:*
- Top-left: "MISSION BRIEFING" in `CLASSIFICATION_LABEL` style (10px mono, letter-spacing 3px, accent color). Below it: "{mission_id} // Chapter {N} // Generation {N}" in 10px mono, `TERTIARY`.
- Title in 28px Newsreader, weight 400, `PRIMARY`. Below: one-line subtitle in 14px Newsreader italic, `SECONDARY`.
- Top-right: era badge ("{ERA} ERA" in `ERA_BADGE` style — accent on accent-dim background, 0.5px accent-tinted border, 2px radius) and a simulation tick counter with `tm_blinking_cursor` appended.
- `tm_divider` spanning full width below the header.

*Left column — narrative:*
- `tm_section_label`: "INTELLIGENCE REPORT".
- Briefing text in `BODY_NARRATIVE` Newsreader, weight 300, line-height 1.75, `SECONDARY`. Key data (military numbers, tick counts) rendered in `PRIMARY` weight 400. Faction and character names in accent color, weight 400.
- Below narrative: `tm_section_label` "MISSION OBJECTIVES".
- Objective card: a `tm_card` variant with a 2px left border in accent color, 6px border-radius on right side only. Primary objective in 12px mono, `PRIMARY`. Objective metadata (archetype, success spectrum label) in 11px mono, `TERTIARY`.
- Secondary objectives (if any) listed below, same card style, slightly indented.

*Right column — four data cards stacked:*
- **Card 1 — "ENEMY ASSESSMENT":** Faction name (accent), archetype label (mono), military stat with `tm_progress_bar` (`DANGER` color for high values), tech tier label, behavior tag (e.g., "DEFENSIVE POSTURE — RARE COMMITTED ATTACK" in 9px mono, `INFO` on `INFO`-dim background, 0.5px `INFO`-tinted border).
- **Card 2 — "YOUR FORCE":** Parity percentage with `tm_progress_bar` (`INFO` fill). Unit type list: each line has a 4px accent-colored circle dot indicator, abstract type display name (era-skinned), and count (e.g., "Legionary ×4"). Rendered in 12px mono.
- **Card 3 — "REGION STATE":** Region name, tier label. Economy / military / tension values each with a `tm_progress_bar` using semantic colors (`HEALTHY` for economy, `DANGER` for depleted military or high tension, accent for moderate values). Values shown as numbers next to bars.
- **Card 4 — "COMMANDER LINEAGE":** Commander name (accent), "Generation {N}" in `TERTIARY`. Predecessor: "{name} — {status}" where status uses semantic color (`DANGER` for "KIA — {location}"). If no predecessor (generation 1): "First of the line." in serif italic, `TERTIARY`.
- Below Card 3: a serif italic note in `TERTIARY` about reinforcement expectations (from `reinforcement_note` in the data).

*Footer zone:*
- Left: "DEPLOY FORCES" (`tm_button` PRIMARY, accent background) and "REVIEW CHRONICLE" (`tm_button` SECONDARY). DEPLOY FORCES is stubbed — shows a modal "Combat deployment will connect to the tactical engine." REVIEW CHRONICLE is stubbed similarly.
- Right: keyboard hints in 10px mono, `TERTIARY` — "ESC to return to galaxy view // TAB for force details".
- "BACK" button or ESC → `SceneRouter.go_back()`.

*Animation:*
- Full stagger sequence matching the bible spec exactly: classification label (0.2s) → title (0.4s) → subtitle (0.55s) → divider expand (0.5s) → narrative body (0.65s) → right column cards cascade (0.7s, 0.85s, 1.0s, 1.15s) → footer (1.2s). Stat bars within cards animate to their values as each card fades in.

---

**`scenes/settings/settings.tscn + .gd`** — Client-side settings. Contains:

*Layout:*
- Full-screen `BASE` background.
- Header: "SETTINGS" in `CLASSIFICATION_LABEL` style.
- Divider.
- Settings organized into `tm_card` groups:

*Card 1 — "DISPLAY":*
- Resolution: dropdown (OptionButton styled to theme) listing common resolutions. Current selection from `UIDataBus.get_settings().resolution_index`.
- Fullscreen: toggle (CheckButton styled — accent-colored when on, `SURFACE` when off). Label: "Fullscreen" in 12px mono.
- VSync: toggle. Label: "VSync".
- These three settings are **functional** — they call Godot's `DisplayServer` methods to apply immediately on change.

*Card 2 — "AUDIO":*
- Master Volume: horizontal slider (HSlider styled — accent fill, `SURFACE` track) with percentage label. Range 0–100.
- Music Volume: same style.
- SFX Volume: same style.
- Narration Volume: same style.
- Sliders are **functional** — they set Godot's `AudioServer` bus volumes (buses "Master", "Music", "SFX", "Narration" — created in the project's default audio bus layout). Even without audio files, the bus volumes are correctly set so future audio plays at the right level.

*Card 3 — "KEYBINDS" (display only):*
- A read-only list of the current keybind mappings displayed in a two-column format: action name (12px mono, `SECONDARY`) and key (12px mono, `PRIMARY`). Actions listed: Select (LMB), Box Select (LMB Drag), Move (RMB), Attack Move (A + RMB), Stop (S), Control Group Assign (Ctrl+1–9), Control Group Select (1–9), All Army (F1), Ability (Q), Layer Up (PageUp), Layer Down (PageDown), Sensor Pulse (Space).
- A note at the bottom: "Keybind customization coming soon." in `HINT_TEXT`.

*Footer:*
- "APPLY" button (saves settings via `UIDataBus.save_settings()`) and "BACK" button. Settings auto-apply on change for display/audio, so APPLY is mainly a confirmation action that also saves to disk.
- ESC → `SceneRouter.go_back()`.

*Animation:*
- Standard stagger entrance.

---

### Celebration Animation System — Shader + Glyph Bloom Hybrid

> **Design philosophy:** Inspired by Claude Code's animations — the thinking spinner (`·` `✢` `✳` `∗` `✻` `✽` blooming at 120ms intervals) and Buddy's idle fidgets (3-frame, 500ms tick, subtle character changes). The principle: individual elements are simple, *composition and timing* create the effect. No animation tries to draw a picture from ASCII characters. Instead, a full-screen shader creates atmospheric mood, and carefully chosen Unicode glyphs bloom, radiate, and pulse around the era title text.

**Two-layer architecture:**
- **Layer 1 — Shader atmosphere (background).** A full-screen Godot shader creates the era's visual mood: drifting particles, gentle gradients, organic motion. The shader runs dimmed (20–30% opacity) so it doesn't overpower the text. It provides warmth and depth without requiring any character rendering. The shader is mathematically smooth — impossible to make cheesy because there are no discrete characters pretending to be something they're not.
- **Layer 2 — Glyph bloom + title resolve (foreground).** Unicode decorative characters bloom outward from the center in timed sequences, using the era's accent color. The era title resolves through a character-shuffle effect (each position rapidly cycles through random glyphs before landing on the correct letter — like an airport departure board). The glyphs are abstract and decorative, not representational. They don't try to be columns or submarines. They're pure visual rhythm.

**`assets/shaders/starfield.gdshader`** — Settled Reach atmosphere shader. Contains:
- A fragment shader that renders point-like stars at pseudo-random positions derived from UV coordinates and a time uniform.
- Stars twinkle via sine-wave opacity modulation at varying frequencies (each star gets a different phase offset derived from its position hash).
- A slow, barely perceptible parallax drift — stars shift position slightly over time, creating a sense of depth. Closer stars (brighter, larger) drift faster than distant ones (dimmer, smaller).
- Parameterized: `uniform float density` (star count), `uniform float drift_speed`, `uniform float twinkle_speed`, `uniform vec3 tint_color` (set to Settled Reach teal).
- Total visual feel: staring into deep space from a command bridge. Calm, vast, alive.

**`assets/shaders/ember_drift.gdshader`** — Roman atmosphere shader. Contains:
- A fragment shader that renders warm, ember-like particles drifting upward.
- Particles are soft circles (smoothstep falloff) in the Roman gold accent color at low opacity, spawning at random horizontal positions near the bottom and rising with slight horizontal sway (sine modulation).
- Particles fade in as they spawn and fade out as they approach the top third of the screen.
- A subtle warm gradient underlies everything — the bottom 20% of the screen has a barely perceptible warm glow (gold at 3–5% opacity).
- Parameterized: `uniform float particle_count`, `uniform float rise_speed`, `uniform vec3 ember_color`.
- Total visual feel: the warmth of a forge or a torchlit senate chamber. Ancient, warm, measured.

**`assets/shaders/wave_surface.gdshader`** — 1980s atmosphere shader. Contains:
- A fragment shader that renders horizontal wave lines across the bottom third of the screen.
- Waves are sine functions at different frequencies and amplitudes, offset vertically, drawn as thin lines (1–2px) in the 1980s olive accent at low opacity. Three to four overlapping wave functions create organic motion.
- The wave lines oscillate horizontally over time, creating the feel of a sonar display or ocean surface viewed from above.
- Above the wave zone: nothing. Clean dark space. The contrast between the active wave zone and the empty space above is the composition.
- Parameterized: `uniform float wave_count`, `uniform float wave_speed`, `uniform vec3 wave_color`.
- Total visual feel: a sonar screen on a submarine. Tense, precise, military.

**`assets/celebrations/celebration_base.gd`** — Base class for all celebration animations. Contains:
- Extends `Control`. Full-screen node that manages both the shader layer and the glyph layer.
- **Shader layer:** A `ColorRect` child with a `ShaderMaterial`. The base class loads the appropriate shader, sets uniforms (colors from `ThemeConstants.get_era_accent()`), and handles fade-in/fade-out of the shader background.
- **Glyph layer:** A set of `Label` nodes managed in a pool, each rendering a single Unicode character. The base class handles creation, positioning, animation, and cleanup of these labels.
- Core methods:
  - `play(era_id: String)` — Starts the full animation sequence. Emits `animation_finished` when complete.
  - `_get_shader() → Shader` — Override in subclasses. Returns the atmosphere shader for this era.
  - `_get_glyph_set() → Array[String]` — Override in subclasses. Returns the set of Unicode glyphs used in the bloom sequence.
  - `_get_bloom_sequence() → Array[Dictionary]` — Override in subclasses. Returns the choreography for the glyph bloom (positions, timings, scales).
  - `_get_title_text() → String` — Override in subclasses. Returns the era title to resolve.

- **Glyph bloom primitive** — `bloom_ring(center: Vector2, glyphs: Array[String], count: int, radius: float, delay: float, duration: float)`:
  Places `count` glyphs evenly spaced in a ring around `center` at `radius` distance. Each glyph fades in from 0 opacity, scales from 0.5× to 1.0×, holds briefly, then fades out. The ring expands slightly during the animation (radius grows 10–15%). Glyphs are drawn from the provided set in order, cycling if `count > glyphs.size()`. Stagger: each glyph's fade-in is offset by `duration / count / 3` from the previous, creating a clockwise sweep rather than all appearing at once.

- **Glyph bloom primitive** — `bloom_scatter(center: Vector2, glyphs: Array[String], count: int, radius: float, delay: float, duration: float)`:
  Like `bloom_ring` but glyphs are placed at random positions within `radius` of `center`. Each glyph fades in, drifts outward slightly (10–20px over its lifetime), and fades out. Creates a breathing, organic particle feel.

- **Title resolve primitive** — `resolve_title(text: String, center: Vector2, delay: float, char_interval: float, scramble_duration: float)`:
  The core title reveal. Each character position starts cycling through random glyphs from the era's glyph set at 60ms intervals (the "departure board" scramble). After `scramble_duration` (0.4–0.6s per character, staggered by `char_interval` from left to right), each position locks to its final letter. The final title is rendered in Newsreader serif at `TITLE` size in the era's accent color. The scramble characters use JetBrains Mono at a slightly smaller size, creating a visual "snap" when the serif letter locks in — the font change itself is part of the reveal.

- **Cleanup:** When the animation finishes, all glyph labels are freed, the shader fades to 0 opacity over 0.3s, and the `animation_finished` signal fires.

**`assets/celebrations/roman_unlock.gd`** — Roman era unlock. Extends `celebration_base.gd`. Contains:
- Shader: `ember_drift.gdshader` with Roman gold tint.
- Glyph set: `["✦", "✧", "◆", "❖", "✶", "⬥", "◈", "✴"]` — angular, gem-like, evoking carved stone and metalwork.
- Sequence:
  - **Phase 1 (0–1.2s):** Shader fades in over 0.5s. Two `bloom_ring` calls fire in quick succession — a small ring (radius 80px, 6 glyphs) at 0.3s delay, then a larger ring (radius 160px, 10 glyphs) at 0.6s delay. Both centered on screen. Gold accent color. The rings create a sense of ornamental framing, like a decorative seal expanding.
  - **Phase 2 (1.2–2.8s):** `resolve_title("ROMAN", center, 1.2, 0.12, 0.5)` fires. Each letter scrambles through the gem-like glyphs for 0.5s before locking. The title resolves left to right over ~1.6s total. During the resolve, a subtle `bloom_scatter` (20 glyphs, radius 200px, gold at 40% opacity) fires around the title, creating ambient sparkle.
  - **Phase 3 (2.8–3.5s):** Everything holds for a beat (0.3s). Then the glyph scatter fades, the bloom rings fade, the title holds at full opacity for 0.4s, then the shader fades out. `animation_finished` emits.

**`assets/celebrations/settled_reach_unlock.gd`** — Settled Reach era unlock. Extends `celebration_base.gd`. Contains:
- Shader: `starfield.gdshader` with teal tint.
- Glyph set: `["·", "✧", "✦", "✶", "✹", "✺", "✻", "✽"]` — the Claude Code spinner set, extended. Dot-to-bloom progression. Evoking stars resolving from noise into clarity.
- Sequence:
  - **Phase 1 (0–1.5s):** Shader fades in over 0.8s (slower than Roman — the starfield needs time to breathe). A sequence of 5 `bloom_scatter` calls fire at 0.2s intervals, each with increasing radius (40, 80, 120, 160, 200px) and increasing glyph count (3, 5, 8, 10, 12). The glyphs progress through the set — early scatters use dots and small stars, later scatters use the larger bloom characters. The effect: a field of stars resolving from pinpoints to detailed glyphs, radiating outward from center. Teal accent color.
  - **Phase 2 (1.5–3.0s):** `resolve_title("SETTLED REACH", center, 1.5, 0.08, 0.4)` fires. Faster `char_interval` than Roman (more characters to resolve). The scramble uses the dot-to-bloom glyph set, so each position looks like a star twinkling before it resolves into a letter. During the resolve, the starfield shader subtly brightens (twinkle_speed uniform increases) — the stars react to the title appearing.
  - **Phase 3 (3.0–3.8s):** The scattered glyphs slowly fade while drifting outward (mimicking the starfield's parallax). Title holds. Shader dims back to base level, then fades. `animation_finished` emits.

**`assets/celebrations/era_1980s_unlock.gd`** — 1980s era unlock. Extends `celebration_base.gd`. Contains:
- Shader: `wave_surface.gdshader` with olive tint.
- Glyph set: `["─", "━", "═", "▪", "▫", "◽", "◾", "■"]` — horizontal lines and blocks. Geometric, military, precise. No curves. Evoking radar blips and sonar returns.
- Sequence:
  - **Phase 1 (0–1.2s):** Shader fades in over 0.4s (quick, military). A single horizontal line of `─` characters draws across the center of the screen, left to right, character by character at 20ms intervals (total ~0.6s for a full line). This is a sonar sweep line. As it completes, a brief `bloom_ring` (radius 100px, 8 glyphs using the block characters, olive accent) fires at center.
  - **Phase 2 (1.2–2.6s):** `resolve_title("1980s", center, 1.2, 0.15, 0.5)` fires. Slower, more deliberate character interval than the other eras — military precision. The scramble uses the geometric glyph set, so each position looks like a radar display cycling through returns. During the resolve, the horizontal sweep line fades out.
  - **Phase 3 (2.6–3.3s):** Two more `bloom_ring` calls at 2.6s and 2.8s — concentric rings expanding outward from the title, like sonar pings radiating. The rings use `▪` and `▫` alternating. Title holds. Rings fade. Shader fades. `animation_finished` emits.

**`assets/celebrations/key_redemption.gd`** — Key redemption personality animations. Contains:
- Unlike era unlocks, key redemptions do NOT use a shader background. The animation is smaller, quicker, and more intimate — it plays within the key redemption screen's centered content area, not full-screen.
- Glyph set: `["✓", "✔", "⚡", "✦", "✧", "·", "✢", "✳", "✻", "✽"]` — the Claude Code spinner set plus check marks and a lightning bolt.
- **3 variants** (randomly selected per redemption):

- **Variant 1 — Bloom burst (1.5s):** A single `bloom_ring` (radius 60px, 8 glyphs) fires centered on where the key input was. As the ring expands, a `✓` character scales up from 0× to 1.5× at center in the accent color, then settles to 1.0×. Quick, satisfying, like a stamp of approval. The ring glyphs use the spinner set, blooming from dots to flowers.

- **Variant 2 — Departure board resolve (1.8s):** The key code the user entered transforms in place. Each character of the code scrambles (cycling through random glyphs at 40ms) and one by one resolves into `✓` characters, left to right, at 0.1s intervals. When all characters are checks, the entire row pulses with the accent color once, then the checks scatter outward via `bloom_scatter` and fade. Playful, acknowledges the key the player typed.

- **Variant 3 — Cascade unlock (1.5s):** A vertical cascade of the spinner glyph sequence (`·` → `✢` → `✳` → `✻` → `✽`) plays at three positions — left of center, center, right of center — staggered by 0.15s. Each cascade blooms upward (4 glyphs stacked, each one appearing 0.08s after the previous, each one a more complex glyph). At the peak, all three cascades simultaneously resolve their top glyph into `✦` at full accent brightness. A horizontal line of `─` connects the three peaks briefly (0.3s), then everything fades down. Structured, rhythmic, satisfying.

---

### Scanline Overlay

**`autoload/scanline_overlay.gd`** — A persistent `CanvasLayer` (layer 100, always on top) containing a full-screen `ColorRect` with the `scanline.gdshader` applied. Added as an autoload so it persists across all scenes. The overlay is purely cosmetic and does not intercept input (`mouse_filter = IGNORE` on all children).

---

## Input/Output Shapes

All data flowing through `UIDataBus` uses these shapes. These are the interface contracts — when the backend replaces mock data, it must produce these exact shapes.

### Era Data

```gdscript
# UIDataBus.get_all_eras() returns Array of:
{
    "id": "roman",                           # String — unique era identifier
    "name": "Roman",                         # String — display name
    "description": "Command the legions...", # String — 2-3 sentence thematic pitch
    "accent_color": "#c9a84c",               # String — hex color
    "is_free": true,                         # bool
    "is_owned": true,                        # bool — permanently purchased
    "is_trial": false,                       # bool — trial access active
    "trial_missions_remaining": 0,           # int — 0 if not trial
    "subscription_required": false,          # bool — needs sub for access
    "tier_progress": {
        "current_tier": 2,                   # int — 1, 2, or 3
        "progress_to_next": 0.45,            # float 0.0-1.0 — progress toward next tier
        "max_tier_unlocked": 2               # int — highest tier earned
    },
    "mastery_progress": 0.12,               # float 0.0-1.0
    "unit_roster": [
        {
            "abstract_type": "raider",       # String — engine type name
            "display_name": "Velites",       # String — era-specific name
            "category": "strike",            # String — strike/line/siege
            "tier": 1,                       # int — which tier this stat profile is
            "role_description": "Fast flanking skirmishers." # String
        }
        # ... 6 entries total, one per unit type
    ],
    "sample_chronicle_text": "In the autumn of the third year..." # String — preview prose
}
```

### Save Slot Data

```gdscript
# UIDataBus.get_save_slots() returns Array of:
{
    "id": "slot_001",                        # String — unique slot ID
    "name": "Roman — Isolated Start",        # String — player-chosen name
    "era_id": "roman",                       # String — era identifier
    "era_name": "Roman",                     # String — era display name
    "template_id": "isolated_start",         # String
    "template_name": "Isolated Start",       # String
    "chapter": 1,                            # int
    "generation": 1,                         # int
    "playtime_seconds": 4500,                # int
    "last_played_timestamp": "2026-04-05T14:30:00Z", # String — ISO 8601
    "era_accent_color": "#c9a84c"            # String — hex
}
```

### Starting Template Data

```gdscript
# UIDataBus.get_starting_templates() returns Array of:
{
    "id": "isolated_start",
    "name": "Isolated Start",
    "description": "A single homeland pushing outward into the unknown. Straightforward, good for learning.",
    "ascii_diagram": "[H]──[F]──[F]──[ ]──[ ]──[ ]"  # String — monospace topology preview
}
```

### Mission Briefing Data

```gdscript
# UIDataBus.get_mission_briefing(mission_id) returns:
{
    "mission_id_label": "OP-2741",           # String — display ID
    "chapter": 3,                            # int
    "generation": 7,                         # int
    "era_id": "roman",                       # String
    "mission_title": "The Siege of Thessalonica",  # String — serif title
    "mission_subtitle": "A Fortifier pushes south with overwhelming force", # String — serif italic
    "tick_counter": 48205,                   # int — current simulation tick

    "situation_text": "The Northern Confederation has marshaled...", # String — full briefing prose
    # Within situation_text, special markup for inline styling:
    # {accent}Name{/accent} for accent-colored text
    # {strong}42{/strong} for primary-weight data values

    "objective_primary": {
        "text": "Hold the southern wall until reinforcements arrive.",
        "archetype": "Rear Guard",
        "success_spectrum_label": "EXTRACTION UNDER FIRE"
    },
    "objectives_secondary": [
        {"text": "Preserve the garrison supply depot.", "weight_label": "SECONDARY"}
    ],

    "enemy_assessment": {
        "faction_name": "Northern Confederation",
        "archetype_label": "FORTIFIER",
        "military_stat": 72,
        "military_stat_max": 100,
        "tech_tier": 2,
        "behavior_tag": "DEFENSIVE POSTURE — RARE COMMITTED ATTACK"
    },

    "player_force": {
        "parity_percentage": 85,
        "units": [
            {"type_abstract": "vanguard", "type_display_name": "Legionary", "category": "line", "count": 4},
            {"type_abstract": "warden", "type_display_name": "Medicus", "category": "line", "count": 2},
            {"type_abstract": "raider", "type_display_name": "Velites", "category": "strike", "count": 3},
            {"type_abstract": "interceptor", "type_display_name": "Equites", "category": "strike", "count": 2},
            {"type_abstract": "bombard", "type_display_name": "Onager", "category": "siege", "count": 1},
            {"type_abstract": "bastion", "type_display_name": "Testudo", "category": "siege", "count": 1}
        ]
    },

    "region_state": {
        "name": "Thessalonica",
        "tier": "Frontier",
        "economy": {"value": 45, "max": 100},
        "military": {"value": 28, "max": 100},
        "tension": {"value": 67, "max": 100}
    },

    "commander_lineage": {
        "name": "Lucius Aurelius",
        "generation_number": 7,
        "predecessor_name": "Marcus Aurelius",
        "predecessor_status": "KIA — Naissus"  # or "Retired — Roma" or null if gen 1
    },

    "reinforcement_note": "Local military infrastructure degraded — expect sparse reinforcements from regional garrisons."
}
```

### Subscription Status

```gdscript
# UIDataBus.get_subscription_status() returns:
{
    "active": false,
    "plan_name": "",          # String — "Monthly" or "Annual" when active
    "renewal_date": ""        # String — ISO 8601 or empty
}
```

### Key Redemption Result

```gdscript
# UIDataBus.redeem_key(code) returns:
# NOTE: code is sanitized through InputSanitizer before reaching this function
{
    "success": true,
    "key_type": "permanent",          # "permanent", "time_limited", "mission_limited"
    "era_ids": ["roman"],             # Array[String] — eras affected
    "era_names": ["Roman"],           # Array[String] — display names
    "duration_label": "",             # String — "30 days" for time-limited, "" for permanent
    "missions_granted": 0,            # int — for mission-limited keys
    "flavor_message": "huh — you must know somebody"  # String — personality text
}
# On failure:
{
    "success": false,
    "error_display": "Invalid key. Check the code and try again."
    # error_display is ALWAYS a pre-authored string, never a raw server error.
    # The set of possible error_display values is finite and pre-defined.
}
```

### Settings

```gdscript
# UIDataBus.get_settings() returns:
{
    "master_volume": 80,       # int 0-100
    "music_volume": 70,        # int 0-100
    "sfx_volume": 80,          # int 0-100
    "narration_volume": 90,    # int 0-100
    "resolution_index": 2,     # int — index into resolution list
    "fullscreen": false,       # bool
    "vsync": true              # bool
}
```

## Integration Points

### With Stage 8 (Godot Renderer)

The mission briefing's "DEPLOY FORCES" button will eventually trigger a scene transition into Stage 8's tactical combat scene. For now, it's stubbed with a modal. The integration point is:
- `SceneRouter.go_to("tactical_combat", {mission_setup: ...})` — this scene name is reserved but not implemented in Stage 9.
- When Stage 8 integrates, it registers its combat scene in the router's scene registry.

### With Python Backend (Future)

The `UIDataBus` is the sole integration seam. To connect the backend:
1. Replace the mock data implementations in `ui_data_bus.gd` with calls to the Python backend over the WebSocket bridge (same bridge Stage 8 uses for tactical state).
2. No scene files change. No component files change. Only `ui_data_bus.gd` internals change.

### Config Flags

- `UIDataBus.MOCK_MODE: bool = true` — When true, all data functions return hardcoded mock data. When false, they query the backend. Default: true. This is the kill switch — flip it to false when the backend is ready.
- `ThemeConstants.IS_RELEASE_BUILD: bool = false` — When true, all `print()` calls are suppressed, debug overlays are hidden, and no internal state is logged to the Godot console. Set to `true` for distribution builds. Default: false during development.

## Implementation Plan — Checkpoints and Parallelism

### Phase 0 — Sequential Foundation (must complete before parallel work)

**Step 0A: Project Setup and Font Installation** ✅ COMPLETE
- Created the Godot project directory structure.
- Downloaded and installed JetBrains Mono (Regular, Medium, Bold, Italic) and Newsreader (Regular, Light, Medium, Italic) font files into `theme/fonts/`.
- Updated `project.godot` with autoload registrations, audio bus layout, display settings (1920×1080, canvas_items stretch), main scene set to main_menu.
- Created `default_bus_layout.tres` with Master, Music, SFX, Narration buses.

**Step 0B: Theme Constants** ✅ COMPLETE
- Implemented `autoload/theme_constants.gd` with all color, typography, and animation values.
- **Note for retrofit:** Missing `IS_RELEASE_BUILD` flag — added in Step 0G.

**Step 0C: Shared Components** ✅ COMPLETE
- Implemented all `theme/components/` scenes and scripts: `tm_card`, `tm_button`, `tm_progress_bar`, `tm_section_label`, `tm_divider`, `tm_blinking_cursor`.
- Implemented `theme/shaders/scanline.gdshader` and `theme/shaders/fade_slide.gdshader`.
- Implemented `autoload/scanline_overlay.gd`.
- Implemented `theme/terminal_glass_theme.tres`.
- **Note:** Visual checkpoint was not performed. Westley should visually verify components match the bible aesthetic during Phase 1 screen builds.

**Step 0D: Scene Router** ✅ COMPLETE
- Implemented `autoload/scene_router.gd` with scene registry, `go_to()`, `go_back()`, fade transitions.
- **Note for retrofit:** Missing registry validation on `go_to()` — patched in Step 0G.

**Step 0E: UI Data Bus — Mock Data** ✅ COMPLETE (pre-security)
- Implemented `autoload/ui_data_bus.gd` with mock data functions for eras, save slots, templates, mission briefings, settings, and key redemption.
- Settings persistence via ConfigFile implemented.
- **Note for retrofit:** Missing `initiate_purchase()`, `refresh_entitlements()`, `error_display` pattern, and InputSanitizer calls — patched in Step 0G.

**Step 0F: Input Sanitizer** ❌ NOT STARTED
- `input_sanitizer.gd` does not exist. Created in Step 0G.

**Step 0G: Security Retrofit** ❌ NOT STARTED — DO THIS NEXT
> The security architecture (Section "Security Architecture" above) was added to the spec after Phase 0 was initially implemented. This step patches all existing Phase 0 files to comply with the security requirements and creates the missing InputSanitizer. **All Phase 0 files must be read before making changes** — the existing implementations are functional and should be patched, not rewritten from scratch.

Sub-steps (implement sequentially, checkpoint after each):

**0G-1: Create `autoload/input_sanitizer.gd`**
- Implement the full InputSanitizer singleton as specified in the "Files to create" section.
- Two rule sets: `"save_name"` (Unicode letters, digits, spaces, hyphens, em-dashes; 64 char max) and `"key_code"` (A-Z, 0-9, hyphens; auto-uppercase; 32 char max).
- `sanitize(raw, rule)` and `is_valid(raw, rule)` methods.
- Unrecognized rule names return empty string (fail closed).
- No logging of raw input, ever.
- Register as an autoload in `project.godot`: `InputSanitizer="*res://autoload/input_sanitizer.gd"`
- **Checkpoint:** Test with adversarial inputs (run from a test script or Godot's script editor):
  - `sanitize("My Campaign", "save_name")` → `"My Campaign"` (passthrough)
  - `sanitize("../../../etc/passwd", "save_name")` → `"etcpasswd"` (path separators stripped)
  - `sanitize("<script>alert(1)</script>", "save_name")` → `"scriptalert1script"` (angle brackets, parens stripped)
  - `sanitize("name\x00with\x01nulls", "save_name")` → `"namewithnulls"` (control chars stripped)
  - `sanitize("  ", "save_name")` → `""` (whitespace-only → empty → invalid)
  - `sanitize("ABC-123-def", "key_code")` → `"ABC-123-DEF"` (uppercased)
  - `sanitize("ABC'; DROP TABLE keys;--", "key_code")` → `"ABCDROPTABLEKEYS"` (only A-Z, 0-9, hyphens survive)
  - `sanitize("", "unknown_rule")` → `""` (unrecognized rule fails closed)
  - Print all results. Verify each matches expected output. **STOP for Westley review.**

**0G-2: Patch `autoload/theme_constants.gd` — add IS_RELEASE_BUILD**
- Add `const IS_RELEASE_BUILD: bool = false` at the top of the file, below the existing constants.
- Add a comment: `# Set to true for distribution builds. Gates all print() calls and debug output.`
- Do not modify any existing constants or functions.
- **Checkpoint:** Verify the constant exists and is `false`. Quick — no need to stop for review, proceed to 0G-3.

**0G-3: Patch `autoload/scene_router.gd` — add registry validation**
- Read the existing `scene_router.gd` first.
- In the `go_to()` function, add a validation check at the top: if `scene_name` is not a key in the `SCENES` dictionary, return silently (no error message, no crash, no print in release mode). In debug mode, print a warning gated behind `not ThemeConstants.IS_RELEASE_BUILD`.
- Ensure the `params` dictionary is never logged in release mode. If any existing `print()` calls exist, gate them behind `not ThemeConstants.IS_RELEASE_BUILD`.
- **Checkpoint:** Call `SceneRouter.go_to("nonexistent_scene")` from a test script. Verify: no crash, no navigation, no console output when `IS_RELEASE_BUILD = true`. **STOP for Westley review.**

**0G-4: Patch `autoload/ui_data_bus.gd` — security hardening**
- Read the existing `ui_data_bus.gd` first — it's 356 lines. Do not rewrite, only patch.
- **Add `initiate_purchase(era_id: String, purchase_type: String) → void`:** In mock mode, emit a signal or call a method that the active scene can listen for to show a placeholder modal: "This will open your browser for secure checkout. (Mock mode — no purchase processed.)" The function never constructs URLs from parameters.
- **Add `refresh_entitlements() → void`:** No-op in mock mode. Add a comment: `# In live mode: polls server for updated entitlements after browser-redirect purchase.`
- **Patch `create_save_slot()`:** Add `name = InputSanitizer.sanitize(name, "save_name")` as the first line. If the sanitized name is empty, fall back to a default name ("{era} — {template}").
- **Patch `redeem_key()`:** Add `code = InputSanitizer.sanitize(code, "key_code")` as the first line. Change the failure return to use `"error_display"` as the key (instead of `"error"` if that's what the current implementation uses). Verify the error message is the pre-authored string "Invalid key. Check the code and try again." — not a dynamic message.
- **Patch all `print()` calls:** Gate every existing `print()` behind `if not ThemeConstants.IS_RELEASE_BUILD:`.
- **Patch `save_settings()`:** Add value range clamping before writing — volumes clamped to 0–100, resolution_index clamped to valid range, booleans verified as booleans. Don't crash on invalid data, just clamp.
- **Checkpoint:** Run a test script that:
  - Calls `create_save_slot("roman", "isolated_start", "<script>alert('xss')</script>")` and prints the returned slot — verify the name is sanitized.
  - Calls `redeem_key(";DROP TABLE keys;--")` and prints the result — verify it returns `{success: false, error_display: "Invalid key. Check the code and try again."}`.
  - Calls `initiate_purchase("roman", "era_pack")` — verify it doesn't crash (the modal display will be wired to a scene in Phase 1).
  - Sets `ThemeConstants.IS_RELEASE_BUILD = true` temporarily, runs all data bus functions, verifies nothing prints to console. Reset to `false` after.
  - **STOP for Westley review.**

---

### Phase 1 — Parallel Screen Implementation

> **Current state:** Phase 0 Steps 0A–0E are complete (pre-security). Step 0G (Security Retrofit) must be completed and verified before Phase 1 begins. No Phase 1 screens have been started.

After Phase 0 (including Step 0G) is complete and verified, the following screens can be built in parallel by independent sub-agents. Each agent reads Phase 0's files (theme constants, components, router, data bus, **input sanitizer**) as dependencies and builds one screen.

**Each sub-agent's rules:**
1. Read `theme_constants.gd`, all `theme/components/*.tscn`, `scene_router.gd`, `ui_data_bus.gd`, and `input_sanitizer.gd` before writing any code.
2. Build the assigned screen using only shared components and data bus calls. No inline mock data. No direct color/font values — always reference `ThemeConstants`.
3. **Security rules:** All `LineEdit` fields must sanitize input through `InputSanitizer` on `text_changed`. All error messages displayed to the user must be pre-authored strings — never constructed from dynamic data. All `print()` calls must be gated behind `not ThemeConstants.IS_RELEASE_BUILD`. No internal IDs, file paths, or system state in player-visible text.
4. Test the screen by running it as the project's main scene (temporarily set in project.godot). Verify: all data renders correctly, all animations play, all interactive elements respond, navigation via `SceneRouter` works (even if the target scene is a placeholder).
5. **Checkpoint after each screen:** Screenshot-equivalent description of what renders, list of all interactive elements and their behavior, confirmation that all data comes from `UIDataBus`, confirmation that all user inputs are sanitized, list of any issues or design questions encountered.
6. **Do not fix cross-screen integration issues.** If the router, data bus, or a shared component has a bug, **stop and escalate.** Do not modify shared files — that's a Phase 2 concern.

**Parallel Agent A — Main Menu + Settings**
- Build `main_menu.tscn + .gd` per spec.
- Build `settings.tscn + .gd` per spec. Wire display settings to `DisplayServer`. Wire audio sliders to `AudioServer`.
- **Checkpoint A1:** Main Menu renders with all elements, stagger animation plays, menu items highlight on hover, QUIT works, navigation to all targets fires (targets may be placeholders).
- **Checkpoint A2:** Settings screen renders, all sliders/toggles are interactive, display settings apply (resolution change, fullscreen toggle, VSync toggle), audio bus volumes update.

**Parallel Agent B — Era Library + Era Detail**
- Build `era_library.tscn + .gd` per spec.
- Build `era_detail.tscn + .gd` per spec.
- **Checkpoint B1:** Era Library renders with 3 era cards from mock data, badges display correctly per access type, subscription status shows, key redemption entry card renders, clicking an era card triggers navigation.
- **Checkpoint B2:** Era Detail renders for each of the 3 mock eras (test by passing different `era_id` params). All sections populate from data bus. Tier progression and mastery bars animate. Purchase buttons call `UIDataBus.initiate_purchase()` and show the browser-redirect placeholder modal. Back navigation works.

**Parallel Agent C — New Game + Load Game**
- Build `new_game.tscn + .gd` per spec.
- Build `load_game.tscn + .gd` per spec.
- **Checkpoint C1:** New Game screen renders, era selection shows accessible eras, template selection appears on era click, ASCII topology diagrams display, BEGIN button enables when both selections are made, save name input sanitizes through `InputSanitizer` on every keystroke, slot creation calls data bus with sanitized name.
- **Checkpoint C2:** Load Game screen renders with mock save slots, delete confirmation modal works, slot deletion calls data bus, empty state message shows when no slots exist.

**Parallel Agent D — Mission Briefing**
- Build `mission_briefing.tscn + .gd` per spec.
- **Checkpoint D1:** Mission briefing renders the complete reference mockup with all four data cards, all text styled per bible spec, all stat bars animate, stagger timing matches the bible's exact sequence (0.2s → 0.4s → 0.55s → ...). Inline accent coloring works in situation text. Footer buttons present. This is the aesthetic north star — it must match the bible mockup precisely.

**Parallel Agent E — Key Redemption + Celebration Animations**
- Build `key_redemption.tscn + .gd` per spec.
- Build `assets/celebrations/celebration_base.gd` with shader layer management, glyph pool, bloom primitives (`bloom_ring`, `bloom_scatter`), and `resolve_title` departure-board effect.
- Build all 3 atmosphere shaders (`starfield.gdshader`, `ember_drift.gdshader`, `wave_surface.gdshader`).
- Build all 4 celebration scripts (roman_unlock, settled_reach_unlock, era_1980s_unlock, key_redemption with 3 variants).
- **Checkpoint E1:** Key redemption flow works end-to-end: key code input sanitizes through `InputSanitizer` on every keystroke (lowercase auto-uppercased, invalid chars stripped). Enter valid test code → loading state → celebration animation plays → flavor text typewriters → confirmation displays → continue returns to Era Library. Enter invalid code → `error_display` message renders. Input re-editable after error.
- **Checkpoint E2:** Each celebration animation plays independently (test scene that triggers each one in sequence). Verify: shader backgrounds render and are visually atmospheric (not distracting), glyph blooms use the correct era glyph set in the correct accent color, `resolve_title` departure-board effect scrambles then locks each letter left-to-right, total animation duration is ~3–3.5s per era unlock and ~1.5–1.8s per key redemption variant. Animations should feel *precise and rhythmic*, not chaotic — if any animation feels messy, **stop and escalate** rather than tweaking blindly.

---

### Phase 2 — Integration and Navigation Testing (Sequential)

After all Phase 1 agents complete and checkpoints are verified:

**Step 2A: Wire all scenes into the router.**
- Set Main Menu as the project's main scene.
- Verify every navigation path works:
  - Main Menu → New Game → (select era, template, name) → Mission Briefing (stubbed first-mission entry)
  - Main Menu → Continue → (select slot) → Mission Briefing (stubbed)
  - Main Menu → Era Library → Era Detail (for each era) → Back
  - Era Library → Key Redemption → (redeem key) → Back to Era Library (verify card updated)
  - Main Menu → Settings → (change settings) → Back
  - ESC / Back from every screen returns correctly
- **Checkpoint 2A:** Full navigation walkthrough documented. Every path works. No dead ends. No crashes. Back stack is correct from every screen.

**Step 2B: Cross-screen data consistency.**
- Create a new save slot via New Game → verify it appears in Load Game.
- Redeem a key in Key Redemption → verify the Era Library card updates.
- Change settings → navigate away → return → verify settings persisted.
- **Checkpoint 2B:** Data flows correctly across screens through the data bus. State changes in one screen are visible in others.

**Step 2C: Security verification.**
- Verify no screen constructs error messages from dynamic data — grep all `.gd` files for string concatenation in error display paths. All error strings must come from pre-authored constants or `error_display` fields from the data bus.
- Verify no screen calls `print()` without an `IS_RELEASE_BUILD` gate — grep all `.gd` files for ungated print calls.
- Verify no screen reads raw user input without passing through `InputSanitizer` — check all `LineEdit` `text_changed` handlers.
- Verify the settings file (`user://settings.cfg`) contains only display/audio values after changing settings — inspect the file on disk.
- Verify `initiate_purchase()` never puts sensitive data in a URL — inspect the mock-mode modal text and the function's implementation.
- Verify the scene router rejects unregistered scene names silently — call `SceneRouter.go_to("nonexistent_scene")` and confirm no crash, no error in console (in release mode), no navigation.
- **Checkpoint 2C:** Security audit results documented. All checks pass or issues flagged for Westley.

**Step 2D: Polish pass.**
- Review all screens for aesthetic consistency: are fonts, colors, spacings, border widths identical across screens?
- Verify scanline overlay renders on every screen.
- Verify all animations use the shared timing constants (no hardcoded values).
- Test at multiple resolutions (1920×1080, 2560×1440, 1280×720) — verify layouts don't break.
- **Checkpoint 2D:** Visual consistency confirmed. Resolution scaling acceptable (or issues documented for Westley to review).

## Done Condition

Run the game from the Main Menu. Navigate through every screen in the following sequence, verifying each step:

1. **Main Menu loads** with stagger animation, scanline overlay visible, all menu items present.
2. **New Game** → select Roman era → select Isolated Start → name the campaign → BEGIN. A save slot is created.
3. **Back to Main Menu** → "CONTINUE" is now visible.
4. **Continue** → the new save slot appears with correct data → click it (stubbed transition).
5. **Back to Main Menu** → **Era Library** → 3 era cards render with correct badges. Subscription status shows.
6. **Click Roman era card** → Era Detail loads with full Roman data, gold accent throughout, tier bars animate, unit roster displays.
7. **Back** → **Click 1980s card** → Era Detail loads with olive accent, trial badge shows "3 MISSIONS LEFT".
8. **Back** → **Key Redemption** → enter "TESTPERM001" → ASCII animation plays → flavor text appears → confirmation shows → CONTINUE returns to Era Library, Roman card unchanged (already owned).
9. **Back to Main Menu** → **Settings** → change resolution, toggle fullscreen, adjust volume sliders. Changes apply. **Back** → return to Settings → settings persisted.
10. **Mission Briefing** (accessible from New Game flow or Load Game) → full reference mockup renders with correct stagger timing, all four data cards populated, stat bars animate, accent colors correct for the era.

Westley sees all of this, confirms the aesthetic matches the bible, confirms navigation is smooth, confirms no dead ends or crashes, and signs off.

**Security sign-off (part of Done Condition):**
- Confirm: no purchase button ever renders a payment form or exposes a URL with player data — all purchase actions show the browser-redirect placeholder modal.
- Confirm: typing `<script>../\x00;DROP` into the save name field produces a sanitized, harmless string.
- Confirm: typing injection strings into the key redemption field produces a sanitized, harmless string and a clean "Invalid key" error.
- Confirm: the settings file on disk contains only display/audio values.
- Confirm: with `IS_RELEASE_BUILD = true`, no print output appears in the Godot console during a full walkthrough.

## Files Created

*Filled in after implementation.*
