#!/usr/bin/env python3
# Mechanical BOFAD rule checker, third Python companion to bofad-check.sh beside
# bofad-format.py and bofad-boxing.py. Carries every SKILL.md rule a parse can
# reach that the shell greps cannot: switch shape, missing braces, repeated
# getters, single-use locals, string concatenation in loops, naming, Oxford comma.
# Type-blind and scope-coarse by design: scopes are brace-depth regions, so an
# inner class merges its methods into one getter-counting scope; accepted ceiling.
# strip_comments_and_strings is duplicated from bofad-boxing.py on purpose, so a
# bare copy-install of this one file keeps working.
# Usage: python bofad-lint.py <file> [more ...] | python bofad-lint.py --selftest
# Output: file:line: RULE: message   (first 3 hits per rule, fix all occurrences)
# Exit 1 when findings exist, 0 clean, 2 on usage or unreadable file.

import re
import sys

MAX_PER_RULE = 3

CODE_EXTS = (".java", ".cs", ".c", ".cpp", ".h", ".hpp", ".ixx")

# Zero-arg calls treated as fresh-value or intentional accessors, never cached; the DOM walk names ride on receivers that reassign every loop iteration.
GETTER_EXCLUSIONS = {"getInstance", "poll", "next", "iterator", "take", "remove", "pop", "read", "readLine", "random", "nanoTime", "currentTimeMillis", "getFirstChild", "getNextSibling", "getLastChild", "getPreviousSibling"}

# Names allowed to break the UPPER_CASE constant rule.
CONSTANT_EXCLUSIONS = {"serialVersionUID"}

PY_EXTS = (".py",)

# Zero-arg Python calls that return a fresh value or mutate the receiver; never cached.
PY_CALL_EXCLUSIONS = {"next", "pop", "popleft", "popitem", "read", "readline", "readlines", "random", "time", "monotonic", "perf_counter", "now", "today", "recv", "acquire", "release", "close", "clear", "reverse", "sort", "copy", "commit", "flush", "get_nowait", "getInstance"}


def strip_comments_and_strings(src):
	# Replace comment/string bodies with spaces, keep newlines so line numbers hold.
	out = []
	i = 0
	n = len(src)
	state = "code"  # code | line | block | str | chr
	while i < n:
		c = src[i]
		nxt = src[i + 1] if i + 1 < n else ""
		if state == "code":
			if c == "/" and nxt == "/":
				state = "line"
				out.append("  ")
				i += 2
				continue
			if c == "/" and nxt == "*":
				state = "block"
				out.append("  ")
				i += 2
				continue
			if c == '"':
				state = "str"
				out.append('"')
				i += 1
				continue
			if c == "'":
				state = "chr"
				out.append("'")
				i += 1
				continue
			out.append(c)
		elif state == "line":
			if c == "\n":
				state = "code"
				out.append(c)
			else:
				out.append(" ")
		elif state == "block":
			if c == "*" and nxt == "/":
				state = "code"
				out.append("  ")
				i += 2
				continue
			out.append(c if c == "\n" else " ")
		elif state == "str":
			if c == "\\":
				out.append("  ")
				i += 2
				continue
			if c == '"':
				state = "code"
				out.append('"')
			else:
				out.append(c if c == "\n" else " ")
		elif state == "chr":
			if c == "\\":
				out.append("  ")
				i += 2
				continue
			if c == "'":
				state = "code"
				out.append("'")
			else:
				out.append(" ")
		i += 1
	return "".join(out)


def match_paren(text, open_pos):
	# Index of the ) matching the ( at open_pos, or -1 when unbalanced.
	depth = 0
	for i in range(open_pos, len(text)):
		if text[i] == "(":
			depth += 1
		elif text[i] == ")":
			depth -= 1
			if depth == 0:
				return i
	return -1


def line_depths(clean_lines):
	# Brace depth at the START of each line, computed from the stripped source.
	depths = []
	depth = 0
	for line in clean_lines:
		depths.append(depth)
		depth += line.count("{") - line.count("}")
	return depths


def next_code_line(clean_lines, start):
	# Index of the first non-blank stripped line at or after start, or -1.
	for i in range(start, len(clean_lines)):
		if clean_lines[i].strip():
			return i
	return -1


