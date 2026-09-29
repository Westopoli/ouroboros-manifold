"""om_chapter_get_number public accessor.

Backs the `chapter` field HDR4 (docs profile, gap-fix-and-migration-plan.md
Wave 1) adds for the save sidecar (S4) and the pipe frames: the current
chapter number, sourced from `gen_state.chapter_number` (csrc/generational.c),
set by `om_chapter_start(w, chapter)`.

Public accessor (not yet implemented):
  uint32_t om_chapter_get_number(const om_world *w)
  - no gen_state / no chapter started -> 0
  - after om_chapter_start(w, N) -> N
  - after a second om_chapter_start(w, M) -> M (not cached/one-shot)

RED on main: the symbol does not exist in libouroboros.so and no conftest.py
binding exists either, so `lib.om_chapter_get_number` raises AttributeError
via ctypes' own dlsym lookup on the CDLL handle. GREEN once the header
declaration, the generational.c implementation, and the conftest.py binding
all land.
"""
def test_fresh_world_with_no_chapter_started_returns_zero(lib, world_factory):
    w = world_factory(n_regions=1)
    assert lib.om_chapter_get_number(w) == 0


def test_after_chapter_start_returns_that_chapter_number(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_chapter_start(w, 3)
    assert lib.om_chapter_get_number(w) == 3


def test_second_chapter_start_updates_the_number(lib, world_factory):
    """Proves the value tracks gen_state.chapter_number live, not a cached or
    one-shot read: a second om_chapter_start with a different chapter number
    must change the accessor's return value."""
    w = world_factory(n_regions=1)
    lib.om_chapter_start(w, 3)
    assert lib.om_chapter_get_number(w) == 3
    lib.om_chapter_start(w, 7)
    assert lib.om_chapter_get_number(w) == 7
