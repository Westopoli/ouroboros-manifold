#!/usr/bin/env bash
# Static Linux pipe exe: dist/linux/ouroboros_pipe (no libouroboros.so). See steam-multiplayer-wiring-spec W8a.
set -euo pipefail
cd "$(dirname "$0")/.."
out=dist/linux; mkdir -p "$out"
${CC:-cc} -std=c11 -Wall -Wextra -Icsrc -O2 \
  -fno-fast-math -ffp-contract=off -fno-math-errno -msse2 -mfpmath=sse -fexcess-precision=standard \
  -static -o "$out/ouroboros_pipe" csrc/*.c csrc/pipe/om_pipe.c csrc/pipe/pipe_*.c -lm
echo "$out/ouroboros_pipe"
