#!/usr/bin/env bash
# H-028 stable-beta-build (docs/stories/H-028.md): refresh the standing beta under <root>/beta/.
#   beta_refresh.sh [--root <dir>] [--tree <dir>] [--sha <sha>]          build: export + pipe into beta/<sha>/
#   beta_refresh.sh ... --proof <png>   publish: capture check, repoint beta/current, PLAYED.txt, install, keep 3
#   beta_refresh.sh --dry-run ...       print the seven steps, change nothing
#   beta_refresh.sh --check-capture <png>   CAPTURE OK <fraction> (exit 0) or CAPTURE REJECT uniform (exit 3)
# The clerk builds, wakes the monitors, launches beta/<sha>/ouroboros_beta.x86_64, takes the screen capture
# (scripts/specfactory/screen_capture.sh), then publishes with --proof. A REJECT leaves beta/current on the previous build.
# The build phase fills <tree>/addons/godotsteam/ from <root>/cache/godotsteam/ first; a cache miss runs
# scripts/fetch_godotsteam.sh (sha256-pinned) in the tree and caches the result, so only the first refresh needs the network.
# --sha defaults to the full `git rev-parse HEAD` of the tree.
# See also: scripts/specfactory/screen_capture.sh (same uniformity rule), scripts/beta/ (installed templates).
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$HOME/Projects/om-push"; tree="$(dirname "$here")"; sha=""; dry=0; proof=""; check=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) dry=1; shift ;;
    --root) root="${2:?--root needs a dir}"; shift 2 ;;
    --tree) tree="${2:?--tree needs a dir}"; shift 2 ;;
    --sha) sha="${2:?--sha needs a sha}"; shift 2 ;;
    --proof) proof="${2:?--proof needs a png}"; shift 2 ;;
    --check-capture) check="${2:?--check-capture needs a png}"; shift 2 ;;
    *) echo "usage: beta_refresh.sh [--dry-run] [--root dir] [--tree dir] [--sha sha] [--proof png] | --check-capture png" >&2; exit 64 ;;
  esac
done

check_capture() {  # thin call into merge_gate_support.frame_busyness; only blank fraction 0 rejects (as screen_capture.sh)
  python3 - "$here/specfactory" "$1" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from merge_gate_support import frame_busyness
fraction = frame_busyness(Path(sys.argv[2]))
if fraction == 0:
    print("CAPTURE REJECT uniform")
    sys.exit(3)
print("CAPTURE OK %.4f" % fraction)
PY
}

if [[ -n "$check" ]]; then check_capture "$check"; exit $?; fi

[[ -n "$sha" ]] || sha="$(git -C "$tree" rev-parse HEAD)" || exit 1
beta="$root/beta"; out="$beta/$sha"; bin=ouroboros_beta.x86_64
steam_cache="$root/cache/godotsteam"; steam_dst="$tree/addons/godotsteam"
bin_dst="$HOME/.local/bin/om-beta"; desk_dst="$HOME/.local/share/applications/ouroboros-beta.desktop"

if [[ $dry -eq 1 ]]; then
  echo "DRY godotsteam: $steam_cache -> $steam_dst (on a cache miss: scripts/fetch_godotsteam.sh, sha256-pinned)"
  echo "DRY export: godot.real --headless --path $tree --export-release \"Linux\" $out/$bin"
  echo "DRY pipe: scripts/build_pipe_linux.sh -> $out/ouroboros_pipe"
  echo "DRY link: ln -sfn $out $beta/current"
  echo "DRY install: $tree/scripts/beta/om-beta -> \$HOME/.local/bin/om-beta"
  echo "DRY install: $tree/scripts/beta/ouroboros-beta.desktop -> \$HOME/.local/share/applications/ouroboros-beta.desktop"
  echo "DRY keep: last 3 builds under $beta/"
  exit 0
fi

if [[ -z "$proof" ]]; then  # build phase
  mkdir -p "$out" || exit 1
  if [[ -n "$(ls -A "$steam_cache" 2>/dev/null)" ]]; then
    mkdir -p "$steam_dst" && cp -a "$steam_cache/." "$steam_dst/" || { echo "BUILD FAIL godotsteam copy" >&2; rm -rf "$out"; exit 1; }
  else  # cache miss: pinned, sha256-checked fetch into the tree, then keep it for the next refresh
    "$tree/scripts/fetch_godotsteam.sh" >/dev/null || { echo "BUILD FAIL godotsteam fetch" >&2; rm -rf "$out"; exit 1; }
    mkdir -p "$steam_cache" && cp -a "$steam_dst/." "$steam_cache/" || { echo "BUILD FAIL godotsteam cache" >&2; rm -rf "$out"; exit 1; }
  fi
  godot.real --headless --path "$tree" --export-release "Linux" "$out/$bin" || { echo "BUILD FAIL export" >&2; rm -rf "$out"; exit 1; }
  printf '%s\n' "$sha" > "$out/beta_build.txt" || exit 1  # H-060: the build's sha beside the binary; the field HUD and BetaMode read it
  "$tree/scripts/build_pipe_linux.sh" >/dev/null || { echo "BUILD FAIL pipe" >&2; rm -rf "$out"; exit 1; }
  cp "$tree/dist/linux/ouroboros_pipe" "$out/ouroboros_pipe" || exit 1
  echo "BUILT $out"
  echo "NEXT: launch $out/$bin, capture the screen, then rerun with --proof <png>"
  exit 0
fi

# publish phase
[[ -x "$out/$bin" ]] || { echo "NO BUILD $out/$bin (run the build phase first)" >&2; exit 1; }
check_capture "$proof" || exit $?  # REJECT: beta/current stays on the previous build
ln -sfn "$out" "$beta/current" || exit 1
printf 'sha: %s\ncapture: %s\nrefreshed: %s\n' "$sha" "$proof" "$(date +%F)" > "$beta/current/PLAYED.txt"
mkdir -p "$HOME/.local/bin" "$HOME/.local/share/applications" || exit 1
install -m 755 "$tree/scripts/beta/om-beta" "$bin_dst" || exit 1
# The desktop-entry spec does not expand env vars: install the entry with $HOME resolved.
sed "s|\$HOME|$HOME|g; s|\${HOME}|$HOME|g" "$tree/scripts/beta/ouroboros-beta.desktop" > "$desk_dst" || exit 1
live="$(readlink -f "$beta/current")"
n=0
while IFS= read -r d; do  # newest first; the live build never counts against the three and is never removed
  [[ "$(readlink -f "$d")" == "$live" ]] && continue
  n=$((n + 1))
  [[ $n -gt 2 ]] && rm -rf "$d"
done < <(find "$beta" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' | sort -rn | cut -d' ' -f2-)
echo "BETA $sha"
