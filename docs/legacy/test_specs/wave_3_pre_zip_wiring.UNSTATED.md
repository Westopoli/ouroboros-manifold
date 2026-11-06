# Unstated assumptions for wave_3_pre_zip_wiring

Inferences made by /swarm during drafting that did not trace directly to a user statement.
Each entry awaits user disposition: **confirm** (accept value), **edit** (provide different value), **accept-as-flagged** (pass to /swarm-spawn's downstream sweep).

## Entries

### U-1: short_objective field name + length cap
- Artifact: spec, umbrella
- Location: spec §B2-A design contract; umbrella `test_umbrella_c_short_objective_length_bounded`
- Inferred value: field name `short_objective`; max length 80 chars
- Why this could not be cited: user approved "1-line `{accent}<short_objective>{/accent}` header" via B2.1, which establishes the slot but not the field name in dict OR the length cap. 80 chars chosen as reasonable HUD-friendly bound.
- Disposition: confirmed 2026-05-26

### U-2: header BBCode format details
- Artifact: spec
- Location: spec §B2-B acceptance criterion 2 — "BBCode `[color=#<accent_primary_hex>][b]<TEXT-UPPERCASE>[/b][/color]` with font size ≥1.5× body text"
- Inferred value: explicit `[b]` bold tag, font size ≥1.5× body text
- Why this could not be cited: user stated "large + uppercase + accent_primary color" (B2.2). "Large" expanded to "≥1.5×"; bold added as standard emphasis pattern with large + uppercase combo.
- Disposition: confirmed 2026-05-26

### U-3: TutorialStateMachine signal names
- Artifact: spec, umbrella
- Location: spec §Type contract Signal names; umbrella `test_umbrella_f_*`
- Inferred value: `beat_fired(beat_id: String)`, `tutorial_completed`
- Why this could not be cited: user approved trigger event names (B3.1) but did not state state-machine signal names. Picked verbs matching action ("beat shown" → `beat_fired`; "TUT_005 dismissed" → `tutorial_completed`).
- Disposition: confirmed 2026-05-26

### U-4: TutorialStateMachine method name `reset_for_replay()`
- Artifact: spec, umbrella
- Location: spec §B3-B acceptance criterion 5; umbrella `test_umbrella_f_state_machine_*`
- Inferred value: method name `reset_for_replay()`
- Why this could not be cited: user said replay button "deletes user://tutorial_completed + sets in-memory replay flag." Method name not stated.
- Disposition: confirmed 2026-05-26

### U-5: PyInstaller Windows binary COLLECT name `ouroboros_sim`
- Artifact: spec, umbrella
- Location: spec §B5-A design contract; umbrella `test_umbrella_a_pyinstaller_win_spec_structure`
- Inferred value: COLLECT name `ouroboros_sim` (`.exe` suffix added by PyInstaller on Windows)
- Why this could not be cited: matches existing Mac `legacy/build/pyinstaller_spec.spec` COLLECT name. Convention inheritance, not user-stated.
- Disposition: confirmed 2026-05-26

### U-6: Privacy modal button label
- Artifact: spec
- Location: spec §B5-B design contract — "Single 'Accept & Continue' button"
- Inferred value: button label literal `"Accept & Continue"`
- Why this could not be cited: user approved B5.1 modal text verbatim but did not state button label. Picked phrase matching the "accept disclosure → proceed" affordance.
- Disposition: confirmed 2026-05-26

### U-7: Tactical signal-emission site location
- Artifact: spec, umbrella
- Location: spec §B3-B acceptance criterion 6; umbrella `test_umbrella_f_tactical_emits_unit_signals`
- Inferred value: `scenes/tactical/tactical.gd` emits `first_unit_visible` (after first sim_state populates units) + `first_unit_selected` (after first selection input)
- Why this could not be cited: user approved trigger event names (B3.1) + state machine autoload location (B3.2) but did not state the emitter file. Picked tactical.gd as canonical mid-mission orchestrator.
- Disposition: confirmed 2026-05-26

### U-8: SimBridge release-mode binary path pattern
- Artifact: spec, umbrella
- Location: spec §B5-C design contract; umbrella `test_umbrella_g_sim_bridge_release_branch`
- Inferred value: release-mode exec path = `<game_root>/sim/ouroboros_sim` (`.exe` on Windows); `--root <game_root>` arg passed
- Why this could not be cited: user approved B5.4 custom_user_dir_name="data" + B5.3 deferred preset config. `sim/` subdir + `--root` arg inferred from existing dev-mode pattern (pipe_transport.py argparse already supports `--root` per memory). Subdir choice `sim/` is conventional.
- Disposition: confirmed 2026-05-26

### U-9: Privacy modal scene path convention
- Artifact: spec, umbrella
- Location: spec §B5-B Files in scope; umbrella `test_umbrella_b_privacy_modal_scene_exists`
- Inferred value: `scenes/privacy_modal/privacy_modal.tscn` + `scenes/privacy_modal/privacy_modal.gd`
- Why this could not be cited: matches existing scenes/<name>/<name>.{tscn,gd} pattern. Convention, not user-stated.
- Disposition: confirmed 2026-05-26

### U-10: Umbrella behavioral ratio override
- Artifact: umbrella
- Location: umbrella test files (both Python + Godot)
- Inferred value: accept ~48% behavioral ratio (below 50% threshold); justification = cover_asteroid_los_spec.md project precedent for heavy source-grep parent umbrella when wave work is wiring-heavy
- Why this could not be cited: user picked option (b) to add Godot headless umbrella + chain umbrella_test_cmd, accepting the resulting marginal-under-threshold ratio. Skill step 8 normally requires explicit re-confirmation on weak umbrella.
- Disposition: confirmed 2026-05-26

## Disposition guidance

- **Confirm**: accept value as-is. Stays in this file as record but no longer pending.
- **Edit**: provide replacement; spec + umbrella updated to match; cited as new user-stmt.
- **Accept-as-flagged**: pass to /swarm-spawn downstream sweep — leaf agents see entry, can re-flag if it breaks slice independence.

Batch-confirm via "confirm U-1 through U-10" or "all confirmed" if accepting every inference. Edit individual entries by index.
