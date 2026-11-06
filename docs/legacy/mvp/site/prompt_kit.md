# Image prompt kit for the playtester site

For Westley, generating concept art by hand in the Gemini web app (Nano Banana Pro, ~100 generations/day on AI Pro, up to 14 reference images per generation). Not automated — `docs/northstar/research/gemini_compute.md` explains why. Files land in `ouroboros-site/public/art/<page-slug>/`.

## Shared style block

Paste at the top of every prompt. From `docs/bible/references/E-18/notes.md`'s register (the only visual register the bible has committed to so far):

> Low-poly, blocky, toy-like register — more blocky than Age of Empires Online, flatter and warmer than photoreal (Art of Rally's flat low-detail look). Clean, readable silhouettes, one per unit type, no fussy detail. Cinematic sense of scale behind the action when a scene calls for background (huge distant objects, busy but readable). Combat reads as mass and weight, not sparse skirmishers, when a scene shows combat. No text anywhere in the image. No existing-IP names, logos, insignia, or ship/character designs — thematic inspiration only, never copied content.

## Negative list

No text or UI chrome baked into the image. No photoreal detail or realistic lighting. No existing-franchise ships, uniforms, insignia, or characters (Star Wars, Halo, etc. — inspiration only, per `CLAUDE.md`'s no-IP-exposure rule). No human faces as the focal subject (this is a commander-of-a-task-force game, not a character portrait game, per the hub). No price tags, store badges, or review-quote overlays.

## Reference images to attach

Up to 14 per generation. Use what's relevant to the page:

- `docs/bible/references/E-18/E-18-1.png` and `E-18-2.png` — the two Age of Empires Online shots the register is built from.
- Live renders of the three unit types in the layer demo (`https://ouroboros-site.fly.dev/layers/` — orbit and screenshot a Raider, Interceptor, and Vanguard). The other three unit types (Bastion, Bombard, Warden) have GLBs under `assets/eras/settled_reach/units/` but are not in the live demo yet; screenshot them in Godot or the Blender source (`docs/legacy/blender_stuff/the-settled-reach/`) if wanted as references.

## Per-page prompts

The order these appear on the site, and which concept each home-page beat needs, is fixed in `narrative.md` (this directory). The full per-beat prompts for the home page — including the five animations and the real galaxy-view capture — live in `concept_prompts.md`; the per-offer lines below serve the `/offers/` pages.


One offer page per row in `docs/legacy/mvp/distinctiveness.md`. Each prompt is the shared style block plus the line below; 2 to 4 images per page is enough.

| Page | Prompt line |
|---|---|
| A living galaxy that moves without the player | A galaxy-scale strategic map: dozens of small star systems connected by glowing route lines, some systems bright and thriving, others dim and contested — a living network, not a static board. |
| Generational carry-forward | Two versions of the same region years apart: one showing fresh construction and a strong garrison, the other showing battle scars, rebuilt structures, and a different faction's colors — same place, changed by time. |
| A chronicle that reads as real history | A scrolling chronicle panel beside the galaxy map: short history entries with small icons (a battle, a treaty, a founding), styled like an in-universe historical record, not a notification log. |
| Elegiac tone with dry, earned humor | A quiet debrief screen after a mission: a short, dryly-worded summary line next to a commander portrait silhouette (no face), warm and a little wry, not somber. |
| The tragedy of understanding | A tactical top-down moment: a small force outmaneuvering a larger one through a chokepoint and high ground, with clear directional arrows showing the surround — the moment of realizing why a fight was won or lost. |
| Commander, not king | A single task force (a handful of units) accepting orders from a civilization's command screen — no base-building UI, no economy panel, just the force and its objective. |
| Missions generated from real trouble | A mission briefing screen where the objective text visibly references a specific galaxy event (a besieged region, a betrayed ally) — the mission clearly grew out of the world state, not a random pick. |
| Single-layer positional skill ceiling | A tactical scene with visible elevation: units on a ridge with line-of-sight advantage over units in a low approach, terrain readable at a glance. |
| Art of Rally low-poly look | A clean unit lineup, six silhouettes side by side (Raider, Interceptor, Vanguard, Warden, Bombard, Bastion), flat lighting, each instantly distinguishable by shape alone. |
| The 2.5D layer and vision system | A cutaway side view of stacked elevation layers with a unit on one layer and a faint, degraded view of another unit two layers away — visually showing vision falling off with layer distance. |
| Multi-era on one skeleton | Two versions of the same galaxy-map layout rendered in different eras (a near-future spacefaring look and a distinct later-era look) side by side, same structure, different dress. |
| Multiplayer lockstep and cross-era matches | Two commander UIs side by side implying two players in the same match, each from a different era's visual dress, meeting on one shared map. |

## Discipline

The site says "private playtest, please do not share the link" and carries no store link or price (`ouroboros-site/src/layouts/Base.astro`'s banner). Generated images are concept art for a target, not screenshots — the site's footer says so on every page; don't caption an image in a way that contradicts that.