RE_OXFORD = re.compile(r"\b\w+, \w+, (?:and|or)\b")
RE_LABEL = re.compile(r"^\s*(?:case\b[^:]*|default\s*):")
RE_TERMINATOR = re.compile(r"^\s*(?:break\s*;|return\b.*;|throw\b.*;|continue\s*;)\s*$")
RE_CONTROL = re.compile(r"^(\s*)(?:\}\s*)?(if|for|while|else if|else|do)\b")
RE_GETTER = re.compile(r"((?:\w+\.)*\w+)\.((?:get|is)[A-Z]\w*|size|length|isEmpty|values|keySet|entrySet|name|ordinal|toString)\(\s*\)")
RE_LOCAL_DECL = re.compile(r"^\s*(?:final\s+)?[A-Za-z_][\w.]*(?:<[^=;]*>)?(?:\[\])*\s+([a-z_]\w*)\s*=")
RE_STRING_DECL = re.compile(r"\bString\s+(\w+)\s*=")
RE_CONST_COMPARE = re.compile(r"^\s*(?:\}\s*)?(?:else\s+)?if\s*\(\s*(\w+)\s*(==[^&|)]+|\.equals\s*\()")
RE_CONST_VALUE = re.compile(r"==\s*(?:-?\d|'|\"|[A-Z][A-Z0-9_]*\b|\w+\.[A-Z][A-Z0-9_]*\b)")
RE_MULTI_DECL = re.compile(r"^\s*(?:final\s+)?[A-Z]\w*(?:<[^=;]*>)?(?:\[\])?\s+[a-z_]\w*\s*,\s*[a-z_]\w*[^(]*;\s*$")
RE_FQN = re.compile(r"(?<![\w.])(?:java|javax|jakarta)\.[a-z_]\w*(?:\.[a-z_]\w*)*\.[A-Z]\w*")
RE_INTERFACE_I = re.compile(r"\binterface\s+I[A-Z]")
RE_CONSTANT = re.compile(r"^\s*(?:(?:public|private|protected)\s+)?static\s+final\s+[\w<>\[\], .]+?\s+([a-z_]\w*)\s*[=;]")
RE_FIELD = re.compile(r"^\s*private\s+(?:final\s+)?(?!static\b)[\w<>\[\], .]+?\s+([a-z]\w*)\s*[=;]")
RE_BARE_LINK = re.compile(r"\{@link\s+([A-Za-z]\w*)\s*\}")
RE_HASH_LINK = re.compile(r"\{@link\s+[^}]*#")
RE_LOWER_COMMENT = re.compile(r"^\s*// ([a-z][^;(){}=<>:/]*)$")
RE_LOOP_HEAD = re.compile(r"^\s*(?:\}\s*)?(?:for|while)\s*\(")

RE_PY_DEF = re.compile(r"^[ \t]*(?:async[ \t]+)?def[ \t]+(\w+)[ \t]*\(")
RE_PY_DEF_FULL = re.compile(r"^[ \t]*(?:async[ \t]+)?def[ \t]+(\w+)[ \t]*\((.*)\)[ \t]*(->[^:]+)?:")
RE_PY_LOOP = re.compile(r"^[ \t]*(?:async[ \t]+)?(?:for|while)\b")
RE_PY_BRANCH = re.compile(r"^[ \t]*(?:elif\b|else[ \t]*:|except\b|case\b)")
RE_PY_CALL = re.compile(r"((?:\w+\.)*\w+)\.(\w+)\(\s*\)")
RE_PY_ASSIGN = re.compile(r"^[ \t]*([A-Za-z_]\w*)[ \t]*(?::[^=]+)?=(?!=)")
RE_PY_STR_INIT = re.compile(r"^[ \t]*(\w+)[ \t]*(?::[ \t]*str[ \t]*)?=[ \t]*(?:''|\"\")[ \t]*$")
RE_PY_LOWER_COMMENT = re.compile(r"^[ \t]*# ([a-z][^;(){}=<>:]*)$")
RE_PY_LITERAL = re.compile(r"^(?:-?\d[\w.]*|''|\"\"|True|False|None|[\[({])")


def strip_python_comments_and_strings(src):
	# Replace comment and string bodies with spaces, keeping newlines and column positions so line numbers and finds hold.
	# Python has no block comment, so the # form and the four quote forms are the whole job. An f-string's {expression} is blanked with the rest of the literal, so a call hiding in one is invisible to every rule below, accepted ceiling.
	out = []
	i = 0
	n = len(src)
	while i < n:
		c = src[i]
		if c == "#":
			while (i < n) and (src[i] != "\n"):
				out.append(" ")
				i += 1
			continue
		if src.startswith('"""', i) or src.startswith("'''", i):
			quote = src[i:i + 3]
			out.append("   ")
			i += 3
			while i < n:
				if src.startswith(quote, i):
					out.append("   ")
					i += 3
					break
				out.append("\n" if src[i] == "\n" else " ")
				i += 1
			continue
		if (c == '"') or (c == "'"):
			out.append(c)
			i += 1
			while i < n:
				if src[i] == "\\":
					out.append(" ")
					i += 1
					if i < n:
						out.append("\n" if src[i] == "\n" else " ")
						i += 1
					continue
				if src[i] == c:
					out.append(c)
					i += 1
					break
				if src[i] == "\n":
					out.append("\n")
					i += 1
					break
				out.append(" ")
				i += 1
			continue
		out.append(c)
		i += 1
	return "".join(out)


