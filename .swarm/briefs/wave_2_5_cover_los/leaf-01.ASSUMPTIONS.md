## Assumptions made during leaf-01

- **Paragraph boundary for `cover_density` in bible_world.md**: replaced single bullet paragraph at line 144 (between `obstacle_density` bullet and `layer_accessibility_mask` bullet). Spec gave range 142-150; actual cover paragraph occupies just line 144. Source: bible_world.md lines 135-150.
- **Damage formula notation**: kept fenced code block, single line `damage_per_attack = base_damage × category_multiplier`, dropped third term. Source: existing formatting at bible_combat.md:420-422.
- **"Cover & Vision" heading style**: used inline bold paragraph lead (`**Cover & Vision.**`) matching sibling paragraphs (`**Attack timing.**`, `**Range.**`, `**Area damage (Bombard).**`, `**Elevation damage bonus.**`) rather than a new `####` subheading, because brief says "replace the Cover paragraph" and sibling style is bold-lead paragraph. Source: bible_combat.md:434-442.
- **Line 529 obstacle LOS extension**: appended a sentence to the existing "No friendly line-of-fire blocking" paragraph rather than inserting a separate line, since the obstacle LOS clause lives mid-paragraph there. Source: bible_combat.md:529.
