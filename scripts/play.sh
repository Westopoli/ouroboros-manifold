#!/usr/bin/env bash
# H-001: open today's main (or a story's scene) built, on the real display. See docs/stories/H-001.md.
# play.sh [--scene <res path>] [--seed N] [--story <id>] [--tree <path>] [--check] [--dry-run] [--keep]
set -uo pipefail
GODOT="$HOME/.local/bin/godot.real"
WINDOW_S=60   # DRAFT-play-window-s
SETTLE_S=10   # DRAFT-play-settle-s
RESOLUTION=1919x1080   # DRAFT-play-resolution; not 1920x1080: a request equal to the project viewport presents only the splash on GNOME Wayland (2026-10-31, DEC-display-fault-measured-2026-10-31)
MIN_FPS=30    # DRAFT-play-min-fps
FPS_S=3       # DRAFT-play-fps-s: consecutive seconds at MIN_FPS
scene=""; seed=""; story=""; tree=""; check=0; dry=0; keep=0; extra=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scene) scene="$2"; shift 2;;
    --seed) seed="$2"; shift 2;;
    --story) story="$2"; shift 2;;
    --tree) tree="$2"; shift 2;;
    --check) check=1; shift;;
    --dry-run) dry=1; shift;;
    --keep) keep=1; shift;;
    *) echo "play.sh: unknown argument $1" >&2; exit 64;;
  esac
done

# 1. Tree
tree_arg="$tree"
if [[ -z "$tree" ]]; then
  tree="$HOME/Projects/om-push/main"
  if [[ $dry -eq 0 ]]; then
    [[ -d "$tree/.git" ]] || git clone -q --shared "$HOME/Projects/ouroboros-manifold" "$tree" || exit 1
    git -C "$tree" fetch -q origin && git -C "$tree" reset -q --hard origin/main || exit 1
  fi
fi
[[ -d "$tree" || $dry -eq 1 ]] || { echo "play.sh: no tree $tree" >&2; exit 1; }

# 1b. --tree plays a shared scratch clone at the tree's HEAD, so Godot's rewrite of tracked
# .import/.uid files never dirties the named tree. Under TMPDIR (default om-push/tmp, never bare /tmp);
# removed on every exit unless --keep.
if [[ -n "$tree_arg" && $dry -eq 0 ]]; then
  sha=$(git -C "$tree" rev-parse HEAD) || exit 1
  export TMPDIR="${TMPDIR:-$HOME/Projects/om-push/tmp}"; mkdir -p "$TMPDIR" || exit 1
  scratch=$(mktemp -d "$TMPDIR/play-${sha:0:12}-XXXX") || exit 1
  [[ $keep -eq 1 ]] || trap 'rm -rf "$scratch"' EXIT
  git clone -q --shared "$tree" "$scratch" && git -C "$scratch" checkout -q "$sha" || exit 1
  tree="$scratch"
  echo "scratch: $tree"
fi

# 3. Story: the Scene line replaces --scene and --seed
if [[ -n "$story" ]]; then
  line=$(sed -n 's/^Scene: *//p' "$tree/docs/stories/$story.md" | head -1)
  [[ -n "$line" ]] || { echo "play.sh: no Scene: line in docs/stories/$story.md" >&2; exit 1; }
  read -r -a parts <<<"$line"
  scene="${parts[0]}"; seed=""; extra=("${parts[@]:1}")
fi
[[ -n "$seed" ]] && extra=(--seed "$seed" "${extra[@]}")

# DEC-play-check-scratch-userdir-2026-10-30: --check runs Godot under a scratch XDG_DATA_HOME so a stored profile cannot change the scene reached.
# See also: scripts/specfactory/merge_gate.sh FINDING-ambient-user-dir
envp=""; [[ $check -eq 1 ]] && envp="XDG_DATA_HOME=$tree/xdg "
# H-031: Xwayland leaves the window unmapped, so a Wayland session launches the Wayland driver; always windowed.
# See also: docs/stories/H-031.md
wayland=0; dflags="--windowed --resolution $RESOLUTION"
[[ -n "${WAYLAND_DISPLAY:-}" ]] && { wayland=1; dflags="--display-driver wayland $dflags"; }
launch="${envp}$GODOT --path $tree $dflags${scene:+ $scene}"
build="cd $tree && scripts/build_pipe_linux.sh"
# 8. Dry run
if [[ $dry -eq 1 ]]; then
  echo "tree: $tree"; echo "build: $build"
  echo "launch: $launch -- ${extra[*]:-}"
  [[ $check -eq 1 ]] && echo "capture: $tree/scripts/specfactory/screen_capture.sh $tree/proof.png"
  exit 0
fi

# DEC-play-display-check-first-2026-10-30: no display exits before the build and the Godot import,
# so nothing under $GODOT runs without a display.
[[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]] || { echo "play.sh: no display" >&2; exit 1; }

# 2. Build
if ! out=$(cd "$tree" && scripts/build_pipe_linux.sh 2>&1); then
  echo "$out" | tail -20; echo "play.sh: build failed" >&2; exit 1
fi
mkdir -p "$tree/pipe" && cp "$tree/dist/linux/ouroboros_pipe" "$tree/pipe/ouroboros_pipe" || exit 1

