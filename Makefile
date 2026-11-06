# Makefile for the Ouroboros C sim core.
#
# Fenced (parent-owned): Agora writes csrc/*.c but does not edit this file or the
# header. Two shared libraries:
#   libouroboros.so      release build the fenced tests load
#   libouroboros_dbg.so  same sources + fault injection, for positive controls
#
# Determinism (docs/northstar/research/c_rewrite.md): identical flags on every
# platform, no fast-math, no FMA contraction, SSE math to kill x87 excess
# precision. The C trace must be byte-identical across Linux/Windows/macOS.
#
# OPT (default -O2) and WERROR (default 0, add -Werror when 1) are the merge
# gate's knobs (`make OPT=-O2 WERROR=1`). The top-level libouroboros*.so
# targets always build at the repo root regardless of OPT -- conftest.py
# depends on that path. build/O0/ and build/O2/ are separate, always-O0 /
# always-O2 output dirs (checksum_trace.py compares one tree against the
# other in the same run, so their optimization level is not left to
# whatever OPT the caller happened to pass).

OPT     ?= -O2
WERROR  ?= 0

CC      ?= cc
SRC     := $(wildcard csrc/*.c)
HDR     := csrc/ouroboros_sim.h

CFLAGS_COMMON   := -std=c11 -Wall -Wextra -Icsrc -fPIC
# Per-target flags: -msse2 -mfpmath=sse only on x86 (arm64 rejects them);
# -fexcess-precision=standard only where the compiler accepts it (clang does
# not); -ffp-contract=off always (dropping it diverges at tick 100).
# MSVC equivalents (no Makefile build there): /fp:precise /fp:contract-
ARCH ?= $(firstword $(subst -, ,$(shell $(CC) -dumpmachine)))
CFLAGS_DET_BASE := -fno-fast-math -ffp-contract=off -fno-math-errno
ifneq (,$(filter x86_64 amd64 i386 i486 i586 i686 x86,$(ARCH)))
CFLAGS_DET_BASE += -msse2 -mfpmath=sse
endif
ifneq (,$(shell $(CC) -fexcess-precision=standard -E -x c /dev/null -o /dev/null 2>/dev/null && echo ok))
CFLAGS_DET_BASE += -fexcess-precision=standard
endif
ifeq ($(WERROR),1)
CFLAGS_DET_BASE += -Werror
endif
CFLAGS_DET := $(OPT) $(CFLAGS_DET_BASE)
CFLAGS     := $(CFLAGS_COMMON) $(CFLAGS_DET)

.PHONY: all clean test layout_dump
all: libouroboros.so libouroboros_dbg.so

libouroboros.so: $(SRC) $(HDR)
	$(CC) $(CFLAGS) -shared -o $@ $(SRC)

libouroboros_dbg.so: $(SRC) $(HDR)
	$(CC) $(CFLAGS) -DOM_DEBUG_INJECT -shared -o $@ $(SRC)

# Fixed-optimization output dirs for the O0-vs-O2 determinism gate
# (checksum_trace.py --lib build/O0/libouroboros.so ... equals the build/O2
# run). Always -O0 / always -O2 by name, independent of $(OPT).
build/O0/libouroboros.so: $(SRC) $(HDR)
	mkdir -p build/O0
	$(CC) $(CFLAGS_COMMON) -O0 $(CFLAGS_DET_BASE) -shared -o $@ $(SRC)

build/O0/libouroboros_dbg.so: $(SRC) $(HDR)
	mkdir -p build/O0
	$(CC) $(CFLAGS_COMMON) -O0 $(CFLAGS_DET_BASE) -DOM_DEBUG_INJECT -shared -o $@ $(SRC)

build/O2/libouroboros.so: $(SRC) $(HDR)
	mkdir -p build/O2
	$(CC) $(CFLAGS_COMMON) -O2 $(CFLAGS_DET_BASE) -shared -o $@ $(SRC)

build/O2/libouroboros_dbg.so: $(SRC) $(HDR)
	mkdir -p build/O2
	$(CC) $(CFLAGS_COMMON) -O2 $(CFLAGS_DET_BASE) -DOM_DEBUG_INJECT -shared -o $@ $(SRC)

# T1 placeholder pipe server (csrc/pipe/om_pipe.c); linked against the
# release library. -lm resolves libm symbols already present in
# libouroboros.so's object code (om_region_composite's round(), the region.c
# weak om_sin fallback's sin()) that ctypes.CDLL never had to resolve at
# link time. T1 replaces the source; this target's shape (name, library
# link) does not change.
PIPE_SRC = csrc/pipe/om_pipe.c csrc/pipe/pipe_tactical.c csrc/pipe/pipe_dumps.c csrc/pipe/pipe_net.c
PIPE_DBG_OBJ = $(patsubst csrc/pipe/%.c,pipe/obj_dbg/%.o,$(PIPE_SRC))

pipe/ouroboros_pipe: $(PIPE_SRC) csrc/pipe/pipe_internal.h libouroboros.so
	mkdir -p pipe
	$(CC) $(CFLAGS) -Icsrc/pipe -o $@ $(PIPE_SRC) -L. -louroboros -lm -Wl,-rpath,'$$ORIGIN/..'

# Debug pipe: same as pipe/ouroboros_pipe but compiled with -DOM_DEBUG_INJECT so
# the inject/objective_complete handlers are active (om_pipe.c #ifdef gate).
# Uses a separate object dir (pipe/obj_dbg/) so the two binaries never share .o files.
pipe/obj_dbg/%.o: csrc/pipe/%.c csrc/pipe/pipe_internal.h $(HDR)
	mkdir -p pipe/obj_dbg
	$(CC) $(CFLAGS) -Icsrc/pipe -DOM_DEBUG_INJECT -c -o $@ $<

pipe/ouroboros_pipe_dbg: $(PIPE_DBG_OBJ) libouroboros_dbg.so
	mkdir -p pipe
	$(CC) $(CFLAGS) -o $@ $(PIPE_DBG_OBJ) -L. -louroboros_dbg -lm -Wl,-rpath,'$$ORIGIN/..'

# Layout kit CLI (S-247): prints a layout as JSON; csrc/tools is outside the csrc/*.c wildcard.
# O0 and O2 variants feed the byte-for-byte determinism check (tests/csim/test_layout_kit_determinism.py).
LAYOUT_DUMP_SRC := csrc/tools/layout_dump.c $(wildcard csrc/layout_kit*.c) csrc/terrain_noise.c

layout_dump: $(LAYOUT_DUMP_SRC) $(wildcard csrc/layout_*.h)
	mkdir -p build
	$(CC) $(CFLAGS_COMMON) $(CFLAGS_DET) -o build/layout_dump $(LAYOUT_DUMP_SRC) -lm

build/O0/layout_dump: $(LAYOUT_DUMP_SRC) $(wildcard csrc/layout_*.h)
	mkdir -p build/O0
	$(CC) $(CFLAGS_COMMON) -O0 $(CFLAGS_DET_BASE) -o $@ $(LAYOUT_DUMP_SRC) -lm

build/O2/layout_dump: $(LAYOUT_DUMP_SRC) $(wildcard csrc/layout_*.h)
	mkdir -p build/O2
	$(CC) $(CFLAGS_COMMON) -O2 $(CFLAGS_DET_BASE) -o $@ $(LAYOUT_DUMP_SRC) -lm

# Convenience: build then run the fenced C-sim test suite.
test: all
	python3 -m pytest tests/csim -p no:cacheprovider

clean:
	rm -f libouroboros.so libouroboros_dbg.so pipe/ouroboros_pipe pipe/ouroboros_pipe_dbg
	rm -rf build pipe/obj_dbg
