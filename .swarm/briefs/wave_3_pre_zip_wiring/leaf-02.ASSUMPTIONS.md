# leaf-02 assumptions

- Test runner bash exec (`bash scripts/run_godot_tests.sh ...`) blocked by harness permission in this session. RED→GREEN proof unrunnable. Static analysis sub:
  - test_privacy_modal.gd staged asserts: scene exists, instantiates, Button has "Accept"/"Continue", Label has "PRIVATE PLAYTEST BUILD", script src contains `pressed` + `user://privacy_accepted`, flag-set re-instantiate path sets `_skip_to_loading_screen=true` and visible-button-count==0.
  - privacy_modal.gd staged: _ready checks `FileAccess.file_exists("user://privacy_accepted")` → sets `_skip_to_loading_screen=true`, hides self, defers route. Else connects pressed→_on_accept_pressed. _on_accept opens FLAG_PATH write, closes, routes via `/root/SceneRouter.go_to("loading_screen")`.
  - privacy_modal.tscn staged: Control root w/ Background ColorRect, CenterContainer/VBoxContainer, Label "PrivacyText" (verbatim 4-paragraph block per spec lines 63-68), Button "AcceptButton" text="Accept & Continue".
- SceneRouter resolved via `/root/SceneRouter` get_node lookup (not class-name autoload var) — avoids needing autoload class hint at parse time in test contexts where SceneRouter autoload not loaded by `--script` SceneTree harness.
- Privacy text uses Label not RichTextLabel. Test accepts either.
- Verbatim text per spec lines 63-68 — header line "PRIVATE PLAYTEST BUILD", blank, then 3-line paragraph. Spec block has 3 paragraphs in 4-line form (header + body); copied exactly.
- Real-path temp-copies created during attempted run, then removed post-attempt. Real destinations clean. Staging is sole landing zone.
