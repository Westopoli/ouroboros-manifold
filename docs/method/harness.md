# Harness stories

Work on the method or the tooling. Same columns as `docs/bible/stories.md`, same loop, same trailers; the story file is `docs/stories/H-###.md`; the gate flag is `harness`.

| Story | In Westley's words | Status | Depth |
|---|---|---|---|
| H-001 | "I type one command and today's main opens, built, in front of me; with a story id it opens at that story's scene." | Spec'd | `docs/stories/H-001.md` |
| H-002 | "One command prints what is in flight, what landed this week, what waits on me and the four numbers, from git alone." | Spec'd | `docs/stories/H-002.md` |
| H-003 | "Every night the token report writes the four numbers for the week, and the share of spend that went into building and testing is the first of them." | Spec'd | `docs/stories/H-003.md` |
| H-004 | "Every night the 30B plays today's main through the same command I use and what it finds shows up as harness stories, never as edits." | Spec'd | `docs/stories/H-004.md` |
| H-005 | "The method check after a compaction tests six rules against the chat's transcript and cites this directory, not the retired documents." | Spec'd | `docs/stories/H-005.md` |
| H-007 | "The 30B plays the nightly session itself, through the QA port, instead of the game sitting open." | On hold (Westley 2026-10-30) | no story file yet |
| H-006 | "The gate reads the story's flag from the story file and the merge message; it needs no pieces row and no owner table, so a story branch lands by itself." | Tested | `docs/stories/H-006.md` |

Order: H-006 first (every later landing needs it; it carries the last pieces.toml row ever written, its own), then H-001, H-002, H-003, H-005, H-004.
