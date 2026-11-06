#!/usr/bin/env bash
# Mac twin of scripts/play.sh: boot the beta windowed in this checkout, check it over the QA port, capture the screen. Run by hand on the Mac.
# play_mac.sh [--check] [--scene <res path>] [--seed N] [--story <id>] [--dry-run]
# Without --check the game is left open to play; the exit codes are play.sh's: 0 ok, 1 setup, 2 window, 3 scene or console, 4 capture, 64 usage.
# Runs under bash 3.2 (macOS): no mapfile, associative arrays, timeout, flock, setsid or xdotool.
# See also: scripts/play.sh (the Linux way); scripts/replay.sh (Godot search); scripts/setup_editor.sh (builds the pipe, EDITOR READY)
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
WINDOW_S="${OM_PLAY_WINDOW_S:-60}"   # test seam, as play.sh WINDOW_S
SETTLE_S="${OM_PLAY_SETTLE_S:-10}"   # test seam, as play.sh SETTLE_S
RESOLUTION=1919x1080   # not 1920x1080: a request equal to the project viewport presents only the splash (DEC-display-fault-measured-2026-10-31)
MIN_FPS=30
FPS_S=3
scene=""; seed=""; story=""; check=0; dry=0; extra=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scene) scene="${2:-}"; shift 2;;
    --seed) seed="${2:-}"; shift 2;;
    --story) story="${2:-}"; shift 2;;
    --check) check=1; shift;;
    --dry-run) dry=1; shift;;
    *) echo "play_mac.sh: unknown argument $1" >&2; exit 64;;
  esac
done

# Story: the Scene line replaces --scene and --seed (as play.sh)
if [[ -n "$story" ]]; then
  line=$(sed -n 's/^Scene: *//p' "$REPO/docs/stories/$story.md" | head -1)
  [[ -n "$line" ]] || { echo "play_mac.sh: no Scene: line in docs/stories/$story.md" >&2; exit 1; }
  read -r -a parts <<<"$line"
  scene="${parts[0]}"; seed=""; extra=(${parts[@]+"${parts[@]:1}"})
fi
[[ -n "$seed" ]] && extra=(--seed "$seed" ${extra[@]+"${extra[@]}"})

# Godot, first match wins (OM_GODOT_APP is a test seam, as in setup_editor.sh)
godot=""
if [[ -n "${OM_GODOT_APP:-}" ]]; then godot="$OM_GODOT_APP"
elif [[ -n "${GODOT:-}" ]]; then godot="$GODOT"
elif command -v godot >/dev/null 2>&1; then godot="$(command -v godot)"
elif [[ -x "$HOME/.local/bin/godot.real" ]]; then godot="$HOME/.local/bin/godot.real"
elif [[ -x "/Applications/Godot.app/Contents/MacOS/Godot" ]]; then godot="/Applications/Godot.app/Contents/MacOS/Godot"
fi

log="$REPO/.play.log"
if [[ $dry -eq 1 ]]; then
  printf 'setup: %q\n' "$REPO/scripts/setup_editor.sh"
  printf 'launch: '; printf '%q ' "${godot:-godot}" --path "$REPO" --windowed --resolution "$RESOLUTION" --print-fps ${scene:+"$scene"} -- --qa-port PORT ${extra[@]+"${extra[@]}"}; echo
  printf 'capture: screencapture -x %q\n' "$REPO/proof.png"
  exit 0
fi
[[ -n "$godot" ]] || { echo "play_mac.sh: godot not found (install Godot 4.6.3 to /Applications, or set GODOT)" >&2; exit 1; }

# 1. Setup: the editor tree and the pipe; its last line says it is ready
cd "$REPO" || exit 1
if ! out=$("$REPO/scripts/setup_editor.sh" 2>&1) || [[ "$(printf '%s\n' "$out" | tail -n 1)" != "EDITOR READY"* ]]; then
  printf '%s\n' "$out" | tail -20; echo "PLAY REJECT setup"; exit 1
fi

# 2. Launch (macOS has no override for the user data dir, so no sandbox: the game reads Westley's real profile)
port=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
nohup "$godot" --path "$REPO" --windowed --resolution "$RESOLUTION" --print-fps ${scene:+"$scene"} -- --qa-port "$port" ${extra[@]+"${extra[@]}"} >"$log" 2>&1 </dev/null &
gpid=$!

# qa_scene <port>: the scene the QA daemon reports, empty when it does not answer (as play.sh).
qa_scene() {
  python3 -c '
import json,socket,sys
s=socket.create_connection(("127.0.0.1",int(sys.argv[1])),timeout=10)
s.sendall(b"[\"state\"]\n"); b=b""
while not b.endswith(b"\n"): b+=s.recv(65536)
print(json.loads(b)["result"]["scene"])' "$1" 2>/dev/null
}

# 3. Window: no X window on a Mac to ask about, so as play.sh's Wayland branch: qa_state answers (with --check) and the last FPS_S fps lines are all >= MIN_FPS.
t=0
until { [[ $check -eq 0 ]] || [[ -n "$(qa_scene "$port")" ]]; } &&
      [[ $(grep -oE 'FPS: *[0-9]+' "$log" | tail -n "$FPS_S" | awk -v m="$MIN_FPS" '$NF>=m' | wc -l) -eq $FPS_S ]]; do
  if [[ $t -ge $WINDOW_S ]]; then
    kill "$gpid" 2>/dev/null
    echo "PLAY REJECT window: no qa_state or under ${MIN_FPS} fps for ${FPS_S}s after ${WINDOW_S}s"; tail -20 "$log"; exit 2
  fi
  sleep 1; t=$((t+1))
done
echo "PLAY window ${t}s mac"

# 4. Playtest mode: leave the game open
if [[ $check -eq 0 ]]; then
  echo "log: $log (game pid $gpid)"
  exit 0
fi

# 5. Check: the scene, the capture, the console
sleep "$SETTLE_S"
got=$(qa_scene "$port")
want="${scene:-$(sed -n 's/^run\/main_scene="\(.*\)"/\1/p' "$REPO/project.godot")}"
if [[ "$got" != "$want" ]]; then kill "$gpid" 2>/dev/null; echo "PLAY REJECT scene $got wanted $want"; exit 3; fi
echo "PLAY scene $got reached"
rm -f "$REPO/proof.png"
screencapture -x "$REPO/proof.png"; crc=$?
kill "$gpid" 2>/dev/null
if [[ $crc -ne 0 || ! -s "$REPO/proof.png" ]]; then echo "PLAY REJECT proof capture failed (exit $crc)"; exit 4; fi
echo "PLAY proof $REPO/proof.png screencapture"
bad=$(grep -nE 'SCRIPT ERROR|ERROR:|Parser Error' "$log" | head -1)
if [[ -n "$bad" ]]; then echo "PLAY REJECT console $bad"; exit 3; fi
exit 0
