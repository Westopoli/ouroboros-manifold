#!/usr/bin/env bash
# Method rev 2 item 6: journals are printed from git and never hand-written.
# One line per first-parent commit, oldest first: "- MM-DD HH:MM <sha7> <subject>".
# See also: docs/northstar/plans/workflows_2026-10-07/journal_2026-10-09.md (the last hand-built one).
set -e
case "${1:-}" in
  -h|--help)
    echo "usage: scripts/journal.sh [<since ref>] [<until ref>]  (defaults: origin/main~40 origin/main)"
    exit 0
    ;;
esac
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
since="${1:-origin/main~40}"
until_ref="${2:-origin/main}"
exec git -C "$repo" log --first-parent --reverse --date=format:'%m-%d %H:%M' --format='- %ad %h %s' "$since..$until_ref"
