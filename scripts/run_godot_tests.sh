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

TIMEOUT="${TIMEOUT_SEC:-300}"

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
cleanup() {
    if [[ -n "$OM_SAVE_DIR_CREATED" ]]; then
        rm -rf "$OM_SAVE_DIR_CREATED"
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
    echo "=== Running $RES_PATH (timeout ${TIMEOUT}s) ==="

    set +e
    "$GODOT" --headless --path . --script "$RES_PATH" --quit-after "$TIMEOUT"
    TEST_EXIT=$?
    set -e

    if [[ $TEST_EXIT -ne 0 ]]; then
        echo "FAIL: $RES_PATH (exit $TEST_EXIT)"
        EXIT_CODE=1
    else
        echo "PASS: $RES_PATH"
    fi
done

exit $EXIT_CODE
