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
darwin=0
[[ "$(uname -s)" == "Darwin" ]] && darwin=1
if [[ $darwin == 1 ]]; then
  arch="$(uname -m)"
  # OM_GODOT_APP is a test seam only (as OM_BETA_BUILD_FILE is); the Linux route never reads it.
  app="${OM_GODOT_APP:-/Applications/Godot.app/Contents/MacOS/Godot}"
  # Same order as scripts/run_godot_tests.sh, then the app; empty means none found.
  if command -v godot.real >/dev/null 2>&1; then godot=godot.real
  elif [[ -x "$HOME/.local/bin/godot.real" ]]; then godot="$HOME/.local/bin/godot.real"
  elif [[ -x "$app" ]]; then godot="$app"
  else godot=""; fi
else
  command -v "$godot" >/dev/null 2>&1 || godot="$HOME/.local/bin/godot.real"
fi

fail() { echo "EDITOR SETUP FAILED $1"; exit 1; }

if [[ "${1:-}" == "--check" ]]; then
  if [[ $darwin == 1 ]]; then
    echo "step pipe: scripts/build_pipe_macos.sh (ARCH=$arch), then copy dist/macos/ouroboros_pipe to $pipe (only when csrc/ is newer than the copy or the copy is missing)"
  else
    echo "step pipe: scripts/build_pipe_linux.sh, then copy dist/linux/ouroboros_pipe to $pipe (only when csrc/ is newer than the copy or the copy is missing)"
  fi
  echo "step steam: copy $cache to addons/godotsteam (cp -a); on a cache miss run scripts/fetch_godotsteam.sh"
  if [[ -z "$godot" ]]; then
    echo "step import: none found (looked at: godot.real on PATH, $app)"
  else
    echo "step import: $godot --headless --import --path ."
  fi
  if [[ $darwin == 1 ]]; then
    if command -v clang >/dev/null 2>&1; then echo "clang: present"; else echo "clang: missing"; fi
  fi
  exit 0
fi

# pipe: pipe/ is git-ignored, so nothing else compares the copy to csrc/.
# (`| head -n1` rather than `-quit`: BSD find on macOS has no -quit.)
if [[ ! -f "$pipe" || -n "$(find csrc -type f -newer "$pipe" -print | head -n1)" ]]; then
  if [[ $darwin == 1 ]]; then
    built=dist/macos/ouroboros_pipe
    ARCH="$arch" scripts/build_pipe_macos.sh >/dev/null || fail pipe
  else
    built=dist/linux/ouroboros_pipe
    scripts/build_pipe_linux.sh >/dev/null || fail pipe
  fi
  mkdir -p pipe || fail pipe
  # cp to a temporary name, then mv: a running binary is busy and cannot be overwritten in place.
  cp "$built" "$pipe.new.$$" && mv -f "$pipe.new.$$" "$pipe" || { rm -f "$pipe.new.$$"; fail pipe; }
fi

# steam: the libraries are git-ignored; without them every open prints benign ERROR lines.
if [[ -n "$(ls -A "$cache" 2>/dev/null)" ]]; then
  mkdir -p addons/godotsteam && cp -a "$cache/." addons/godotsteam/ || fail steam
else
  scripts/fetch_godotsteam.sh >/dev/null || fail steam
fi

if [[ -z "$godot" ]]; then
  echo "no Godot found: looked for godot.real on PATH, $HOME/.local/bin/godot.real and $app"
  fail import
fi
"$godot" --headless --import --path . >/dev/null 2>&1 || fail import
echo "EDITOR READY $tree"
