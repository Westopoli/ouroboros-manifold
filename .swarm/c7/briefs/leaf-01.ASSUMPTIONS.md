# leaf-01 assumptions (C7 -- autoload/qa_daemon.gd, scenes/harness/**)

- `harness.tscn` is a thin standalone wrapper (`Control` root + `harness.gd`),
  not the real main menu. Source: spec_lines 58-59 ("the main menu or a thin
  wrapper around it"); chose the thin wrapper to stay inside C7's ownership
  boundary (`scenes/harness/**` only) and avoid any coupling to
  `scenes/main_menu/**` internals or `SceneRouter`'s scene table, neither of
  which C7 owns or was asked to touch.

- `--qa-port N` wire framing: line-delimited JSON, request
  `{"verb": "<name>", "args": [...]}` (or bare `["<name>", ...]` array,
  accepted as a convenience), response `{"ok": bool, "result": ...}` or
  `{"ok": false, "error": "..."}`, one line each direction. No source in the
  repo for this exact shape -- pure guess, chosen to mirror the JSON-array
  action shape `qa_driver.gd` already uses for `--qa-script`.

- `inject <bug-id>` returns `{"bug_id": <id>, "known": <bool>}`, true for a
  small hardcoded `KNOWN_BUG_IDS` stub list, false otherwise; records it in
  an in-memory dict, nothing downstream reads it yet. Source: spec_lines
  47-49, "a stub that records the id and returns true/false for known/
  unknown is enough here."

- `fixture <path>` has no spec detail beyond the verb name. Implemented as a
  stub that stores the path and echoes it back (`{"fixture": path}`), no
  actual load -- no source, pure guess, by analogy to `inject` being
  explicitly scoped as a stub with no downstream consumer yet.

- `step <n>` advances a local `tick` counter by `n` and returns the new
  value; it does not step the Python sim (`SimBridge`) itself -- no source,
  pure guess. Wiring `step` to the real sim's tick loop is a materially
  bigger change (cross-process command, not just a getter) that felt out of
  scope for "adapted to the real game...enough here" language covering the
  sibling `inject` stub; flagging this explicitly in case a later piece
  wants `step` to actually drive the sim.

- `state()`'s `tick` field reads `TacticalBridge.current_tick` (via
  `get_node_or_null("/root/TacticalBridge")`) when the daemon is inside a
  running tree and that autoload is present, else falls back to the local
  `tick` var (0 by default, incremented only by `step`). Source:
  `autoload/tactical_bridge.gd:145`/`:183` -- `current_tick` is the existing
  repo convention for "current sim tick," found by grep, not a guess.

- The `input` wire-verb (spec_lines 44-46, "the desktop analogues...input")
  is the umbrella for `qa_driver.gd`'s reused move/click/click_node/drag/
  wheel/key/key_down/key_up/wait_frames verbs, dispatched as
  `["input", "<sub-verb>", ...]`. Source: spec_lines 55-57 name `screenshot`
  and `input` as the only two surface verbs left unlisted in the "only
  state, tree, seed, fixture, pause, step, inject are new" sentence, so
  `input`/`screenshot` must be where the reused verbs live; the sub-verb
  array shape is a guess, mirroring `qa_driver.gd`'s own `_do()` action-array
  format.

- **Deviation, evidence-based (not a guess): `qa_driver.gd` reuse is limited
  to `--qa-port` mode.** Instantiating `QaDriverScript` and adding it to the
  tree while `--qa-script` is also present crashes the process: `qa_driver.gd`'s
  own `_ready()` independently reads `--qa-script` off
  `OS.get_cmdline_user_args()` and, finding no `qa_state()`/`qa_plant()`
  contract on the harness scene root (spec explicitly says there is none),
  calls `get_tree().quit(3)`. Verified empirically with two throwaway probe
  scripts run via `godot --headless --script` (not committed, deleted after
  use): (1) confirmed `NOTIFICATION_READY` fires deferred, not synchronously,
  so no add-order trick avoids it; (2) confirmed exit code 2/`QA_ERR` fires
  the moment `--qa-script` is present on the cmdline regardless of when/how
  the driver node enters the tree. Fix: `qa_daemon.gd` only ever
  instantiates and `add_child()`s `QaDriverScript` in `--qa-port` mode
  (verified safe -- its `_ready()` no-ops harmlessly there since
  `--qa-script` is absent). In `--qa-script` mode, the `input`/`screenshot`
  wire-verbs return `{"ok": false, "error": "...only available in --qa-port
  mode"}` instead of crashing the process; `state`/`tree`/`seed`/`fixture`/
  `pause`/`step`/`inject` work identically in both modes. Not required to
  fix `qa_driver.gd` itself (out of C7's ownership,
  `scenes/mockups/_shared/**`), and not exercised by either fenced
  acceptance path (`tests/test_qa_daemon.gd` only calls `state()` outside a
  SceneTree).

- `await someObject.call("_private_method", ...)` (dynamic dispatch, used so
  the static GDScript analyzer doesn't reject calling `qa_driver.gd`'s
  underscore-prefixed methods on a statically-typed `Node` variable) was
  verified empirically to correctly await through to the coroutine's real
  return value rather than an intermediate Signal, via a throwaway probe
  script (deleted after use). Not a guess by the end, but flagging since it
  isn't an established pattern elsewhere in this repo.
