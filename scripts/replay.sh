#!/usr/bin/env bash
# H-063: open a lab fight in the replay scene, on Linux and macOS. See docs/stories/H-063.md.
# replay.sh <fight.json> [--shots <dir>] [--dry-run]
# Runs under bash 3.2 (macOS): no associative arrays, mapfile or ${var,,}; no timeout, flock, setsid or xdotool.
# See also: scripts/play.sh (the Linux way, with OM_FIGHT set by hand); scripts/run_godot_tests.sh (Godot search)
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SCENE="res://scenes/proto/fight_replay/fight_replay.tscn"
RESOLUTION=1919x1080   # not 1920x1080, as in play.sh: a request equal to the project viewport presents only the splash on GNOME Wayland
fight=""; shots=""; dry=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --shots) shots="${2:-}"; shift 2;;
    --dry-run) dry=1; shift;;
    -*) echo "replay.sh: unknown argument $1" >&2; exit 64;;
    *) fight="$1"; shift;;
  esac
done
[[ -n "$fight" ]] || { echo "replay.sh: usage: replay.sh <fight.json> [--shots <dir>] [--dry-run]" >&2; exit 64; }
[[ -f "$fight" ]] || { echo "replay.sh: no fight file $fight" >&2; exit 2; }

# absolute path of a file or directory that may not exist yet, against the caller's directory
abspath() {
  case "$1" in
    /*) printf '%s' "$1";;
    *) printf '%s/%s' "$(pwd -P)" "${1#./}";;
  esac
}
fight_abs="$(cd "$(dirname "$fight")" && pwd -P)/$(basename "$fight")"
[[ -z "$shots" ]] || shots_abs="$(abspath "$shots")"

# Godot, first match wins; the Mac app location is tried on Darwin only.
osname="${OM_UNAME:-$(uname -s)}"
godot=""
if [[ -n "${GODOT:-}" ]]; then godot="$GODOT"
elif command -v godot >/dev/null 2>&1; then godot="$(command -v godot)"
elif [[ -x "$HOME/.local/bin/godot.real" ]]; then godot="$HOME/.local/bin/godot.real"
elif [[ "$osname" == Darwin && -x "/Applications/Godot.app/Contents/MacOS/Godot" ]]; then godot="/Applications/Godot.app/Contents/MacOS/Godot"
fi
[[ -n "$godot" ]] || { echo "replay.sh: godot not found (set GODOT, or put godot on PATH)" >&2; exit 2; }

marker="$REPO/.godot/replay_imported"
envs=(OM_FIGHT="$fight_abs"); [[ -z "$shots" ]] || envs+=(OM_SHOT_OUT="$shots_abs")
if [[ $dry -eq 1 ]]; then
  printf '%q --headless --import --path %q\n' "$godot" "$REPO"
  printf '%q ' "${envs[@]}" "$godot" --path "$REPO" --windowed --resolution "$RESOLUTION" "$SCENE"; echo
  exit 0
fi
if [[ ! -f "$marker" ]]; then
  "$godot" --headless --import --path "$REPO" || exit 1
  mkdir -p "$REPO/.godot" && touch "$marker"
fi
exec env "${envs[@]}" "$godot" --path "$REPO" --windowed --resolution "$RESOLUTION" "$SCENE"
