class_name ChronicleJump
extends RefCounted

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")
const DEDUP_THRESHOLD := 0.4
const STOP_WORDS := ["the", "a", "an", "of", "in", "to", "and", "for", "with", "on", "at", "by",
	"from", "as", "is", "was", "were", "that", "this", "their", "its", "it", "his", "her", "he",
	"she", "they", "had", "have", "not", "no", "one", "over", "twice", "before", "than", "then",
	"when", "which", "who", "still", "only", "more", "most", "much", "would", "could", "did",
	"done", "been", "being", "there", "never", "ever", "once", "up", "out", "off", "into", "onto",
	"other"]

var time_jump_id: String = ""
var span_years: int = 0
var faction_names: Dictionary = {}
var ownership_timeline: Array = []
var keyframes: Array = []
var entries: Array = []
var dropped_entries: Array = []
var errors: Array = []
var ok: bool = false


func load_file(path: String) -> bool:
	var text := FileAccess.get_file_as_string(path)
	if text == "":
		errors = ["cannot read %s" % path]
		ok = false
		return false
	var parsed = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		errors = ["not a JSON object: %s" % path]
		ok = false
		return false
	return load_dict(parsed)


func load_dict(fixture: Dictionary) -> bool:
	errors.clear()
	dropped_entries.clear()

	var start: Dictionary = fixture.get("time_jump_start", {})
	time_jump_id = String(start.get("time_jump_id", ""))
	span_years = int(start.get("span_years", 0))
	faction_names = start.get("faction_names", {})
	ownership_timeline = start.get("ownership_timeline", [])
	keyframes = fixture.get("keyframes", [])

	var raw: Array = fixture.get("entries", []).duplicate(true)
	if QaPlants.is_active("entries-duplicate") and raw.size() >= 3:
		raw.append(_near_copy(raw[2]))

	var deduped := _dedup(raw)
	_validate_count(deduped)
	_validate_categories(deduped)
	_validate_words(deduped)
	_validate_keyframes(deduped)

	if QaPlants.is_active("order-shuffled"):
		deduped.reverse()
	entries = deduped

	ok = errors.is_empty()
	return ok


func _near_copy(e: Dictionary) -> Dictionary:
	var copy: Dictionary = e.duplicate(true)
	copy["entry_id"] = String(e.get("entry_id", "")) + "_dup"
	copy["base_form"] = String(e.get("base_form", "")) + " Or so the record keeps."
	return copy


func expanded_text_for(e: Dictionary) -> String:
	if QaPlants.is_active("expand-noop"):
		return String(e.get("base_form", ""))
	return String(e.get("expanded_form", ""))


func mentions_for(e: Dictionary, form: String) -> Array:
	var key := "mentions" if form == "base" else "expanded_mentions"
	var out: Array = []
	for m in e.get(key, []):
		out.append(m)
	return out


func entries_by_tick(t: int) -> Array:
	var out: Array = []
	for e in entries:
		if int(e.get("tick_range_start", 0)) <= t:
			out.append(e)
	return out


func keyframes_by_tick(t: int) -> Array:
	var out: Array = []
	for kf in keyframes:
		if int(kf.get("tick", 0)) <= t:
			out.append(kf)
	return out


func total_span_ticks() -> int:
	var last := 0
	for e in entries:
		last = max(last, int(e.get("tick_range_end", 0)))
	for kf in keyframes:
		last = max(last, int(kf.get("tick", 0)))
	return last


func hash() -> int:
	var parts := PackedStringArray()
	for e in entries:
		parts.append("%s|%s|%d" % [e.get("entry_id", ""), e.get("category", ""), int(e.get("tick_range_start", 0))])
	for kf in keyframes:
		parts.append("k%d|%s|%s" % [int(kf.get("tick", 0)), kf.get("system_id", ""), kf.get("owner", "")])
	var s := "~".join(parts)
	return s.hash()


func _strip_punct(w: String) -> String:
	var punct := ".,;:!?—-\"'()[]"
	var s := w
	while s.length() > 0 and punct.find(s[0]) != -1:
		s = s.substr(1)
	while s.length() > 0 and punct.find(s[s.length() - 1]) != -1:
		s = s.substr(0, s.length() - 1)
	return s


func _content_words(text: String) -> PackedStringArray:
	var out := PackedStringArray()
	for w in text.to_lower().split(" ", false):
		var clean := _strip_punct(w)
		if clean.length() >= 4 and not STOP_WORDS.has(clean):
			out.append(clean)
	return out


