#!/usr/bin/env bash
# scripts/qa_harness.sh -- F6 seam (two-day push, item 5). Drives the real
# game (not a mockup) through the QADaemon autoload and scenes/harness/**,
# both piece C7's (docs/northstar/plans/briefs/2026-09-22-two-day-push.md).
# C7 is built: cmd_run/cmd_liveness/cmd_scan drive scenes/harness/harness.tscn
# using the same Xvfb pattern scripts/mockup_qa.sh already proved (docs/
# northstar/plans/briefs/2026-09-22-mockup-qa-harness.md): a private Xvfb,
# software GL, never the live seat's DISPLAY (:0 or :1). cmd_liveness talks
# to the QADaemon autoload (autoload/qa_daemon.gd) over its --qa-port TCP
# protocol and drives real OS-level input via xdotool, matched to the
# window by X class (WM_CLASS "Ouroboros"), not by title -- the title set
# in scenes/harness/harness.gd's _ready() never changes under Xvfb.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HARNESS_SCENE="scenes/harness/harness.tscn"

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

usage() {
    cat >&2 <<EOF
usage:
  qa_harness.sh run [--res WxH] [--timeout N]
  qa_harness.sh liveness [--timeout N]
  qa_harness.sh scan <outdir>

run/liveness drive ${HARNESS_SCENE} (piece C7).
EOF
    exit 2
}

require_harness() {
    if [[ ! -f "$REPO_ROOT/$HARNESS_SCENE" ]]; then
        echo "qa_harness.sh: ${HARNESS_SCENE} missing; nothing to run" >&2
        usage
    fi
}

# A fresh worktree has neither logs/ (autoload/sim_bridge.gd and
# scenes/tactical/perf_logger.gd both write cwd-relative log files even
# under --path) nor .venv (the harness's own Python deps) and boots straight
# to the error screen without them.
ensure_worktree_setup() {
    mkdir -p "$REPO_ROOT/logs"
    if [[ ! -e "$REPO_ROOT/.venv" ]]; then
        ln -s "$HOME/Projects/agora/.venv" "$REPO_ROOT/.venv"
    fi
}

# A fresh directory outside the checkout: Godot writes crash/perf logs and
# other cwd-relative files (autoload/sim_bridge.gd's logs/, perf_logger.gd)
# even with --path pinning the project root elsewhere, and this is real
# game state, not a disposable mockup -- cmd_run/cmd_liveness never launch
# from inside $REPO_ROOT.
scratch_dir() {
    mktemp -d -t qa_harness.XXXXXX
}

cmd_run() {
    require_harness
    ensure_worktree_setup
    local res="1280x720" timeout="120"
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --res) res="$2"; shift 2 ;;
            --timeout) timeout="$2"; shift 2 ;;
            *) echo "run: unknown arg $1" >&2; exit 2 ;;
        esac
    done

    local scratch out_abs
    scratch="$(scratch_dir)"
    out_abs="$scratch/out"
    mkdir -p "$out_abs"

    set +e
    ( cd "$scratch" && env -u DISPLAY -u WAYLAND_DISPLAY -u XAUTHORITY \
        LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe OM_SAVE_DIR="$scratch/saves" \
        timeout --kill-after=10 "$timeout" \
        xvfb-run -a -s "-screen 0 ${res}x24" \
        "$GODOT" --path "$REPO_ROOT" --display-driver x11 --rendering-driver opengl3 \
            -w --position 0,0 --resolution "$res" --fixed-fps 30 --quit-after 100000 \
            "res://${HARNESS_SCENE}" >"$out_abs/stdout.log" 2>"$out_abs/stderr.log" )
    local exit_code=$?
    set -e
    echo "$exit_code" > "$out_abs/exit.txt"
    echo "$out_abs"
    return "$exit_code"
}

# A free TCP port for the QADaemon (autoload/qa_daemon.gd) --qa-port
# listener, picked from a scratch range and verified free right before use.
pick_qa_port() {
    python3 -c '
import random, socket
for _ in range(50):
    port = random.randint(47400, 47499)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        s.close()
        print(port)
        break
    except OSError:
        s.close()
'
}