def indent_width(line):
	# Visual indent of a line with tabs expanded, so Python blocks compare by depth the way braces do elsewhere.
	stripped = line.lstrip(" \t")
	return len(line[:len(line) - len(stripped)].expandtabs(4))


def python_bodies(clean_lines):
	# Index range [start, end) of each def body, header excluded. A nested def stays inside its parent's range; scope-coarse by design, same as the brace scan.
	bodies = []
	for idx, line in enumerate(clean_lines):
		if not RE_PY_DEF.match(line):
			continue
		indent = indent_width(line)
		last = idx
		for other in range(idx + 1, len(clean_lines)):
			if not clean_lines[other].strip():
				continue
			if indent_width(clean_lines[other]) <= indent:
				break
			last = other
		if last > idx:
			bodies.append((idx + 1, last + 1))
	return bodies


def python_loop_lines(clean_lines):
	# Indexes of every line sitting inside a for or while body.
	inside = set()
	for idx, line in enumerate(clean_lines):
		if not RE_PY_LOOP.match(line):
			continue
		indent = indent_width(line)
		for other in range(idx + 1, len(clean_lines)):
			if not clean_lines[other].strip():
				continue
			if indent_width(clean_lines[other]) <= indent:
				break
			inside.add(other)
	return inside


def split_params(text):
	# Top-level comma split, so an annotation like Dict[str, int] stays one parameter.
	parts = []
	depth = 0
	current = ""
	for c in text:
		if c in "([{":
			depth += 1
		elif c in ")]}":
			depth -= 1
		if (c == ",") and (depth == 0):
			parts.append(current)
			current = ""
			continue
		current += c
	if current.strip():
		parts.append(current)
	return parts


def camel_violation(name):
	# True when a name breaks house lowerCamelCase. Dunders belong to the language and UPPER_CASE constants earn their underscores.
	if name.startswith("__") or name.endswith("__"):
		return False
	core = name.lstrip("_")
	if core.upper() == core:
		return False
	return "_" in core


def check_python_scopes(clean_lines, hit):
	loop_lines = python_loop_lines(clean_lines)
	for start, end in python_bodies(clean_lines):
		# Repeated zero-arg calls on the identical receiver; a branch or loop header resets the counts, same reasoning as the brace-language scan.
		seen = {}
		flagged = set()
		for ln in range(start, end):
			if RE_PY_BRANCH.match(clean_lines[ln]) or RE_PY_LOOP.match(clean_lines[ln]):
				seen = {}
			for m in RE_PY_CALL.finditer(clean_lines[ln]):
				receiver = m.group(1)
				call = m.group(2)
				if (call in PY_CALL_EXCLUSIONS) or call.startswith("__") or receiver.endswith(")"):
					continue
				key = receiver + "." + call
				if key in flagged:
					continue
				if key in seen:
					hit("REPEATED CALL", ln + 1, key + "() repeats in this scope, cache it in a local")
					flagged.add(key)
				else:
					seen[key] = ln

		# Single-use locals folded only when the lone read sits on the very next statement.
		for ln in range(start, end):
			m = RE_PY_ASSIGN.match(clean_lines[ln])
			if not m:
				continue
			name = m.group(1)
			reads = []
			for other in range(ln + 1, end):
				if re.search(r"\b" + re.escape(name) + r"\b", clean_lines[other]):
					reads.append(other)
			if (len(reads) == 1) and (reads[0] == next_code_line(clean_lines, ln + 1)):
				hit("SINGLE-USE LOCAL", ln + 1, name + " is read once on the next line, fold it into the use site")

		# String grown with += inside a loop; every append reallocates.
		string_vars = set()
		for ln in range(start, end):
			m = RE_PY_STR_INIT.match(clean_lines[ln])
			if m:
				string_vars.add(m.group(1))
			if ln not in loop_lines:
				continue
			for name in string_vars:
				if re.search(r"\b" + re.escape(name) + r"\s*\+=", clean_lines[ln]) or re.search(r"\b" + re.escape(name) + r"\s*=\s*" + re.escape(name) + r"\s*\+", clean_lines[ln]):
					hit("STRING CONCAT LOOP", ln + 1, name + " concatenates inside a loop, collect the parts and join them")


