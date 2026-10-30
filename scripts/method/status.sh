#!/usr/bin/env bash
# status.sh: H-002, what is in flight, what landed, what waits on Westley, from git alone.
# Eight sections in a fixed order (docs/stories/H-002.md). Reads origin/main (main when
# there is no origin) of the repo it runs in. Bash plus git; nothing else is consulted
# except ~/Projects/om-push/metrics/<week>.csv (H-003) and ~/Projects/om-push/main.
# See also: scripts/specfactory/status_check.py, which checks the same trailers.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1
if git rev-parse -q --verify origin/main >/dev/null; then MAIN=origin/main; else MAIN=main; fi
WEEK=$(date +%G-W%V)
SINCE=$(date -d "-$(( $(date +%u) - 1 )) days" +%F)
NOW=$(date +%s)
ind() { sed 's/^/  /'; }

echo "IN FLIGHT"
git branch -r --no-merged "$MAIN" --format='%(refname:short)' | grep '^origin/s/' | while read -r b; do
    age=$(( (NOW - $(git log -1 --format=%ct "$b")) / 86400 ))
    stale=""; [ "$age" -gt 14 ] && stale=" stale"
    echo "$b ${age}d $(git log -1 --format=%s "$b")$stale"
done | ind

echo "LANDED $WEEK"
git log --first-parent --since="$SINCE" --grep='^Land ' --format='%h %s' "$MAIN" | grep -E '^[0-9a-f]+ Land ' | while read -r h s; do
    echo "$h $s"
    for k in Story Played Gate; do
        v=$(git log -1 --format="%(trailers:key=$k,valueonly)" "$h" | sed '/^$/d')
        [ -n "$v" ] && echo "    $k: $v"
    done
done | ind

echo "WAITING ON WESTLEY"
words_file=$(mktemp); trap 'rm -f "$words_file"' EXIT
for f in docs/bible/stories.md docs/method/harness.md; do git show "$MAIN:$f" 2>/dev/null; done >"$words_file"
seen=$(git log --first-parent --format=%s "$MAIN" | grep -E '^Seen ' | awk '{print $2}')
git log --first-parent --reverse --grep='^Land ' --format='%H' "$MAIN" | while read -r H; do
    s=$(git log -1 --format=%s "$H")
    case "$s" in "Land "*) ;; *) continue ;; esac
    id=$(echo "$s" | awk '{print $2}')
    echo "$seen" | grep -qx -- "$id" && continue
    stub=""; case "$s" in *"(stub)") stub=" (stub)" ;; esac
    play=$(git log -1 --format='%(trailers:key=Play,valueonly)' "$H" | sed '/^$/d')
    words=$(grep -E "^\| *$id *\|" "$words_file" | head -1 | awk -F'|' '{ for (i = 3; i <= NF; i++) if ($i ~ /^ *"/) { print $i; exit } }' | sed 's/^ *//;s/ *$//')
    echo "$id$stub  run: $play"
    [ -n "$words" ] && echo "    $words"
done | ind

echo "TEST DEFECTS $WEEK"
git log --since="$SINCE" --grep='^Test-defect:' --format='%h' "$MAIN" | while read -r h; do
    why=$(git log -1 --format='%(trailers:key=Test-defect,valueonly)' "$h" | sed '/^$/d')
    echo "$h $(git show --name-only --format= "$h" | tr '\n' ' ')-- $why"
done | ind

echo "SWEEPS"
{
    git log --first-parent --format='%h %s' "$MAIN" | grep -E '^[0-9a-f]+ Sweep ' | head -3
    last=$(git log --first-parent --format='%H %s' "$MAIN" | grep -E '^[0-9a-f]+ Sweep ' | head -1 | cut -d' ' -f1)
    git log --first-parent --format='%h %s' ${last:+"$last..$MAIN"} "$MAIN" 2>/dev/null | grep -E '^[0-9a-f]+ Revert.*Land '
} | ind

echo "DECISIONS $WEEK"
git log --since="$SINCE" --grep='^Decision:' --format='%h %(trailers:key=Decision,valueonly)' "$MAIN" | grep -E '^[0-9a-f]+ .+' | ind

echo "NUMBERS $WEEK"
csv="$HOME/Projects/om-push/metrics/$WEEK.csv"
if [ -s "$csv" ]; then tail -1 "$csv" | ind; else echo "no report yet" | ind; fi

echo "LAST PLAYED"
git -C "$HOME/Projects/om-push/main" rev-parse HEAD 2>/dev/null | ind
exit 0