cmd_liveness() {
    require_harness
    ensure_worktree_setup
    local timeout="60"
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --timeout) timeout="$2"; shift 2 ;;
            *) echo "liveness: unknown arg $1" >&2; exit 2 ;;
        esac
    done

    local scratch out_abs qa_port
    scratch="$(scratch_dir)"
    out_abs="$scratch/out"
    mkdir -p "$out_abs"
    qa_port="$(pick_qa_port)"
    if [[ -z "$qa_port" ]]; then
        echo "liveness: could not find a free port in the scratch range" >&2
        exit 2
    fi

    # The daemon's --qa-port protocol has no window-manager under Xvfb, so
    # the Godot window is found by X class (WM_CLASS "Ouroboros"), not by
    # title -- confirmed with xprop against a live run: harness.gd's
    # window_set_title("QA:" + name) never lands under Xvfb even though the
    # daemon reports the harness as the current scene.
    set +e
    ( cd "$scratch" && env -u DISPLAY -u WAYLAND_DISPLAY -u XAUTHORITY \
        LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe OM_SAVE_DIR="$scratch/saves" \
        timeout --kill-after=10 "$timeout" \
        xvfb-run -a -s "-screen 0 1280x720x24" \
        python3 - "$REPO_ROOT" "$GODOT" "$HARNESS_SCENE" "$qa_port" "$out_abs" "$timeout" <<'LIVENESS_PY'
import json, os, socket, subprocess, sys, time

repo_root, godot_bin, harness_scene, port_s, out_dir, timeout_s = sys.argv[1:7]
port = int(port_s)
timeout_s = float(timeout_s)
deadline = time.monotonic() + timeout_s


def fail(reason):
    with open(os.path.join(out_dir, "liveness.json"), "w") as f:
        json.dump({"ok": False, "reason": reason}, f, indent=2)
    print("LIVENESS FAIL %s" % reason)
    sys.exit(1)


stdout_log = open(os.path.join(out_dir, "stdout.log"), "wb")
stderr_log = open(os.path.join(out_dir, "stderr.log"), "wb")

proc = subprocess.Popen(
    [godot_bin, "--path", repo_root, "--display-driver", "x11",
     "--rendering-driver", "opengl3", "-w", "--position", "0,0",
     "--resolution", "1280x720", "--fixed-fps", "30",
     "--quit-after", "100000", "res://%s" % harness_scene,
     "--", "--qa-port", str(port)],
    stdout=stdout_log, stderr=stderr_log,
)


def send(verb_args):
    with socket.create_connection(("127.0.0.1", port), timeout=5) as sock:
        sock.sendall((json.dumps(verb_args) + "\n").encode())
        sock.settimeout(5)
        buf = b""
        while b"\n" not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
    return json.loads(buf.decode())


# See also: docs/stories/H-068.md (a connect to a closed port can connect to itself; qa_wait_port refuses that)
connected = subprocess.run(
    [sys.executable, os.path.join(repo_root, "scripts", "qa_wait_port.py"), str(port),
     "--timeout", str(max(0.0, deadline - time.monotonic()))],
    stdout=subprocess.DEVNULL,
).returncode == 0
if not connected:
    proc.kill()
    fail("port %d never opened" % port)

try:
    state1 = send(["state"])
except Exception as e:
    proc.kill()
    fail("first state call failed: %s" % e)

expected_scene = "res://%s" % harness_scene
if not state1.get("ok") or state1.get("result", {}).get("scene") != expected_scene:
    proc.kill()
    fail("first state mismatch: %s" % state1)

try:
    subprocess.run(
        ["xdotool", "search", "--sync", "--onlyvisible", "--class", "Ouroboros"],
        check=True, timeout=max(1, deadline - time.monotonic()),
    )
except Exception as e:
    proc.kill()
    fail("xdotool search --class Ouroboros failed: %s" % e)

for _ in range(2):
    subprocess.run(["xdotool", "mousemove", "640", "360", "click", "1"], check=False)
    time.sleep(0.3)
subprocess.run(["xdotool", "key", "space"], check=False)
time.sleep(0.5)

try:
    state2 = send(["state"])
except Exception as e:
    proc.kill()
    fail("second state call failed: %s" % e)

stdout_log.flush()
with open(os.path.join(out_dir, "stdout.log"), "r", errors="replace") as f:
    qa_input_lines = [line for line in f if line.startswith("QA_INPUT")]

proc.kill()
try:
    proc.wait(timeout=10)
except Exception:
    pass

result = {
    "state1": state1,
    "state2": state2,
    "os_inputs": len(qa_input_lines),
}
with open(os.path.join(out_dir, "liveness.json"), "w") as f:
    json.dump(result, f, indent=2)

ok = len(qa_input_lines) >= 2 and state1.get("ok") and state2.get("ok")
if ok:
    print("LIVENESS OK os_inputs=%d scene=%s" % (len(qa_input_lines), state1["result"]["scene"]))
    sys.exit(0)
else:
    print("LIVENESS FAIL insufficient QA_INPUT lines or state not ok (os_inputs=%d)" % len(qa_input_lines))
    sys.exit(1)
LIVENESS_PY
    )
    local exit_code=$?
    set -e
    echo "$exit_code" > "$out_abs/exit.txt"
    echo "$out_abs"
    return "$exit_code"
}

cmd_scan() {
    local outdir="${1:-}"
    if [[ -z "$outdir" || ! -d "$outdir" ]]; then
        echo "scan: usage: qa_harness.sh scan <outdir>" >&2
        exit 2
    fi
    local errors_file="$outdir/errors.txt"
    local marks_file="$outdir/marks.txt"
    : > "$errors_file"
    : > "$marks_file"
    for log in "$outdir/stdout.log" "$outdir/stderr.log"; do
        [[ -f "$log" ]] || continue
        grep -nE 'SCRIPT ERROR|^ERROR:|^USER ERROR|Node not found' "$log" >> "$errors_file" || true
        grep -nE 'QA_WARN|QA_CALL' "$log" >> "$marks_file" || true
    done
    echo "errors: $(wc -l < "$errors_file")"
}

[[ $# -ge 1 ]] || usage
sub="$1"
shift
case "$sub" in
    run) cmd_run "$@" ;;
    liveness) cmd_liveness "$@" ;;
    scan) cmd_scan "$@" ;;
    *) usage ;;
esac
