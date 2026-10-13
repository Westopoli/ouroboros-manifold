#!/usr/bin/env bash
# macOS DEBUG pipe exe for the sim viewer, built natively on a Mac: dist/macos/ouroboros_pipe_dbg (arm64 by default, ARCH=x86_64 for Intel).
# Not run on this Linux box. arm64 rejects the x86 SSE flags.
# See also: scripts/build_pipe_macos.sh (same compile line, without -DOM_DEBUG_INJECT)
set -euo pipefail
cd "$(dirname "$0")/../.."
arch=${ARCH:-arm64}
out=dist/macos; mkdir -p "$out"
flags="-std=c11 -Wall -Wextra -Icsrc -O2 -fno-fast-math -ffp-contract=off -fno-math-errno -DOM_DEBUG_INJECT -arch $arch"
[ "$arch" = x86_64 ] && flags="$flags -m""sse2 -mfpmath""=sse"
# shellcheck disable=SC2086
${CC:-clang} $flags -o "$out/ouroboros_pipe_dbg" csrc/*.c csrc/pipe/om_pipe.c csrc/pipe/pipe_*.c -lm
scripts/codesign_macos.sh "$out/ouroboros_pipe_dbg"
echo "$out/ouroboros_pipe_dbg"
