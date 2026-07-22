#!/usr/bin/env python3
# Mechanical Java autoboxing checker, BOFAD companion to bofad-check.sh.
# Type-blind: tracks wrapper/primitive declarations per file by regex, so shadowing
# and cross-file types are invisible. For type-resolved analysis use PMD or Error Prone.
# Usage: python bofad-boxing.py <file.java> [more.java ...] | python bofad-boxing.py --selftest
# Output: file:line: RULE: message   (first 3 hits per rule, fix all occurrences)
# Exit 1 when findings exist, 0 clean.

import re
import sys

WRAPPERS = r"(?:Integer|Long|Double|Float|Short|Byte|Character|Boolean)"
PRIMITIVES = r"(?:int|long|double|float|short|byte|char|boolean)"

MAX_PER_RULE = 3


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


def check_file(path, src):
	findings = []
	clean = strip_comments_and_strings(src)
	lines = clean.split("\n")

	wrapper_vars = {}    # name -> decl line
	primitive_vars = {}  # name -> decl line
	wrapper_colls = {}   # name -> decl line, collection with wrapper value type

	decl_wrapper = re.compile(r"(?<![\w<,.])(" + WRAPPERS + r")\s+([a-z_]\w*)\s*[=;)]")
	decl_primitive = re.compile(r"(?<![\w<,.])(" + PRIMITIVES + r")\s+([a-z_]\w*)\s*[=;)]")
	decl_coll = re.compile(r"\b(?:Map|HashMap|TreeMap|List|ArrayList|Set|HashSet|Queue|Deque)\s*<[^<>]*\b" + WRAPPERS + r"\s*>\s+([A-Za-z_]\w*)")

	for idx, line in enumerate(lines, 1):
		for m in decl_coll.finditer(line):
			wrapper_colls[m.group(1)] = idx
		for m in decl_wrapper.finditer(line):
			wrapper_vars[m.group(2)] = idx
		for m in decl_primitive.finditer(line):
			primitive_vars[m.group(2)] = idx

	def hit(rule, idx, msg):
		findings.append((rule, idx, msg))

	re_ctor = re.compile(r"\bnew\s+(" + WRAPPERS + r")\s*\(")
	re_boxed_for = re.compile(r"\bfor\s*\(\s*(" + WRAPPERS + r")\s+(\w+)\s*=")
	re_roundtrip = re.compile(r"(?:\bnew\s+" + WRAPPERS + r"\s*\([^()]*\)|\b" + WRAPPERS + r"\s*\.\s*valueOf\s*\([^()]*\))\s*\.\s*" + PRIMITIVES + r"Value\s*\(")
	re_compare = re.compile(r"\b(\w+)\s*[=!]=\s*(\w+)\b")
	re_incdec = re.compile(r"\b(\w+)\s*(\+\+|--)|(\+\+|--)\s*(\w+)\b")
	re_opassign = re.compile(r"\b(\w+)\s*[-+*/%]=")
	re_selfarith = re.compile(r"\b(\w+)\s*=\s*\1\s*[-+*/%]")
	re_unbox_get = re.compile(r"\b" + PRIMITIVES + r"\s+\w+\s*=\s*(\w+)\s*\.\s*get\s*\(")
	re_put_prim = re.compile(r"\b(\w+)\s*\.\s*put\s*\([^,()]+,\s*(\w+)\s*\)")
	re_add_prim = re.compile(r"\b(\w+)\s*\.\s*add\s*\(\s*(\w+)\s*\)")
	re_foreach_unbox = re.compile(r"\bfor\s*\(\s*" + PRIMITIVES + r"\s+\w+\s*:\s*(\w+)\s*\)")

	for idx, line in enumerate(lines, 1):
		for m in re_ctor.finditer(line):
			hit("WRAPPER CTOR", idx, "new " + m.group(1) + "(...) is deprecated boxing, use the literal or valueOf")
		for m in re_boxed_for.finditer(line):
			hit("BOXED LOOP INDEX", idx, m.group(1) + " " + m.group(2) + " as loop counter boxes every iteration, use the primitive")
		for m in re_roundtrip.finditer(line):
			hit("BOX ROUNDTRIP", idx, "box then immediate xxxValue() on one line, drop both")
		for m in re_compare.finditer(line):
			a, b = m.group(1), m.group(2)
			if a in wrapper_vars and b in wrapper_vars:
				hit("WRAPPER IDENTITY ==", idx, a + " == " + b + " compares references, equals() or unbox one side")
		boxed_loop_header = re_boxed_for.search(line) is not None
		for m in re_incdec.finditer(line):
			name = m.group(1) or m.group(4)
			if name in wrapper_vars and not boxed_loop_header:
				hit("WRAPPER ARITHMETIC", idx, name + " is a wrapper, ++/-- unboxes and reboxes, declare it primitive")
		for m in re_opassign.finditer(line):
			if m.group(1) in wrapper_vars:
				hit("WRAPPER ARITHMETIC", idx, m.group(1) + " is a wrapper, compound assignment unboxes and reboxes, declare it primitive")
		for m in re_selfarith.finditer(line):
			if m.group(1) in wrapper_vars:
				hit("WRAPPER ARITHMETIC", idx, m.group(1) + " is a wrapper, self arithmetic unboxes and reboxes, declare it primitive")
		for m in re_unbox_get.finditer(line):
			if m.group(1) in wrapper_colls:
				hit("BOUNDARY UNBOX", idx, "primitive local from " + m.group(1) + ".get(...), keep the wrapper when the value goes back in boxed")
		for m in re_put_prim.finditer(line):
			if m.group(1) in wrapper_colls and m.group(2) in primitive_vars:
				hit("BOUNDARY BOX", idx, m.group(2) + " boxes into " + m.group(1) + ".put(...), keep it boxed across the round trip")
		for m in re_add_prim.finditer(line):
			if m.group(1) in wrapper_colls and m.group(2) in primitive_vars:
				hit("BOUNDARY BOX", idx, m.group(2) + " boxes into " + m.group(1) + ".add(...), keep it boxed across the round trip")
		for m in re_foreach_unbox.finditer(line):
			if m.group(1) in wrapper_colls:
				hit("FOREACH UNBOX", idx, "foreach unboxes every element of " + m.group(1) + ", iterate the wrapper type")

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


