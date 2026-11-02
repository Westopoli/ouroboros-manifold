#!/bin/bash
# Slow-tier sweep of origin/main: worktree, merge_gate.sh --tier slow over the Land ids since the last PASS/BASE row,
# sweeps.md row + empty `Sweep` commit pushed under records.lock; an early reject (no result file) still writes its row, `early <stage>` in the last column. Takes no gate lock (a sweep and a landing gate run at once).
# See also: docs/stories/H-014.md, docs/northstar/plans/2026-10-29-layered-gate-spec.md sections 4, 8 B2 and B3.
# See also: docs/stories/H-034.md (row on early reject), docs/stories/H-021.md.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
SWEEPS=docs/northstar/plans/push/sweeps.md
PUSHDIR="$HOME/Projects/om-push"
DRY=0; [[ "${1:-}" == --dry-run ]] && DRY=1
STAMP=$(date -u +%Y%m%d-%H%M%S)

git -C "$REPO" fetch -q origin || exit 1
BASE=$(git -C "$REPO" show "origin/main:$SWEEPS" | awk -F'|' '{v=$4; gsub(/ /,"",v)} v=="PASS"||v=="BASE"{s=$3; gsub(/ /,"",s)} END{print s}')
[[ -n "$BASE" ]] || { echo "sweep: no PASS or BASE row in $SWEEPS" >&2; exit 1; }
IDS=$(git -C "$REPO" log --first-parent --merges --reverse --format=%s "$BASE..origin/main" \
    | sed -n 's/^Land \([^ ]*\) .*/\1/p' | paste -sd, -)

if [[ $DRY -eq 1 ]]; then
    echo "$HERE/merge_gate.sh --tier slow $PUSHDIR/wt/sweep-$STAMP $BASE $IDS"
    exit 0
fi

WT=$(python3 "$HERE/wt.py" new "sweep-$STAMP" --owner sweep-timer --purpose "slow tier" --base origin/main | sed -n 's/^WT OK \([^ ]*\) .*/\1/p')
[[ -n "$WT" && -d "$WT" ]] || { echo "sweep: wt.py new gave no path" >&2; exit 1; }
SHA=$(git -C "$WT" rev-parse HEAD)
LOG="$WT/../sweep-$STAMP.gate.log"

( cd "$WT" && MERGE_GATE_SUITE_TIMEOUT=2400 MERGE_GATE_PLAYTHROUGH_TIMEOUT=2400 MERGE_GATE_PLAY_TIMEOUT=900 \
    MERGE_GATE_PIECES="$WT/docs/northstar/plans/push/pieces.toml" \
    bash "$HERE/merge_gate.sh" --tier slow "$WT" "$BASE" "$IDS" ) > "$LOG" 2>&1
RC=$?
RESULT="$(dirname "$WT")/candidate_results/$SHA.json"
# An early reject (rc 1) exits before the gate stores a result file: its row is built from the log (H-034). No `GATE ` line, or rc > 1, is a harness error.
if [[ $RC -gt 1 ]] || ! grep -q '^GATE ' "$LOG"; then
    echo "sweep: gate rc $RC, result $RESULT missing or harness error; no row written" >&2
    exit 1
fi

IFS='|' read -r VERDICT NEW N EARLY < <(python3 - "$LOG" "$RESULT" "$RC" "$HERE" <<'PY'
import json, re, sys
from pathlib import Path
log, result, rc, here = sys.argv[1], sys.argv[2], int(sys.argv[3]), Path(sys.argv[4])
known = []
for name in ("lane_plays_known_red.txt", "playthrough_known_red.txt", "gd_tests_known_red.txt"):
    p = here / name
    for line in p.read_text().splitlines() if p.exists() else []:
        for part in line.split("#")[0].split(" :: "):
            known += [x.strip() for x in part.split(",") if x.strip()]
is_known = lambda t: any(t.startswith(k) for k in known)
new, bare, seen, ids_log, bare_log, stage = [], 0, 0, [], 0, ""
for line in Path(log).read_text(errors="replace").splitlines():
    m = re.match(r"GATE (\S+) REJECT(.*)", line)
    if not m:
        continue
    if m.group(1) == "early_exit":
        continue
    seen += 1
    stage = stage or m.group(1)
    found = [i for i in re.findall(r"FAILED (\S+)", m.group(2)) + re.findall(r"'([^']+)'", m.group(2)) if not is_known(i)]
    ids_log += found
    bare_log += 0 if found else 1
    listed = "new failures" in m.group(2)
    ids = [i for i in re.findall(r"'([^']+)'", m.group(2)) if not is_known(i)] if listed else []
    new += ids
    bare += 0 if listed else 1
new = sorted(set(new))
early = not Path(result).exists()
if early:
    new = red = sorted(set(ids_log))
else:
    red = sorted({i for s in json.loads(Path(result).read_text()).get("suites", {}).values()
                  for i in s.get("failing_ids", []) if not is_known(i)})
Path(str(log) + ".red").write_text("".join(i + "\n" for i in red))
reject = new or bare or (rc == 1 and not seen)
n_red = len(red) + (bare_log if early else 0)
print("REJECT" if reject else "PASS", ",".join(new) or "none", n_red, ("early " + stage).strip() if early else "", sep="|")
PY
)
[[ -n "$VERDICT" ]] || { echo "sweep: verdict parse failed" >&2; exit 1; }

DATE=$(date -u +%Y-%m-%d)
LISTREL=docs/northstar/plans/push/sweeps/$DATE-$SHA.txt
if [[ "$N" -gt 20 ]]; then REDCOL=$LISTREL; else REDCOL=$(paste -sd, "$LOG.red" | sed 's/,/, /g'); fi
[[ -n "$EARLY" ]] && REDCOL=$EARLY  # no result file: the last column names the rejecting stage, the ids are in the .red sidecar

exec 9>>"$PUSHDIR/records.lock" 2>/dev/null || { mkdir -p "$PUSHDIR"; exec 9>>"$PUSHDIR/records.lock"; }
flock -w 3600 9 || { echo "sweep: records.lock timeout" >&2; exit 1; }
git -C "$WT" fetch -q origin && git -C "$WT" merge -q --ff-only origin/main || exit 1
if [[ "$N" -gt 20 ]]; then
    mkdir -p "$WT/$(dirname "$LISTREL")"; cp "$LOG.red" "$WT/$LISTREL"; git -C "$WT" add "$LISTREL"
fi
tail -c1 "$WT/$SWEEPS" | od -An -c | grep -q '\\n' || echo >> "$WT/$SWEEPS"
echo "| $(date -u '+%Y-%m-%d %H:%M') | $SHA | $VERDICT | new: $NEW | red: $N | $REDCOL |" >> "$WT/$SWEEPS"
git -C "$WT" add "$SWEEPS"
git -C "$WT" commit -q -m "Sweep row $DATE $VERDICT $SHA"
if [[ "$VERDICT" == PASS && "$N" -eq 0 ]]; then SUBJ="Sweep $DATE pass"; else SUBJ="Sweep $DATE red $N"; fi
git -C "$WT" commit -q --allow-empty -m "$SUBJ"
git -C "$WT" push -q origin HEAD:main || exit 1
PUSHED=$(git -C "$WT" rev-parse HEAD)
flock -u 9
python3 "$HERE/wt.py" done "$WT" "$PUSHED"
echo "SWEEP $VERDICT red $N $PUSHED"
