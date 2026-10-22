#!/usr/bin/env bash
# launch_check.sh <script.js> [<args.json>]: the Dispatcher's step before every Workflow call (HARNESS-C4).
# Prints `LAUNCH OK <sha256 of script> <sha256 of args or ->`, `LAUNCH WARN ...` or `LAUNCH REJECT <reason>`;
# exits 1 on any REJECT. A workflow script has no file access, so the check lives here, not in the script.
# See also: status_check.py check_launch, which holds the landing-time sha test.
set -uo pipefail

WF_DIR="docs/northstar/plans/workflows_2026-10-07/"
rc=0
reject() { echo "LAUNCH REJECT $1"; rc=1; }

[ $# -ge 1 ] || { echo "usage: launch_check.sh <script.js> [<args.json>]" >&2; exit 2; }
script="$1"
args="${2:-}"

root=$(git -C "$(dirname "$script")" rev-parse --show-toplevel 2>/dev/null) || { reject "not inside a checkout"; exit 1; }
root=$(realpath "$root")
rel() { realpath --relative-to="$root" "$1"; }
spath=$(rel "$script")
case "$spath" in
  "$WF_DIR"*) ;;
  *) reject "script not under $WF_DIR"; exit 1 ;;
esac

git -C "$root" fetch -q origin >/dev/null 2>&1 || { reject "no origin"; exit 1; }

on_main() {  # <repo path> <file>
  if ! git -C "$root" cat-file -e "origin/main:$1" 2>/dev/null; then
    reject "$1 not on origin/main"
  elif ! git -C "$root" show "origin/main:$1" | cmp -s - "$2"; then
    reject "$1 differs from origin/main"
  fi
}

on_main "$spath" "$script"
script_sha=$(sha256sum "$script" | cut -d' ' -f1)
args_sha="-"

if [ -n "$args" ]; then
  apath=$(rel "$args")
  on_main "$apath" "$args"
  args_sha=$(sha256sum "$args" | cut -d' ' -f1)
  gaps=$(python3 - "$args" <<'PY'
import json, sys
g = json.load(open(sys.argv[1])).get("gaps") or {}
for gid, v in g.items():
    spec = v.get("spec") if isinstance(v, dict) else None
    print(("OBJ" if spec else "STR") + "\t" + gid + "\t" + (spec or ""))
PY
  ) || { reject "$apath is not valid JSON"; gaps=""; }
  while IFS=$'\t' read -r kind id spec; do
    [ -n "$kind" ] || continue
    if [ "$kind" = STR ]; then
      echo "LAUNCH WARN gap $id has no spec line"
      continue
    fi
    sfile="${spec%:*}"
    sline="${spec##*:}"
    case "$sline" in ''|*[!0-9]*) sline=0 ;; esac
    if [ "$sline" -lt 1 ] || ! git -C "$root" show "origin/main:$sfile" 2>/dev/null | sed -n "${sline}p" | grep -qF -- "$id"; then
      reject "gap $id not in the spec on main"
    fi
  done <<<"$gaps"
fi

[ "$rc" -eq 0 ] && echo "LAUNCH OK $script_sha $args_sha"
exit "$rc"