def check_python_lines(clean_lines, raw_lines, hit):
	for idx, line in enumerate(clean_lines, 1):
		# Python needs no semicolon, so even one splits a line into two statements.
		depth = 0
		semis = 0
		for c in line:
			if c in "([{":
				depth += 1
			elif c in ")]}":
				depth -= 1
			elif (c == ";") and (depth == 0):
				semis += 1
		if semis >= 1:
			hit("MULTI-STATEMENT LINE", idx, "one statement per line, Python needs no semicolon")

		m = RE_PY_DEF_FULL.match(line)
		if m:
			name = m.group(1)
			if camel_violation(name):
				hit("PY NAMING", idx, name + " is snake_case, house style is lowerCamelCase")

			# Explicit types mean written-out annotations. __init__ is exempt from the return type, its None is not news to anyone.
			if not m.group(3) and (name != "__init__"):
				hit("MISSING TYPE HINT", idx, name + " has no return type, write it out")
			for param in split_params(m.group(2)):
				param = param.strip()
				if not param or param.startswith("*") or (param in ("self", "cls")):
					continue
				if ":" not in param.split("=")[0]:
					hit("MISSING TYPE HINT", idx, "parameter " + param.split("=")[0].strip() + " has no type, write it out")

		if indent_width(line) > 0:
			continue
		m = RE_PY_ASSIGN.match(line)
		if not m:
			continue
		name = m.group(1)
		if camel_violation(name):
			hit("PY NAMING", idx, name + " is snake_case, house style is lowerCamelCase")
		value = line.split("=", 1)[1].strip()
		if RE_PY_LITERAL.match(value) and not name.startswith("_") and (name.upper() != name):
			hit("CONSTANT CASE", idx, name + " is a module-level literal, name it UPPER_CASE")

	for idx, line in enumerate(raw_lines, 1):
		m = RE_PY_LOWER_COMMENT.match(line)
		if m and not ((idx > 1) and raw_lines[idx - 2].lstrip().startswith("#")):
			hit("LOWERCASE COMMENT", idx, "comments are complete sentences, start with a capital letter")
		comment_pos = line.find("# ")
		if (comment_pos >= 0) and RE_OXFORD.search(line[comment_pos:]):
			hit("OXFORD COMMA", idx, "no comma before the and/or closing a list")



def check_mixed_eol(raw_bytes, hit):
	crlf = raw_bytes.count(b"\r\n")
	bare = raw_bytes.count(b"\n") - crlf
	if crlf > 0 and bare > 0:
		minority = b"\n" if bare <= crlf else b"\r\n"
		idx = 1
		for chunk in raw_bytes.split(b"\n")[:-1]:
			is_crlf = chunk.endswith(b"\r")
			if (minority == b"\r\n") == is_crlf:
				break
			idx += 1
		hit("MIXED EOL", idx, "file mixes CRLF and LF line endings, match the file's dominant ending")


def check_markdown(raw_lines, hit):
	in_fence = False
	for idx, line in enumerate(raw_lines, 1):
		if line.strip().startswith("```"):
			in_fence = not in_fence
			continue
		if in_fence:
			continue
		prose = re.sub(r"`[^`]*`", "", line)
		if RE_OXFORD.search(prose):
			hit("OXFORD COMMA", idx, "no comma before the and/or closing a list")


def check_switches(clean_lines, raw_lines, clean_text, hit):
	for m in re.finditer(r"\bswitch\s*\(", clean_text):
		open_pos = clean_text.find("(", m.start())
		close_pos = match_paren(clean_text, open_pos)
		if close_pos < 0:
			continue
		brace_pos = clean_text.find("{", close_pos)
		if brace_pos < 0:
			continue
		depth = 0
		end_pos = -1
		for i in range(brace_pos, len(clean_text)):
			if clean_text[i] == "{":
				depth += 1
			elif clean_text[i] == "}":
				depth -= 1
				if depth == 0:
					end_pos = i
					break
		if end_pos < 0:
			continue
		switch_line = clean_text.count("\n", 0, m.start()) + 1
		body_first = clean_text.count("\n", 0, brace_pos) + 1
		body_last = clean_text.count("\n", 0, end_pos) + 1

		# Labels at the switch body's own depth; nested blocks are deeper and skipped.
		labels = []
		depth = 0
		for ln in range(body_first, body_last + 1):
			line = clean_lines[ln - 1]
			if depth == 1 and RE_LABEL.match(line):
				labels.append((ln, line.strip().startswith("default")))
			depth += line.count("{") - line.count("}")

		if not any(is_default for _, is_default in labels):
			hit("SWITCH DEFAULT", switch_line, "switch without a default block")
		case_count = sum(1 for _, is_default in labels if not is_default)
		if case_count < 3:
			hit("SWITCH TOO SMALL", switch_line, "fewer than 3 specific cases, use if/else")

		# Group consecutive labels, then judge each group's block shape and terminator.
		groups = []
		for ln, is_default in labels:
			if groups and ln - groups[-1][-1] <= 1:
				groups[-1].append(ln)
			else:
				groups.append([ln])
		for gi, group in enumerate(groups):
			nxt = next_code_line(clean_lines, group[-1])
			if nxt >= 0 and clean_lines[nxt].strip() != "{":
				hit("SWITCH CASE BRACES", group[0], "case block needs its own Allman braces")
			seg_end = groups[gi + 1][0] - 1 if gi + 1 < len(groups) else body_last - 1
			last_stmt = -1
			for ln in range(group[-1] + 1, seg_end + 1):
				stripped = clean_lines[ln - 1].strip()
				if stripped and stripped not in ("{", "}"):
					last_stmt = ln
			if last_stmt < 0:
				continue
			if RE_TERMINATOR.match(clean_lines[last_stmt - 1]):
				continue
			raw_segment = "\n".join(raw_lines[group[-1]:seg_end])
			if "Fallthrough" not in raw_segment:
				hit("SWITCH BREAK", group[0], "case block must end with break, return, throw or continue, or carry // Fallthrough.")