func _overlap_fraction(a: PackedStringArray, b: PackedStringArray) -> float:
	var aset := {}
	for w in a:
		aset[w] = true
	var bset := {}
	for w in b:
		bset[w] = true
	if aset.is_empty() or bset.is_empty():
		return 0.0
	var shared := 0
	for w in aset:
		if bset.has(w):
			shared += 1
	return float(shared) / float(min(aset.size(), bset.size()))


func _dedup(raw: Array) -> Array:
	var kept: Array = []
	var kept_words: Array = []
	for e in raw:
		var words := _content_words(String(e.get("base_form", "")))
		var drop := false
		var reason := ""
		if not QaPlants.is_active("entries-duplicate"):
			for i in range(kept.size()):
				var frac := _overlap_fraction(words, kept_words[i])
				if frac >= DEDUP_THRESHOLD:
					drop = true
					reason = "shares %.0f%% content words with %s" % [frac * 100.0, kept[i].get("entry_id", "")]
					break
		if drop:
			dropped_entries.append({"entry_id": e.get("entry_id", ""), "reason": reason})
		else:
			kept.append(e)
			kept_words.append(words)
	return kept


func _validate_count(list: Array) -> void:
	if list.size() < 5 or list.size() > 10:
		errors.append("entry count %d outside 5..10" % list.size())


func _validate_categories(list: Array) -> void:
	if list.is_empty():
		errors.append("no entries")
		return
	var first_cat := String(list[0].get("category", ""))
	if not first_cat.begins_with("consequence_"):
		errors.append("entry 0 category %s is not a consequence cluster" % first_cat)
	var has_lineage := false
	var counts := {}
	for e in list:
		var cat := String(e.get("category", ""))
		counts[cat] = int(counts.get(cat, 0)) + 1
		if cat.begins_with("lineage_"):
			has_lineage = true
	if not has_lineage:
		errors.append("no lineage entry present")
	for cat in counts:
		if int(counts[cat]) > 2:
			errors.append("category %s appears %d times, cap is 2" % [cat, counts[cat]])
	var last_score := INF
	for i in range(1, list.size()):
		var score := float(list[i].get("score", 0.0))
		if score > last_score:
			errors.append("entry %d score %.2f is not descending" % [i, score])
		last_score = score


func _validate_words(list: Array) -> void:
	for e in list:
		var eid := String(e.get("entry_id", ""))
		var base := String(e.get("base_form", ""))
		var expanded := expanded_text_for(e)
		var base_n := base.split(" ", false).size()
		var exp_n := expanded.split(" ", false).size()
		if base_n >= 90:
			errors.append("%s base form %d words, at or over 90" % [eid, base_n])
		if exp_n >= 140:
			errors.append("%s expanded form %d words, at or over 140" % [eid, exp_n])
		if exp_n <= base_n:
			errors.append("%s expanded form adds no words" % eid)
		var base_m := mentions_for(e, "base")
		var exp_m := mentions_for(e, "expanded")
		var new_mention := false
		for m in exp_m:
			var hit := false
			for bm in base_m:
				if bm.get("kind") == m.get("kind") and bm.get("id") == m.get("id"):
					hit = true
					break
			if not hit:
				new_mention = true
				break
		if not new_mention:
			errors.append("%s expanded form adds no new mention" % eid)


func _validate_keyframes(list: Array) -> void:
	for e in list:
		var s := int(e.get("tick_range_start", 0))
		var t := int(e.get("tick_range_end", 0))
		var found := false
		for kf in keyframes:
			var kt := int(kf.get("tick", -1))
			if kt >= s and kt <= t:
				found = true
				break
		if not found:
			errors.append("%s tick range [%d,%d] contains no keyframe" % [e.get("entry_id", ""), s, t])
	for ot in ownership_timeline:
		var found2 := false
		for kf in keyframes:
			if int(kf.get("tick", -1)) == int(ot.get("tick", -2)) \
					and String(kf.get("system_id", "")) == String(ot.get("system_id", "x")) \
					and String(kf.get("owner", "")) == String(ot.get("owner", "y")):
				found2 = true
				break
		if not found2:
			errors.append("ownership change at tick %d/%s has no matching keyframe" % [int(ot.get("tick", -1)), ot.get("system_id", "")])
