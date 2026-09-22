#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if command -v godot >/dev/null 2>&1; then
    GODOT="godot"
elif [[ -x "$HOME/.local/bin/godot" ]]; then
    GODOT="$HOME/.local/bin/godot"
elif [[ -x "/Applications/Godot.app/Contents/MacOS/Godot" ]]; then
    GODOT="/Applications/Godot.app/Contents/MacOS/Godot"
else
    echo "ERROR: godot binary not found. Install Godot 4.x or add to PATH." >&2
    exit 2
fi

if [[ $# -lt 1 ]]; then
    echo "usage: $0 <mockup> [--plant id[,id]] [--timeout 120] [--refresh-cache]" >&2
    exit 2
fi

MOCKUP="$1"
shift
PLANT=""
TIMEOUT="120"
REFRESH_CACHE="0"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --plant) PLANT="$2"; shift 2 ;;
        --timeout) TIMEOUT="$2"; shift 2 ;;
        --refresh-cache) REFRESH_CACHE="1"; shift ;;
        *) echo "unknown arg $1" >&2; exit 2 ;;
    esac
done

VERIFY_SCRIPT="scenes/mockups/${MOCKUP}/verify.gd"
if [[ ! -f "$VERIFY_SCRIPT" ]]; then
    echo "no verify script $VERIFY_SCRIPT" >&2
    exit 2
fi

SCRATCH="${TMPDIR:-/tmp}/mockup_verify"
mkdir -p "$SCRATCH"
LOG="$SCRATCH/verify-${MOCKUP}.log"

CACHE_FILE=".godot/global_script_class_cache.cfg"
needs_refresh="$REFRESH_CACHE"
if [[ "$needs_refresh" != "1" && -f "$CACHE_FILE" ]]; then
    if [[ -n "$(find "scenes/mockups/${MOCKUP}" scenes/mockups/_shared -newer "$CACHE_FILE" -name '*.gd' 2>/dev/null)" ]]; then
        needs_refresh="1"
    fi
elif [[ ! -f "$CACHE_FILE" ]]; then
    needs_refresh="1"
fi
if [[ "$needs_refresh" == "1" ]]; then
    "$GODOT" --headless --path . --import >/dev/null 2>&1 || true
fi

set +e
MOCKUP_PLANT="$PLANT" timeout "$TIMEOUT" "$GODOT" --headless --path . --script "res://${VERIFY_SCRIPT}" --quit-after 100000 2>&1 | tee "$LOG"
EXIT_CODE="${PIPESTATUS[0]}"
set -e

if [[ -z "$PLANT" ]]; then
    if [[ "$EXIT_CODE" == "0" ]] && grep -q "^VERIFY OK$" "$LOG"; then
        exit 0
    fi
    echo "VERIFY did not pass cleanly (exit $EXIT_CODE)" >&2
    exit 1
fi

FAIL_COUNT="$(grep -c '^FAIL:' "$LOG" || true)"
if [[ "$EXIT_CODE" != "0" && "$FAIL_COUNT" -gt 0 ]]; then
    echo "PLANT $PLANT LIVE ($FAIL_COUNT FAIL)"
    exit 0
fi
echo "PLANT $PLANT DEAD"
exit 1