def check_missing_braces(clean_lines, hit):
	for idx, line in enumerate(clean_lines, 1):
		m = RE_CONTROL.match(line)
		if not m:
			continue
		keyword = m.group(2)
		if keyword in ("if", "for", "while", "else if"):
			open_pos = line.find("(", m.end())
			if open_pos < 0:
				continue
			close_pos = match_paren(line, open_pos)
			if close_pos < 0:
				continue
			rest = line[close_pos + 1:].strip()
			if keyword == "while" and rest == ";":
				continue
		else:
			rest = line[m.end():].strip()
			if keyword == "else" and (rest.startswith("if ") or rest.startswith("if(")):
				continue
		if rest == "":
			nxt = next_code_line(clean_lines, idx)
			if nxt >= 0 and not clean_lines[nxt].strip().startswith("{"):
				hit("MISSING BRACES", idx, keyword + " body needs its own braced block")
		elif rest != "{":
			hit("MISSING BRACES", idx, keyword + " body inline on the header line, give it a braced block")


def check_switch_candidates(clean_lines, hit):
	idx = 0
	total = len(clean_lines)
	while idx < total:
		line = clean_lines[idx]
		m = RE_CONST_COMPARE.match(line)
		if not m or re.match(r"^\s*(?:\}\s*)?else", line):
			idx += 1
			continue
		var = m.group(1)
		indent = len(line) - len(line.lstrip())
		start_line = idx + 1
		count = 0
		scan = idx
		valid = True
		while scan < total:
			cur = clean_lines[scan]
			cm = RE_CONST_COMPARE.match(cur)
			is_chain = scan == idx or re.match(r"^\s*(?:\}\s*)?else\s+if\b", cur)
			if not cm or not is_chain or (len(cur) - len(cur.lstrip())) != indent:
				break
			cond_open = cur.find("(", cur.find("if"))
			cond_close = match_paren(cur, cond_open)
			cond = cur[cond_open:cond_close + 1] if cond_close > 0 else cur
			if cm.group(1) != var or "&&" in cond or "!=" in cond or "<" in cond or ">" in cond:
				valid = False
				break
			branch_hits = len(RE_CONST_VALUE.findall(cond)) + cond.count(".equals")
			if branch_hits == 0 or re.search(r"\b" + re.escape(var) + r"\s*\.\s*(?!equals\b)\w+\s*\(", cond):
				valid = False
				break
			count += branch_hits
			nxt = scan + 1
			while nxt < total and not re.match(r"^\s*(?:\}\s*)?else\b", clean_lines[nxt]):
				stripped = clean_lines[nxt].strip()
				if stripped and not stripped.startswith(("{", "}")) and (len(clean_lines[nxt]) - len(clean_lines[nxt].lstrip())) <= indent:
					nxt = total
					break
				nxt += 1
			if nxt >= total or not re.match(r"^\s*(?:\}\s*)?else\s+if\b", clean_lines[nxt]):
				break
			scan = nxt
		if valid and count >= 3:
			hit("SWITCH CANDIDATE", start_line, "if/else-if chain compares " + var + " to " + str(count) + " constants, rewrite as a classic switch")
		idx += 1


