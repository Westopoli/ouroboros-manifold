# C4-E1 Era Library tests

Rules proved: R-110-05, R-110-06, R-110-07 (E-16), rulings A45, A51 and A58 (Q-C4-E1-04 to 08 answered). Test: `tests/test_era_library_live.gd`.
Run: `godot --headless --path . --script tests/test_era_library_live.gd` (no display needed).

## Result
- On main: RED (2 assertions at the first gate: `qa_set_sources` missing, so the rest do not run; 56 more assertions wait behind it). It fails at the first contract check (`era_library` root has no `qa_set_sources`); the later checks do not run until that method exists.
- Satisfiable (A58 revision): a temporary reference patch (manifest-reading stub scenes, a stub `era_ownership.gd`, and the three manifests given the new keys) took it from 3 live-pack failures to 60 of 60 passing. Planting a Play button, a "Role:" label, or removing `test_only` from `test_era` each failed the matching assertions. All reverted, none committed.

## Contract the test fixes (scene roots under scenes/era_library/)
- `qa_set_sources(packs_root, ownership_path)` on both scenes; `""` or a missing ownership file is the dev default (every installed era owned). With no call, both read `res://assets/eras/`.
- `era_library` `qa_state()` gains `eras`: `{id, name, owned}`.
- `era_detail` `qa_state()` gains `era_id, name, owned, tiers, roster[{abstract_type, category}]`; neither state has mastery or progress keys.

## What it checks
- Over fixture packs: valid packs listed, a pack missing a required key (R-146-03) hidden, names read from the manifest, all owned in dev, no mastery or tier progress anywhere (A51): no text, ProgressBar node, or state key with mastery/progress/"not yet tracked".
- Over the live packs: `settled_reach` and `greek_placeholder` listed; `roman` and `1980s` (hard-coded today, no pack) not listed.
- Detail: identity, tiers [1,2,3] and roster read from the manifest.
- No hard-coded text: a scan of every Label, RichTextLabel and Button for the legacy strings.

## Controls
- Planted "Legionary" label must be caught by the legacy-text scan.
- Planted "Mastery" label, ProgressBar and tier_progress key must all be caught by the progress scan.
- A broken pack, once repaired, must appear (the validation filter is not just hiding everything).

## A58 additions (this revision)
- Fixture manifests carry `era_spatial_scale`, `era_tone`, `era_order`. Library over fixtures must list `[zz_tide, zz_dunes]` (orders 10, 20: reverse of alphabetical, so a name sort fails), hide `zz_hidden` (`test_only`) and `zz_notone` (missing `era_tone`), and show scale and tone as labels and as `spatial_scale`, `tone`, `order` state keys. Controls: restoring `era_tone` and dropping `test_only` must make them appear.
- Live packs: `test_era` not listed; `settled_reach` and `greek_placeholder` listed in the order of their manifests' `era_order` (read from the manifest, so the test does not pin which comes first); every card has non-empty scale and tone.
- Ownership: this runner is a debug build (asserted). With the real store `user://era_ownership.json` and an explicit path both planted as `{"owned":["zz_dunes"]}`, every pack is still owned in library and detail (the real store is backed up and restored). The release reader is the seam `era_ownership.gd`: `owned_from_store(path, installed_ids)` (file limits owned, `{"owned":[]}` owns nothing, no file owns all installed) and `owned_ids(installed_ids, path)` (debug owns all).
- Detail: roster title label is the type id (case-insensitive match), a label shows each category, no label text or state key with `role` or `description`; no Button whose text has play/start campaign/begin campaign/launch era, and no `can_play`, `play_enabled` or `playable` state key; the library gets the same Button scan. Controls: planted "Play this era" Button and "Role: flanker" label plus `role_text` key are caught.
- New Campaign is not tested (A58 08 only asks it not break).

