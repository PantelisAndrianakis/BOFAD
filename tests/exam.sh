#!/bin/sh
# BOFAD successor exam. Runs the host model headlessly against the shipped fixtures and answers one question: does the model carrying these rules still enforce them? Three parts: detection on SemanticBad.java, restraint on SemanticGood.java, voice register on probe 01. Grep and the final-check hook grade every part, no model grades a model.
# The runner is any command that reads a prompt on stdin and prints the reply on stdout, set via BOFAD_ASK. Prompts ride stdin because a 40KB argument dies on the Windows argument-size limit. CI never runs this; a person runs it once after every host swap.
# Usage: BOFAD_ASK="mycli --flags" sh tests/exam.sh   (any working directory)

set -u
cd "$(dirname "$0")/.." || exit 1

ask="${BOFAD_ASK:-}"
[ -n "$ask" ] || { echo "set BOFAD_ASK to a command that reads a prompt on stdin and prints the reply on stdout"; exit 1; }
command -v "${ask%% *}" >/dev/null 2>&1 || { echo "runner not found: ${ask%% *}"; exit 1; }

fail=0
agent_body=$(awk '/^---$/{f++; next} f>=2' agents/bofad-code-check.md)

grade_code()
{
	{ printf '%s\n\nReview this Java code given inline:\n\n```java\n' "$agent_body"; sed "1,${1}d" "tests/samples/$2"; printf '```\n'; } | $ask 2>/dev/null
}

# Part 1: detection. The answer-key comment on lines 1-2 is stripped before the model sees the code. Four violations are planted; three findings pass, so one miss is tolerated and real degradation is not.
out=$(grade_code 2 SemanticBad.java)
count=$(printf '%s' "$out" | sed -n 's/^FINDINGS: *\([0-9][0-9]*\).*/\1/p' | head -n 1)
if [ -n "$count" ] && [ "$count" -ge 3 ]
then
	echo "PASS detection - $count findings on SemanticBad.java"
else
	echo "FAIL detection - expected 3+ findings on SemanticBad.java, got ${count:-no FINDINGS line}"
	printf '%s\n\n' "$out"
	fail=1
fi

# Part 2: restraint. The clean twin, expectation comment stripped; anything but a clean verdict is an invented finding.
out=$(grade_code 1 SemanticGood.java)
if printf '%s' "$out" | grep -q '^FINDINGS: *0' && printf '%s' "$out" | grep -qi '^VERDICT:.*clean'
then
	echo "PASS restraint - clean verdict on SemanticGood.java"
else
	echo "FAIL restraint - expected FINDINGS: 0 and a clean verdict on SemanticGood.java"
	printf '%s\n\n' "$out"
	fail=1
fi

# Part 3: voice. Probe 01 answered under the full ruleset, reply scanned for the measured drift tells plus section headers, which a short factual answer never gets.
reply=$({ printf 'The rules below govern your reply.\n\n'; cat skills/bofad/SKILL.md; printf '\nwhat does the `volatile` keyword actually guarantee in Java?\n'; } | $ask 2>/dev/null)
tmp="${TMPDIR:-/tmp}/bofad-exam-reply.$$"
printf '%s\n' "$reply" > "$tmp"
scan=$(sh hooks/bofad-final-check.sh "$tmp"); scanned=$?
rm -f "$tmp"
if [ -n "$reply" ] && [ "$scanned" -eq 0 ] && ! printf '%s' "$reply" | grep -q '^#'
then
	echo "PASS voice - probe 01 reply carries no drift tells"
else
	echo "FAIL voice - probe 01 reply tripped the final check or grew headers"
	printf '%s\n%s\n\n' "$scan" "$reply"
	fail=1
fi

[ "$fail" -eq 0 ] && echo "EXAM PASS" || echo "EXAM FAIL"
exit "$fail"