def check_scoped_rules(clean_lines, depths, hit):
	# Scope = a maximal run of lines at brace depth 2 or deeper; coarse on inner classes.
	total = len(clean_lines)
	idx = 0
	while idx < total:
		if depths[idx] < 2:
			idx += 1
			continue
		start = idx
		while idx < total and depths[idx] >= 2:
			idx += 1
		end = idx  # Exclusive.

		# Repeated getters on the identical receiver. A branch boundary resets the counts: calls in mutually exclusive else/case arms are separate scopes, and hoisting a lookup above its discriminator is what the gate-the-lookup rule forbids. A loop header resets too: sequential loops reuse and redeclare the same short node names, so a textual repeat across headers is a different variable.
		seen = {}
		flagged = set()
		for ln in range(start, end):
			if re.match(r"^\s*(?:\}\s*)?(?:else\b|case\b|default\s*:)", clean_lines[ln]) or RE_LOOP_HEAD.match(clean_lines[ln]):
				seen = {}
			for m in RE_GETTER.finditer(clean_lines[ln]):
				receiver, call = m.group(1), m.group(2)
				if call in GETTER_EXCLUSIONS or receiver.endswith(")"):
					continue
				key = receiver + "." + call
				if key in flagged:
					continue
				if key in seen:
					if seen[key][0] != ln or seen[key][1] != m.start():
						hit("REPEATED GETTER", ln + 1, key + "() repeats in this scope, cache it in a final local")
						flagged.add(key)
				else:
					seen[key] = (ln, m.start())

		# Single-use locals folded only when the lone read sits on the very next statement.
		for ln in range(start, end):
			m = RE_LOCAL_DECL.match(clean_lines[ln])
			if not m or RE_LOOP_HEAD.match(clean_lines[ln]):
				continue
			name = m.group(1)
			reads = []
			for other in range(ln + 1, end):
				for x in re.finditer(r"\b" + re.escape(name) + r"\b", clean_lines[other]):
					reads.append(other)
			if len(reads) == 1 and reads[0] == next_code_line(clean_lines, ln + 1):
				hit("SINGLE-USE LOCAL", ln + 1, name + " is read once on the next line, fold it into the use site")

		# String concatenation inside a loop.
		string_vars = set()
		loop_stack = []
		depth = depths[start]
		for ln in range(start, end):
			line = clean_lines[ln]
			for m in RE_STRING_DECL.finditer(line):
				string_vars.add(m.group(1))
			if RE_LOOP_HEAD.match(line) and not line.rstrip().endswith(";"):
				loop_stack.append(depth)
			depth += line.count("{") - line.count("}")
			if line.count("}") > line.count("{"):
				while loop_stack and depth <= loop_stack[-1]:
					loop_stack.pop()
			if loop_stack:
				for name in string_vars:
					if re.search(r"\b" + re.escape(name) + r"\s*\+=", line) or re.search(r"\b" + re.escape(name) + r"\s*=\s*" + re.escape(name) + r"\s*\+", line):
						hit("STRING CONCAT LOOP", ln + 1, name + " concatenates inside a loop, use StringBuilder")


def check_line_rules(clean_lines, depths, raw_lines, is_java, hit):
	for idx, line in enumerate(clean_lines, 1):
		# Two or more statements on one line; semicolons inside parens (for headers) do not count.
		depth = 0
		semis = 0
		for c in line:
			if c == "(":
				depth += 1
			elif c == ")":
				depth -= 1
			elif c == ";" and depth == 0:
				semis += 1
		if semis >= 2:
			hit("MULTI-STATEMENT LINE", idx, "one statement per line")

		if RE_MULTI_DECL.match(line):
			hit("OBJECT MULTI-DECL", idx, "one variable per line")
		if RE_INTERFACE_I.search(line):
			hit("INTERFACE I PREFIX", idx, "interfaces are PascalCase without the I prefix")

		if is_java:
			if RE_FQN.search(line) and not re.match(r"^\s*(?:import|package)\b", line):
				hit("FQN INLINE", idx, "fully qualified name inline, add an import instead")
			m = RE_CONSTANT.match(line)
			if m and m.group(1) not in CONSTANT_EXCLUSIONS and not m.group(1).startswith("_"):
				hit("CONSTANT CASE", idx, m.group(1) + " is static final, name it UPPER_CASE")
			m = RE_FIELD.match(line)
			if m and depths[idx - 1] == 1 and "(" not in line and not m.group(1).startswith("_"):
				hit("FIELD UNDERSCORE", idx, m.group(1) + " is a private field, prefix it with an underscore")

	for idx, line in enumerate(raw_lines, 1):
		if is_java:
			m = RE_BARE_LINK.search(line)
			if m:
				hit("BARE LINK", idx, "{@link " + m.group(1) + "} needs the full package path")
			if RE_HASH_LINK.search(line):
				hit("BARE LINK", idx, "the {@link #member} form is forbidden, use {@code ...}")
		m = RE_LOWER_COMMENT.match(line)
		if m and not ((idx > 1) and raw_lines[idx - 2].lstrip().startswith("//")):
			hit("LOWERCASE COMMENT", idx, "comments are complete sentences, start with a capital letter")
		comment_pos = line.find("//")
		if comment_pos >= 0 and "://" not in line:
			if RE_OXFORD.search(line[comment_pos:]):
				hit("OXFORD COMMA", idx, "no comma before the and/or closing a list")


def formatter_off_lines(raw_lines):
	"""Line numbers inside // @formatter:off .. // @formatter:on regions, markers included.

	Those regions are laid out by hand on purpose, so the line-shape rules do not apply to them.
	"""
	off = set()
	active = False
	for idx, line in enumerate(raw_lines, 1):
		stripped = line.strip()
		if stripped.startswith(("//", "#")) and "@formatter:off" in stripped:
			active = True
			off.add(idx)
			continue

		if stripped.startswith(("//", "#")) and "@formatter:on" in stripped:
			active = False
			off.add(idx)
			continue

		if active:
			off.add(idx)

	return off