## Not covered (gaps)
- Card click routing to the detail (a desktop probe belongs with the UI unit).
- A malformed ownership file, and a store listing an id that is not installed (A58 does not say; the reader should ignore unknown ids, untested).
- Release-build behaviour of the screens themselves (the runner is debug); only the reader unit is tested for release logic.
- The sentence text of the three installed manifests (the validator tests prove non-empty text only).

## Doer unit plan (each about one file, under about 100 lines; order matters)
1. `scripts/specfactory/pack_validate.py` (piece K1, M0, attached): add `era_spatial_scale`, `era_tone`, `era_order` to `REQUIRED_KEYS`; era_order must be int and not bool, the text keys non-empty text, `test_only` optional bool; each a named finding. About 15 lines. Tests: `tests/specfactory/test_pack_validate.py` (branch push/ERA-validator-tests).
2. `assets/eras/settled_reach/manifest.json`, `assets/eras/greek_placeholder/manifest.json` (K2 owns `assets/eras/greek_placeholder/**`; no piece owns `settled_reach/**` or `test_era/**`, so the Architect must assign those two before a Doer starts), same piece as 1: add the three keys, one plain sentence each from the bible where it has one, "(placeholder)" marked otherwise; `test_era` also gets `"test_only": true`. Mechanical-diff test must stay green (the new keys are not mechanical keys).
3. `scenes/era_library/era_pack_source.gd` (G-eralib, new, about 70 lines): read `<root>/*/manifest.json`, keep packs with all REQUIRED_KEYS and not `test_only`, sort ascending by `era_order`, `tiers()`, `roster()`.
4. `scenes/era_library/era_ownership.gd` (G-eralib, new, about 30 lines): the seam in the contract header.
5. `scenes/era_library/era_library.gd` (G-eralib, now 198 lines, rewritten, may split card building into `era_card.gd`): cards from units 3 and 4 with name, scale, tone, owned; `qa_set_sources`; delete legacy card text, tier and mastery bars, COMING SOON and the settled_reach-only gate (A58 08: no play control).
6. `scenes/era_library/era_detail.gd` (G-eralib, now 376 lines, split into detail plus a roster file): identity, tiers, roster rows titled by type id plus category, no role text; remove mastery card, purchase overlay and any play control.
7. `autoload/ui_data_bus.gd` (G-uidatabus, one unit, takes its next id; settings and Era Library units go one at a time): repoint `get_all_eras`, `get_era_detail`, `is_era_accessible` at units 3 and 4, or delete once neither screen calls them. About 15 lines. `autoload/sim_bridge_data_source.gd` (owner G-simbridge, not G-eralib) holds the hard-coded era list and the load-screen name lookup at line 110; it needs its own row or an ordering with G-simbridge.
Order: 1 and 2 first (validator and manifests before the screen), then 3, 4, then 5 and 6, then 7.

## Q candidates
- Q-C4-E1-04 ownership store format and path: (a) JSON `{"owned":[era_id,...]}` in `user://`; (b) one marker file per era; (c) key in settings.cfg. Also how a build is "development" (debug flag vs feature tag).
- Q-C4-E1-05 R-110-05 needs spatial scale, tone and chronological order, but the pack manifest and pack_validate.py have none of them: (a) add optional manifest keys `era_scale`, `era_tone`, `era_order` (a pack-contract change landing first); (b) show name and ownership only and amend the rule; (c) take them from a separate era index file.
- Q-C4-E1-06 roster display: the manifest has unit ids and categories but no display names or role text: (a) show the abstract_type and category only; (b) add display names to the manifest.
- Q-C4-E1-07 does `test_era` (installed, passes validation) appear in the library: (a) yes; (b) hidden by a dev/test flag in the manifest.
- Q-C4-E1-08 the playable gate: today only settled_reach opens its detail and others read COMING SOON. With manifest-driven cards, which packs are selectable: (a) all valid ones; (b) only those with a campaign.

Q-C4-E1-04 to 08: answered in Addendum 24 (A58) as ownership store JSON, three required manifest keys, id plus category roster, test_only, viewing screen only; the tests above pin them. The candidate text below is kept as the question history.
