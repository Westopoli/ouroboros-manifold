#!/usr/bin/env bash
# Set this tree up for the Godot editor (docs/stories/H-067.md): current pipe binary, GodotSteam libraries, one project import.
# Run once, and again after any pull that changes csrc/. `--check` prints the steps and changes nothing.
# Ends with `EDITOR READY <tree>` or `EDITOR SETUP FAILED <step>` (steps: pipe, steam, import).
set -uo pipefail
tree="$(cd "$(dirname "$0")/.." && pwd)"
cd "$tree" || exit 1
cache="$HOME/Projects/om-push/cache/godotsteam"
pipe=pipe/ouroboros_pipe
godot=godot.real
command -v "$godot" >/dev/null 2>&1 || godot="$HOME/.local/bin/godot.real"

fail() { echo "EDITOR SETUP FAILED $1"; exit 1; }

if [[ "${1:-}" == "--check" ]]; then
  echo "step pipe: scripts/build_pipe_linux.sh, then copy dist/linux/ouroboros_pipe to $pipe (only when csrc/ is newer than the copy or the copy is missing)"
  echo "step steam: copy $cache to addons/godotsteam (cp -a); on a cache miss run scripts/fetch_godotsteam.sh"
  echo "step import: $godot --headless --import --path ."
  exit 0
fi

# pipe: pipe/ is git-ignored, so nothing else compares the copy to csrc/.
if [[ ! -f "$pipe" || -n "$(find csrc -type f -newer "$pipe" -print -quit)" ]]; then
  scripts/build_pipe_linux.sh >/dev/null || fail pipe
  mkdir -p pipe || fail pipe
  # cp to a temporary name, then mv: a running binary is busy and cannot be overwritten in place.
  cp dist/linux/ouroboros_pipe "$pipe.new.$$" && mv -f "$pipe.new.$$" "$pipe" || { rm -f "$pipe.new.$$"; fail pipe; }
fi

# steam: the libraries are git-ignored; without them every open prints benign ERROR lines.
if [[ -n "$(ls -A "$cache" 2>/dev/null)" ]]; then
  mkdir -p addons/godotsteam && cp -a "$cache/." addons/godotsteam/ || fail steam
else
  scripts/fetch_godotsteam.sh >/dev/null || fail steam
fi

"$godot" --headless --import --path . >/dev/null 2>&1 || fail import
echo "EDITOR READY $tree"
