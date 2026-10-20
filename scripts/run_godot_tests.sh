#!/usr/bin/env bash
# run_godot_tests.sh — headless Godot test runner for Phase 1 ship work.
# Usage:
#   scripts/run_godot_tests.sh tests/test_phase1_apex_ship.gd
#   scripts/run_godot_tests.sh tests/test_b2_briefing_integration.gd
# Exit code: 0 on pass, non-zero on fail.
# Test scripts are expected to call get_tree().quit() with an exit code after assertions.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Locate Godot binary
if command -v godot >/dev/null 2>&1; then
    GODOT="godot"
elif [[ -x "/Applications/Godot.app/Contents/MacOS/Godot" ]]; then
    GODOT="/Applications/Godot.app/Contents/MacOS/Godot"
elif [[ -x "/Applications/Godot_mono.app/Contents/MacOS/Godot" ]]; then
    GODOT="/Applications/Godot_mono.app/Contents/MacOS/Godot"
else
    echo "ERROR: godot binary not found. Install Godot 4.x or add to PATH." >&2
    exit 2
fi

DEFAULT_TIMEOUT=300
# A test script may declare its own budget (frames, like --quit-after) with a
# line `# test-timeout: N`; it is clamped up to the default. An explicit
# TIMEOUT_SEC in the environment wins over any declaration.

if [[ $# -lt 1 ]]; then
    echo "usage: $0 <test_script.gd> [<test_script.gd> ...]" >&2
    exit 2
fi

# Tests save (test_load_game.gd deletes/rewrites campaign_1; live-frame
# sections autosave). Without OM_SAVE_DIR, autoload/c_bridge.gd's saves_dir()
# falls back to the real user save directory and a test run destroys a
# developer's saves. Point it at a throwaway temp dir unless the caller
# already set one, and clean it up on exit.
OM_SAVE_DIR_CREATED=""
if [[ -z "${OM_SAVE_DIR:-}" ]]; then
    OM_SAVE_DIR="$(mktemp -d)"
    export OM_SAVE_DIR
    OM_SAVE_DIR_CREATED="$OM_SAVE_DIR"
fi
# FINDING-ambient-user-dir: same pattern for the user dir (project.godot's
# custom_user_dir_name="data" puts user:// at $XDG_DATA_HOME/data), so a test run
# never reads or writes the machine's ~/.local/share/data. A non-empty
# XDG_DATA_HOME from the caller (the merge gate's) wins and is never removed.
# See also: the OM_SAVE_DIR block above, scripts/specfactory/merge_gate.sh
XDG_DATA_HOME_CREATED=""
if [[ -z "${XDG_DATA_HOME:-}" ]]; then
    XDG_DATA_HOME="$(mktemp -d)"
    export XDG_DATA_HOME
    XDG_DATA_HOME_CREATED="$XDG_DATA_HOME"
fi
cleanup() {
    if [[ -n "$OM_SAVE_DIR_CREATED" ]]; then
        rm -rf "$OM_SAVE_DIR_CREATED"
    fi
    if [[ -n "$XDG_DATA_HOME_CREATED" ]]; then
        rm -rf "$XDG_DATA_HOME_CREATED"
    fi
}
trap cleanup EXIT

EXIT_CODE=0
for TEST_PATH in "$@"; do
    if [[ ! -f "$TEST_PATH" ]]; then
        echo "FAIL: $TEST_PATH not found" >&2
        EXIT_CODE=1
        continue
    fi

    RES_PATH="res://${TEST_PATH#./}"
    if [[ -n "${TIMEOUT_SEC:-}" ]]; then
        TIMEOUT="$TIMEOUT_SEC"
    else
        TIMEOUT="$DEFAULT_TIMEOUT"
        DECLARED="$(grep -m1 -oP '^# test-timeout: \K[0-9]+' "$TEST_PATH" || true)"
        if [[ -n "$DECLARED" && "$DECLARED" -gt "$TIMEOUT" ]]; then
            TIMEOUT="$DECLARED"
        fi
    fi
    echo "=== Running $RES_PATH (timeout ${TIMEOUT}s) ==="

    RUN_LOG="$(mktemp)"
    set +e
    "$GODOT" --headless --path . --script "$RES_PATH" --quit-after "$TIMEOUT" 2>&1 | tee "$RUN_LOG"
    TEST_EXIT="${PIPESTATUS[0]}"
    set -e

    # A GDScript SCRIPT ERROR (missing method/constant, bad call) halts the
    # erroring function on the spot but does not throw -- the awaiting
    # coroutine in _initialize() resumes anyway, the test still prints its
    # summary with whatever partial pass/fail counts it reached, and Godot
    # still exits 0. Exit code and the summary line both lie in that case,
    # so a SCRIPT ERROR line anywhere in the run is fail-worthy on its own,
    # ahead of the exit-code check below.
    SCRIPT_ERR_LINE="$(grep -m1 'SCRIPT ERROR' "$RUN_LOG" || true)"

    # A test that hangs (awaits a signal/frame that never comes) never
    # reaches its own summary print; --quit-after force-quits it with exit
    # 0 once the timeout elapses, which the old exit-code-only check read
    # as PASS. Every test file's convention (tests/test_c_bridge.gd,
    # tests/test_galaxy_view.gd, etc.) is to print `PASS: N  FAIL: M`
    # right before quitting, so its absence means the run aborted.
    HAS_SUMMARY="$(grep -cE '^PASS: [0-9]+ +FAIL: [0-9]+$' "$RUN_LOG" || true)"
    rm -f "$RUN_LOG"

    if [[ -n "$SCRIPT_ERR_LINE" ]]; then
        echo "FAIL: $RES_PATH (script error: $SCRIPT_ERR_LINE)"
        EXIT_CODE=1
    elif [[ "${HAS_SUMMARY:-0}" -eq 0 ]]; then
        echo "FAIL: $RES_PATH (no summary: aborted)"
        EXIT_CODE=1
    elif [[ $TEST_EXIT -ne 0 ]]; then
        echo "FAIL: $RES_PATH (exit $TEST_EXIT)"
        EXIT_CODE=1
    else
        echo "PASS: $RES_PATH"
    fi
done

exit $EXIT_CODE
