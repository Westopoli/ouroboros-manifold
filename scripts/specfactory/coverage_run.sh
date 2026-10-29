#!/usr/bin/env bash
# coverage_run.sh <repo> <out_dir> | --accept <summary>: the weekly coverage number (HARNESS-coverage).
# Copies <repo> (not .git) to <out_dir>/tree, builds it with gcov instrumentation and runs the csim tests (gcov
# into <out_dir>/A), then the transport tests (gcov into <out_dir>/B), then coverage_report.py writes
# <out_dir>/functions.csv and summary.json. Failing tests do not abort the run; their exit codes go in the summary.
# --accept byte-copies a summary to the baseline status_check.py check_coverage reads.
# See also: coverage_report.py, status_check.py check_coverage.
set -uo pipefail

if [ "${1:-}" = "--accept" ]; then
  [ -f "${2:-}" ] || { echo "coverage_run.sh: no summary at ${2:-}" >&2; exit 1; }
  base="$(cd "$(dirname "$0")/../.." && pwd)/docs/northstar/plans/drift_audits/coverage_baseline.json"
  mkdir -p "$(dirname "$base")" && cp "$2" "$base"
  exit
fi
[ $# -eq 2 ] || { echo "usage: coverage_run.sh <repo> <out_dir> | --accept <summary>" >&2; exit 2; }

here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$1" && pwd)"
mkdir -p "$2"
out="$(cd "$2" && pwd)"
tree="$out/tree"
rm -rf "$tree" "$out/A" "$out/B"
mkdir -p "$tree" "$out/A" "$out/B"
tar -C "$repo" --exclude=./.git --exclude=./.godot --exclude=./wt --exclude='*.gcda' -cf - . | tar -C "$tree" -xf -

gcov_into() {  # <dir>: gcov JSON for every .gcda in the tree
  mapfile -t gcda < <(find "$tree" -name '*.gcda')
  [ ${#gcda[@]} -gt 0 ] && { (cd "$1" && gcov -f -j "${gcda[@]}" >/dev/null) || exit 1; }
}

cd "$tree" || exit 1
# -B: a copied release build must not count as up to date at -O0.
make -B all pipe/ouroboros_pipe pipe/ouroboros_pipe_dbg OPT="-O0 --coverage" || { echo "coverage_run.sh: build failed" >&2; exit 1; }
pytest tests/csim --ignore=tests/csim/scale --ignore=tests/csim/controls -q -p no:cacheprovider
echo $? > "$out/exit_a"
gcov_into "$out/A"
find "$tree" -name '*.gcda' -delete
pytest tests/transport -q -p no:cacheprovider
echo $? > "$out/exit_b"
gcov_into "$out/B"
python3 "$here/coverage_report.py" "$out" "$repo"
