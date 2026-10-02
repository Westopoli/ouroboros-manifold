# C4-E1 Era Library tests

Rules proved: R-110-05, R-110-06, R-110-07 (E-16), ruling A45. Test: `tests/test_era_library_live.gd`.
Run: `godot --headless --path . --script tests/test_era_library_live.gd` (no display needed).

## Result
- On main: RED. It fails at the first contract check (`era_library` root has no `qa_set_sources`); the later checks do not run until that method exists.
- Satisfiable: a temporary reference patch (manifest-reading stub scenes) made all 28 assertions pass. It was reverted and is not committed.

## Contract the test fixes (scene roots under scenes/era_library/)
- `qa_set_sources(packs_root, ownership_path)` on both scenes; `""` or a missing ownership file is the dev default (every installed era owned). With no call, both read `res://assets/eras/`.
- `era_library` `qa_state()` gains `eras`: `{id, name, owned, mastery_text, tier_text}`.
- `era_detail` `qa_state()` gains `era_id, name, owned, tiers, roster[{abstract_type, category}], mastery_text, tier_text`.

## What it checks
- Over fixture packs: valid packs listed, a pack missing a required key (R-146-03) hidden, names read from the manifest, all owned in dev, mastery and tier progress read "not yet tracked".
- Over the live packs: `settled_reach` and `greek_placeholder` listed; `roman` and `1980s` (hard-coded today, no pack) not listed.
- Detail: identity, tiers [1,2,3] and roster read from the manifest.
- No hard-coded text: a scan of every Label, RichTextLabel and Button for the legacy strings.

## Controls
- Planted "Legionary" label must be caught by the legacy-text scan.
- A broken pack, once repaired, must appear (the validation filter is not just hiding everything).

## Not covered (gaps)
- Card click routing to the detail (a desktop probe belongs with the UI unit).
- An ownership store that is not the dev default (format unset, Q-C4-E1-04).
- Chronological order and spatial scale and tone (no manifest field, Q-C4-E1-05).

## Doer unit plan (each about one file, under about 100 lines)
1. `scenes/era_library/era_pack_source.gd` (G-eralib, new file): read `<root>/*/manifest.json`, keep packs with all `REQUIRED_KEYS`, expose `tiers()` and `roster()`; no scene code.
2. `scenes/era_library/era_ownership.gd` (G-eralib, new file): read the ownership store, dev default every era owned; `owned(era_id)`.
3. `scenes/era_library/era_library.gd` (G-eralib): build cards from units 1 and 2, add `qa_set_sources`, `eras` in `qa_state`; delete the legacy card text ("Available on Steam", COMING SOON, hard-coded `settled_reach` playable check) and the tier/mastery bars, replaced by "not yet tracked" labels. May exceed 100 lines; split card building into `era_card.gd` if so.
4. `scenes/era_library/era_detail.gd` (G-eralib): same sources, roster and tiers from the manifest, `qa_set_sources`, new `qa_state` keys; drop sample chronicle text and the purchase overlay (not manifest-driven). Likely needs a split (left column, right column) into two files.
5. `autoload/sim_bridge_data_source.gd` and `autoload/ui_data_bus.gd` (owner piece not G-eralib; check pieces.toml, needs its own row): remove the hard-coded `get_all_eras`, `get_era_detail`, `is_era_accessible`, or repoint them at unit 1. `get_era_detail` is still read for the load-screen era name at line 110, so repoint, do not just delete.
Order: 1, 2, then 3 and 4 in parallel, then 5 after both screens stop calling UIDataBus.

## Q candidates
- Q-C4-E1-04 ownership store format and path: (a) JSON `{"owned":[era_id,...]}` in `user://`; (b) one marker file per era; (c) key in settings.cfg. Also how a build is "development" (debug flag vs feature tag).
- Q-C4-E1-05 R-110-05 needs spatial scale, tone and chronological order, but the pack manifest and pack_validate.py have none of them: (a) add optional manifest keys `era_scale`, `era_tone`, `era_order` (a pack-contract change landing first); (b) show name and ownership only and amend the rule; (c) take them from a separate era index file.
- Q-C4-E1-06 roster display: the manifest has unit ids and categories but no display names or role text: (a) show the abstract_type and category only; (b) add display names to the manifest.
- Q-C4-E1-07 does `test_era` (installed, passes validation) appear in the library: (a) yes; (b) hidden by a dev/test flag in the manifest.
- Q-C4-E1-08 the playable gate: today only settled_reach opens its detail and others read COMING SOON. With manifest-driven cards, which packs are selectable: (a) all valid ones; (b) only those with a campaign.
