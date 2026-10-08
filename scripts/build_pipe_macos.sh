#!/usr/bin/env bash
# macOS pipe exe, built natively on a Mac: dist/macos/ouroboros_pipe (arm64 by default, ARCH=x86_64 for Intel).
# Not run on this Linux box. clang rejects -fexcess-precision; arm64 rejects the x86 SSE flags.
set -euo pipefail
cd "$(dirname "$0")/.."
arch=${ARCH:-arm64}
out=dist/macos; mkdir -p "$out"
flags="-std=c11 -Wall -Wextra -Icsrc -O2 -fno-fast-math -ffp-contract=off -fno-math-errno -arch $arch"
[ "$arch" = x86_64 ] && flags="$flags -m""sse2 -mfpmath""=sse"
# shellcheck disable=SC2086
${CC:-clang} $flags -o "$out/ouroboros_pipe" csrc/*.c csrc/pipe/om_pipe.c csrc/pipe/pipe_*.c -lm
"$(dirname "$0")/codesign_macos.sh" "$out/ouroboros_pipe"
echo "$out/ouroboros_pipe"