SELFTEST_SRC = """
class T
{
	private static final java.util.Map<String, Integer> MAP = new java.util.HashMap<>();
	void run(java.util.List<Integer> nums)
	{
		Integer a = 1;
		Integer b = 2;
		Integer count = 0;
		Integer x = new Integer(5);                      // WRAPPER CTOR
		int y = new Integer(7).intValue();               // WRAPPER CTOR + BOX ROUNDTRIP
		long z = Long.valueOf(9).longValue();            // BOX ROUNDTRIP
		if (a == b) { }                                  // WRAPPER IDENTITY ==
		count++;                                         // WRAPPER ARITHMETIC
		count += 2;                                      // WRAPPER ARITHMETIC
		count = count + 1;                               // WRAPPER ARITHMETIC
		for (Integer i = 0; i < 10; i++) { }             // BOXED LOOP INDEX
		int v = MAP.get("k");                            // BOUNDARY UNBOX
		MAP.put("k", v);                                 // BOUNDARY BOX
		for (int n : nums) { }                           // FOREACH UNBOX
		// Integer fake = 0; comment only, and "Integer s = 0" in a string below
		String s = "Integer inString = 0";
		int fine = 3;
		fine++;
	}
}
"""


def selftest():
	findings = check_file("selftest.java", SELFTEST_SRC)
	rules = [f[0] for f in findings]
	expected = {
		"WRAPPER CTOR": 2,
		"BOX ROUNDTRIP": 2,
		"WRAPPER IDENTITY ==": 1,
		"WRAPPER ARITHMETIC": 3,
		"BOXED LOOP INDEX": 1,
		"BOUNDARY UNBOX": 1,
		"BOUNDARY BOX": 1,
		"FOREACH UNBOX": 1,
	}
	for rule, want in expected.items():
		got = rules.count(rule)
		assert got == want, rule + ": expected " + str(want) + " got " + str(got)
	assert not any("fake" in f[2] or "inString" in f[2] or "fine" in f[2] for f in findings), "comment/string/primitive leaked into findings"
	print("selftest OK, " + str(len(findings)) + " findings as expected")


def main():
	args = sys.argv[1:]
	if not args:
		print("usage: bofad-boxing.py <file.java> [...] | --selftest")
		return 2
	if args == ["--selftest"]:
		selftest()
		return 0
	exit_code = 0
	for path in args:
		try:
			with open(path, "r", encoding="utf-8", errors="replace") as f:
				src = f.read()
		except OSError as e:
			print(path + ": unreadable: " + str(e))
			exit_code = 2
			continue
		findings = check_file(path, src)
		if findings:
			exit_code = 1
			report(path, findings)
	return exit_code


if __name__ == "__main__":
	sys.exit(main())
