#!/usr/bin/env bash
# Ad-hoc sign Mac binaries (notarization is Westley's step). Usage: scripts/codesign_macos.sh <path>...
set -euo pipefail
[ $# -ge 1 ] || { echo "usage: $0 <path>..." >&2; exit 2; }
for p in "$@"; do codesign -s - --force "$p"; done
