extends Node

const SAVE_NAME_MAX := 64
const KEY_CODE_MAX := 32


func sanitize(raw: String, rule: String) -> String:
	match rule:
		"save_name":
			return _sanitize_save_name(raw)
		"key_code":
			return _sanitize_key_code(raw)
		_:
			return ""


func is_valid(raw: String, rule: String) -> bool:
	return sanitize(raw, rule) != ""


func _sanitize_save_name(raw: String) -> String:
	var result := ""
	for i in range(raw.length()):
		var c := raw[i]
		var code := raw.unicode_at(i)
		if _is_unicode_letter(code) or _is_unicode_digit(code):
			result += c
		elif c == " " or c == "\t":
			result += " "
		elif c == "-" or c == "\u2014":
			result += c
		# All other characters silently dropped
	result = result.strip_edges()
	if result.length() > SAVE_NAME_MAX:
		result = result.left(SAVE_NAME_MAX)
	if result.strip_edges() == "":
		return ""
	return result


func _sanitize_key_code(raw: String) -> String:
	var upper := raw.to_upper()
	var result := ""
	for i in range(upper.length()):
		var c := upper[i]
		var code := upper.unicode_at(i)
		if (code >= 65 and code <= 90) or (code >= 48 and code <= 57) or c == "-":
			result += c
	if result.length() > KEY_CODE_MAX:
		result = result.left(KEY_CODE_MAX)
	return result


func _is_unicode_letter(code: int) -> bool:
	if code >= 65 and code <= 90:
		return true
	if code >= 97 and code <= 122:
		return true
	if code >= 0x00C0 and code <= 0x024F:
		return true
	if code >= 0x0370 and code <= 0x03FF:
		return true
	if code >= 0x0400 and code <= 0x04FF:
		return true
	if code >= 0x0500 and code <= 0x052F:
		return true
	if code >= 0x1E00 and code <= 0x1EFF:
		return true
	if code >= 0x3040 and code <= 0x30FF:
		return true
	if code >= 0x4E00 and code <= 0x9FFF:
		return true
	if code >= 0xAC00 and code <= 0xD7AF:
		return true
	if code >= 0x0600 and code <= 0x06FF:
		return true
	if code >= 0x0900 and code <= 0x097F:
		return true
	return false


func _is_unicode_digit(code: int) -> bool:
	return code >= 48 and code <= 57