# 4. Import once
# Godot idles forever after a project.godot parse error, so watch the output for it.
implog=$(mktemp)
timeout 600 "$GODOT" --headless --path "$tree" --import </dev/null >"$implog" 2>&1 &
ipid=$!
while kill -0 "$ipid" 2>/dev/null; do
  if grep -qE "Error parsing|Couldn't load file|Can't run project" "$implog"; then
    kill "$ipid" 2>/dev/null; tail -20 "$implog"; echo "play.sh: Godot import failed (project.godot)" >&2; exit 1
  fi
  sleep 1
done
wait "$ipid"; rc=$?
if [[ $rc -ne 0 ]]; then tail -20 "$implog"; echo "play.sh: Godot import failed (exit $rc)" >&2; exit 1; fi

# 5. Launch on the real display. H-059: one real-display run at a time across both gate channels; play.lock is held
# until this script exits (the game itself is started with fd 8 closed so it never keeps the lock).
# See also: scripts/specfactory/screen_capture.sh
mkdir -p "$HOME/Projects/om-push" && exec 8>>"$HOME/Projects/om-push/play.lock" && flock 8 || exit 1
export PLAY_LOCK_HELD=1
port=""
if [[ $check -eq 1 ]]; then
  port=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
  extra+=(--qa-port "$port")
fi
log="$tree/.play.log"
[[ $check -eq 1 ]] && mkdir -p "$tree/xdg"
pflag=(); [[ $wayland -eq 1 ]] && pflag=(--print-fps)
setsid nohup ${envp:+env "${envp% }"} "$GODOT" --path "$tree" $dflags "${pflag[@]}" ${scene:+"$scene"} -- "${extra[@]}" >"$log" 2>&1 8>&- &
gpid=$!

# qa_scene <port>: the scene the QA daemon reports, empty when it does not answer.
# See also: docs/stories/H-068.md (a self-connect echoes the request back; the helper refuses it first)
qa_scene() {
  python3 "$(dirname "${BASH_SOURCE[0]}")/qa_wait_port.py" "$1" --timeout 2 >/dev/null || return 1
  python3 -c '
import json,socket,sys
s=socket.create_connection(("127.0.0.1",int(sys.argv[1])),timeout=10)
s.sendall(b"[\"state\"]\n"); b=b""
while not b.endswith(b"\n"): b+=s.recv(65536)
print(json.loads(b)["result"]["scene"])' "$1" 2>/dev/null
}

# 6. Window
t=0
if [[ $wayland -eq 1 ]]; then
  # No X window under the Wayland driver: qa_state answers (with --check) and the last FPS_S fps lines are all >= MIN_FPS.
  until { [[ $check -eq 0 ]] || [[ -n "$(qa_scene "$port")" ]]; } &&
        [[ $(grep -oE 'FPS: *[0-9]+' "$log" | tail -n "$FPS_S" | awk -v m="$MIN_FPS" '$NF>=m' | wc -l) -eq $FPS_S ]]; do
    if [[ $t -ge $WINDOW_S ]]; then
      echo "PLAY REJECT wayland window: no qa_state or under ${MIN_FPS} fps for ${FPS_S}s after ${WINDOW_S}s"; tail -20 "$log"; exit 2
    fi
    sleep 1; t=$((t+1))
  done
  echo "PLAY window ${t}s wayland"
else
  # X11: xdotool finds the window by name and xwininfo reports it IsViewable (Xwayland leaves it IsUnMapped).
  state=""
  until wid=$(xdotool search --name Ouroboros 2>/dev/null | head -1); [[ -n "$wid" ]] &&
        state=$(xwininfo -id "$wid" 2>/dev/null | sed -n 's/.*Map State: *//p') && [[ "$state" == IsViewable ]]; do
    if [[ $t -ge $WINDOW_S ]]; then
      if [[ -n "$wid" ]]; then echo "PLAY REJECT window unmapped ${state:-unknown}"
      else echo "PLAY REJECT no window after ${WINDOW_S}s"; fi
      tail -20 "$log"; exit 2
    fi
    sleep 1; t=$((t+1))
  done
  echo "PLAY window ${t}s"
fi

# 7. Check
if [[ $check -eq 1 ]]; then
  sleep "$SETTLE_S"
  got=$(qa_scene "$port")
  want="${scene:-$(sed -n 's/^run\/main_scene="\(.*\)"/\1/p' "$tree/project.godot")}"
  if [[ "$got" != "$want" ]]; then kill "$gpid" 2>/dev/null; echo "PLAY REJECT scene $got wanted $want"; exit 3; fi
  echo "PLAY scene $got reached"
  # H-031 proof: a real capture of the desktop while the scene is up; the method is the second word of its CAPTURE line.
  cap=$("$tree/scripts/specfactory/screen_capture.sh" "$tree/proof.png"); crc=$?
  kill "$gpid" 2>/dev/null
  echo "$cap"
  method=$(sed -n 's/^CAPTURE \(portal\) .*/\1/p' <<<"$cap")
  if [[ $crc -ne 0 || -z "$method" ]]; then echo "PLAY REJECT proof capture failed (exit $crc)"; exit 4; fi
  echo "PLAY proof $tree/proof.png $method"
fi
exit 0