def check_file(path, raw_bytes):
	findings = []
	suppressed = set()

	def hit(rule, idx, msg):
		if idx in suppressed:
			return

		findings.append((rule, idx, msg))

	check_mixed_eol(raw_bytes, hit)

	text = raw_bytes.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
	raw_lines = text.split("\n")
	suppressed.update(formatter_off_lines(raw_lines))

	if path.endswith(".md"):
		check_markdown(raw_lines, hit)
		return findings
	if path.endswith(PY_EXTS):
		clean_lines = strip_python_comments_and_strings(text).split("\n")
		check_python_scopes(clean_lines, hit)
		check_python_lines(clean_lines, raw_lines, hit)
		return findings
	if not path.endswith(CODE_EXTS):
		return findings

	is_java = path.endswith(".java")
	clean_text = strip_comments_and_strings(text)
	clean_lines = clean_text.split("\n")
	depths = line_depths(clean_lines)

	check_switches(clean_lines, raw_lines, clean_text, hit)
	check_missing_braces(clean_lines, hit)
	if is_java:
		check_switch_candidates(clean_lines, hit)
		check_scoped_rules(clean_lines, depths, hit)
	check_line_rules(clean_lines, depths, raw_lines, is_java, hit)
	return findings


def report(path, findings):
	shown = {}
	total = {}
	for rule, idx, msg in sorted(findings, key=lambda f: (f[0], f[1])):
		total[rule] = total.get(rule, 0) + 1
		if total[rule] <= MAX_PER_RULE:
			shown.setdefault(rule, []).append(path + ":" + str(idx) + ": " + rule + ": " + msg)
	for rule in shown:
		for line in shown[rule]:
			print(line)
		if total[rule] > MAX_PER_RULE:
			print(path + ": " + rule + ": " + str(total[rule] - MAX_PER_RULE) + " more hit(s), fix all occurrences")


SELFTEST_JAVA = """\
public class T
{
\tprivate int count;
\tprivate final java.util.List<String> names = null;
\tstatic final int maxRetries = 3;
\tString s1, s2;

\t/**
\t * Doc with {@link Bad} and {@link #member} forms.<br>
\t */
\tvoid run(Order order, int code)
\t{
\t\tif (ready) fire();
\t\tif (ready)
\t\t\tfire();
\t\tint i = 0; i++;
\t\t// lowercase fragment comment
\t\t// Retry once, twice, and thrice.
\t\tif ((order.getStatus() == PAID) && (order.getStatus() != REFUNDED))
\t\t{
\t\t\tuse(order);
\t\t}
\t\tfinal double rounded = Math.round(1.5);
\t\tuse(rounded);
\t\tString result = "";
\t\tfor (Order o : orders)
\t\t{
\t\t\tresult += o.getId() + ",";
\t\t}
\t\tif (code == 1)
\t\t{
\t\t\tuse(1);
\t\t}
\t\telse if (code == 2)
\t\t{
\t\t\tuse(2);
\t\t}
\t\telse if (code == 3)
\t\t{
\t\t\tuse(3);
\t\t}
\t\tswitch (kind)
\t\t{
\t\t\tcase A:
\t\t\t\tdoA();
\t\t\t\tbreak;
\t\t\tcase B:
\t\t\t{
\t\t\t\tdoB();
\t\t\t}
\t\t}
\t}

\tvoid handLaidOut()
\t{
\t\t// @formatter:off
\t\tregister(a,
\t\t\t() -> { first(); second(); },
\t\t\t() -> { third(); fourth(); });
\t\t// @formatter:on
\t}
}

interface IThing
{
}
"""

SELFTEST_CLEAN_JAVA = """\
public class Clean
{
\tprivate final int _count;
\tprivate static final int MAX_RETRIES = 3;

\tpublic int label(int code)
\t{
\t\tfinal OrderStatus orderStatus = order.getStatus();
\t\tif ((orderStatus == PAID) && (orderStatus != REFUNDED))
\t\t{
\t\t\tuse(orderStatus);
\t\t}
\t\tfinal StringBuilder result = new StringBuilder();
\t\tfor (int i = 0; i < 3; i++)
\t\t{
\t\t\tresult.append(i).append(',');
\t\t}
\t\tfor (Node a = d.getFirstChild(); a != null; a = a.getNextSibling())
\t\t{
\t\t\tuse(a);
\t\t}
\t\tfor (Node a = d.getFirstChild(); a != null; a = a.getNextSibling())
\t\t{
\t\t\tuse(a);
\t\t}
\t\tif (code == 9)
\t\t{
\t\t\tuse(order.getAttributes());
\t\t}
\t\telse
\t\t{
\t\t\tuse(order.getAttributes());
\t\t}
\t\tswitch (code)
\t\t{
\t\t\tcase 1:
\t\t\t{
\t\t\t\treturn 1;
\t\t\t}
\t\t\tcase 2:
\t\t\t{
\t\t\t\treturn 2;
\t\t\t}
\t\t\tcase 3:
\t\t\t{
\t\t\t\t// Fallthrough.
\t\t\t}
\t\t\tdefault:
\t\t\t{
\t\t\t\treturn 0;
\t\t\t}
\t\t}
\t}
}
"""

