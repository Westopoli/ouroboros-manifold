#!/usr/bin/env bash
# H-001: open today's main (or a story's scene) built, on the real display. See docs/stories/H-001.md.
# play.sh [--scene <res path>] [--seed N] [--story <id>] [--tree <path>] [--check] [--dry-run]
set -uo pipefail
GODOT="$HOME/.local/bin/godot.real"
WINDOW_S=60   # DRAFT-play-window-s
SETTLE_S=10   # DRAFT-play-settle-s
scene=""; seed=""; story=""; tree=""; check=0; dry=0; extra=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scene) scene="$2"; shift 2;;
    --seed) seed="$2"; shift 2;;
    --story) story="$2"; shift 2;;
    --tree) tree="$2"; shift 2;;
    --check) check=1; shift;;
    --dry-run) dry=1; shift;;
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
# .import/.uid files never dirties the named tree. Under TMPDIR; nothing is removed.
if [[ -n "$tree_arg" && $dry -eq 0 ]]; then
  sha=$(git -C "$tree" rev-parse HEAD) || exit 1
  scratch=$(mktemp -d "${TMPDIR:-/tmp}/play-${sha:0:12}-XXXX") || exit 1
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

launch="$GODOT --path $tree${scene:+ $scene}"
build="cd $tree && scripts/build_pipe_linux.sh"
# 8. Dry run
if [[ $dry -eq 1 ]]; then
  echo "tree: $tree"; echo "build: $build"
  echo "launch: $launch -- ${extra[*]:-}"
  exit 0
fi

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

# 5. Launch on the real display
[[ -n "${DISPLAY:-}" ]] || { echo "play.sh: no display" >&2; exit 1; }
port=""
if [[ $check -eq 1 ]]; then
  port=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
  extra+=(--qa-port "$port")
fi
log="$tree/.play.log"
setsid nohup "$GODOT" --path "$tree" ${scene:+"$scene"} -- "${extra[@]}" >"$log" 2>&1 &
gpid=$!

# 6. Window
t=0
until xdotool search --name Ouroboros >/dev/null 2>&1; do
  if [[ $t -ge $WINDOW_S ]]; then
    echo "PLAY REJECT no window after ${WINDOW_S}s"; tail -20 "$log"; exit 2
  fi
  sleep 1; t=$((t+1))
done
echo "PLAY window ${t}s"

# 7. Check
if [[ $check -eq 1 ]]; then
  sleep "$SETTLE_S"
  got=$(python3 -c '
import json,socket,sys
s=socket.create_connection(("127.0.0.1",int(sys.argv[1])),timeout=10)
s.sendall(b"[\"state\"]\n"); b=b""
while not b.endswith(b"\n"): b+=s.recv(65536)
print(json.loads(b)["result"]["scene"])' "$port")
  kill "$gpid" 2>/dev/null
  want="${scene:-$(sed -n 's/^run\/main_scene="\(.*\)"/\1/p' "$tree/project.godot")}"
  if [[ "$got" == "$want" ]]; then echo "PLAY scene $got reached"; else echo "PLAY REJECT scene $got wanted $want"; exit 3; fi
fi
exit 0