SELFTEST_MD = """\
# Doc

This lists one, two, and three items.

```java
// code fence with one, two, and three stays exempt
```

The `one, two, and three` span stays exempt too.
"""


SELFTEST_PY = """\
maxRetries = 3

def run(order: Order, code: int) -> None:
\t# lowercase fragment comment
\t# Retry once, twice, and thrice.
\tstatus = order.getStatus()
\tuse(status)
\ttotal = ""
\tfor item in items:
\t\ttotal += item
\tvalue = 1; other = 2
\tuse(order.name())
\tuse(order.name())

def send_now(x) -> None:
\tuse(x)
"""

SELFTEST_CLEAN_PY = """\
MAX_RETRIES = 3

def label(order: Order, code: int) -> int:
\torderStatus = order.getStatus()
\tif orderStatus == PAID:
\t\tuse(orderStatus)
\tparts: list = []
\tfor item in items:
\t\tparts.append(item)
\treturn code
"""

def selftest():
	findings = check_file("selftest.java", SELFTEST_JAVA.encode("utf-8"))
	rules = [f[0] for f in findings]
	expected = {
		"FIELD UNDERSCORE": 2,
		"CONSTANT CASE": 1,
		"OBJECT MULTI-DECL": 1,
		"FQN INLINE": 1,
		"BARE LINK": 2,
		"MISSING BRACES": 2,
		"MULTI-STATEMENT LINE": 1,
		"LOWERCASE COMMENT": 1,
		"OXFORD COMMA": 1,
		"REPEATED GETTER": 1,
		"SINGLE-USE LOCAL": 1,
		"STRING CONCAT LOOP": 1,
		"SWITCH CANDIDATE": 1,
		"SWITCH DEFAULT": 1,
		"SWITCH TOO SMALL": 1,
		"SWITCH CASE BRACES": 1,
		"SWITCH BREAK": 1,
		"INTERFACE I PREFIX": 1,
	}
	for rule, want in expected.items():
		got = rules.count(rule)
		assert got == want, rule + ": expected " + str(want) + " got " + str(got) + " " + str([f for f in findings if f[0] == rule])
	unexpected = [f for f in findings if f[0] not in expected]
	assert not unexpected, "unexpected findings: " + str(unexpected)

	clean = check_file("clean.java", SELFTEST_CLEAN_JAVA.encode("utf-8"))
	assert not clean, "clean fixture flagged: " + str(clean)

	md = check_file("selftest.md", SELFTEST_MD.encode("utf-8"))
	assert [f[0] for f in md] == ["OXFORD COMMA"], "markdown fixture wrong: " + str(md)
	assert md[0][1] == 3, "OXFORD COMMA expected on line 3, got " + str(md[0][1])

	py = check_file("selftest.py", SELFTEST_PY.encode("utf-8"))
	py_rules = [f[0] for f in py]
	py_expected = {
		"CONSTANT CASE": 1,
		"LOWERCASE COMMENT": 1,
		"OXFORD COMMA": 1,
		"SINGLE-USE LOCAL": 1,
		"STRING CONCAT LOOP": 1,
		"MULTI-STATEMENT LINE": 1,
		"REPEATED CALL": 1,
		"MISSING TYPE HINT": 1,
		"PY NAMING": 1,
	}
	for rule, want in py_expected.items():
		got = py_rules.count(rule)
		assert got == want, "python " + rule + ": expected " + str(want) + " got " + str(got) + " " + str([f for f in py if f[0] == rule])
	py_unexpected = [f for f in py if f[0] not in py_expected]
	assert not py_unexpected, "unexpected python findings: " + str(py_unexpected)

	clean_py = check_file("clean.py", SELFTEST_CLEAN_PY.encode("utf-8"))
	assert not clean_py, "clean python fixture flagged: " + str(clean_py)

	mixed = check_file("mixed.java", b"class A\r\n{\r\n}\n")
	assert any(f[0] == "MIXED EOL" for f in mixed), "MIXED EOL did not fire"

	print("selftest OK, " + str(len(findings)) + " findings as expected")


def main():
	args = sys.argv[1:]
	if not args:
		print("usage: bofad-lint.py <file> [...] | --selftest")
		return 2
	if args == ["--selftest"]:
		selftest()
		return 0
	exit_code = 0
	for path in args:
		try:
			with open(path, "rb") as f:
				raw_bytes = f.read()
		except OSError as e:
			print(path + ": unreadable: " + str(e))
			exit_code = 2
			continue
		findings = check_file(path, raw_bytes)
		if findings:
			exit_code = 1
			report(path, findings)
	return exit_code


if __name__ == "__main__":
	sys.exit(main())
