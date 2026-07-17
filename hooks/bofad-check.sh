#!/bin/sh
# BOFAD mechanical style check.
# Hook mode (no arguments): reads Claude Code PostToolUse JSON from stdin, scopes findings to lines changed since the last commit, reports on stderr and exits 2 so the model self-corrects.
# Standalone mode (file arguments): checks each whole file, reports on stdout and exits 1 on findings; used by the pre-commit wrapper, CI or manually.
# Code checks run on brace languages where every rule below is safe; prose checks run on markdown. Warn-only in hook mode, the edit itself is never blocked.

# Line numbers to report on, space-separated; empty means the whole file. Set in hook mode from git diff; standalone callers preset it via BOFAD_CHANGED (the pre-commit wrapper does).
CHANGED="${BOFAD_CHANGED:-}"

# Keeps only hits whose leading line number is in CHANGED; passes everything through when CHANGED is empty.
filter_hits()
{
	if [ -z "$CHANGED" ]
	then
		cat
		return
	fi
	awk -F : -v lines="$CHANGED" 'BEGIN { n = split(lines, a, " "); for (i = 1; i <= n; i++) set[a[i]] = 1 } ($1 in set)'
}

check_code()
{
	f="$1"
	out=""

	# Spaces used for indentation, tabs required; doc comment continuation lines starting with " *" are exempt.
	hits=$(grep -nE '^ +[^ *]' "$f" | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
SPACE INDENT (tabs required):
$hits"
	fi

	# Opening brace left at end of a code line, Allman requires it alone on its own line.
	hits=$(grep -nE '[^[:space:]][[:space:]]*\{[[:space:]]*$' "$f" | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
K&R BRACE (Allman required, opening brace on its own line):
$hits"
	fi

	# Missing space after comment marker.
	hits=$(grep -nE '//[^ /!-]' "$f" | grep -vE '://' | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
COMMENT SPACING (space required after //):
$hits"
	fi

	# Local type inference forbidden.
	hits=$(grep -nE '(^|[^A-Za-z0-9_.])var[[:space:]]+[A-Za-z_]' "$f" | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
TYPE INFERENCE (explicit type required, no var):
$hits"
	fi

	# Functional collection chains forbidden.
	hits=$(grep -nE '\.stream\(\)|\.forEach\(|\.Select\(|\.Where\(' "$f" | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
FUNCTIONAL CHAIN (traditional loops required):
$hits"
	fi

	# Switch expression arrow syntax forbidden; a classic case label carries a colon before any arrow can appear.
	hits=$(grep -nE '^[[:space:]]*(case[^:]*|default[[:space:]]*)->' "$f" | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
SWITCH ARROW (classic switch with break and default required):
$hits"
	fi

	# Nullability annotations forbidden, explicit null checks required.
	hits=$(grep -nE '@(Nullable|NonNull|Nonnull|NotNull)' "$f" | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
NULLABILITY ANNOTATION (explicit null checks required):
$hits"
	fi

	# One variable per line; a leading primitive type followed by a comma-separated identifier list is a multi-declaration.
	hits=$(grep -nE '^[[:space:]]*(final[[:space:]]+)?(int|long|short|byte|float|double|char|boolean)[[:space:]]+[A-Za-z_][A-Za-z0-9_]*[[:space:]]*,[[:space:]]*[A-Za-z_]' "$f" | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
MULTI-DECLARATION (one variable per line):
$hits"
	fi

	common_checks "$f"
}

check_prose()
{
	f="$1"
	out=""

	# Oxford comma check skipped - clause commas make a grep heuristic block-happy; add one if drift returns.
	common_checks "$f"
}

# Checks shared by code and prose; appends to out, then prints the whole report.
common_checks()
{
	f="$1"

	# Em and en dashes forbidden in prose and code comments alike.
	hits=$(grep -n '—\|–' "$f" | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
EM/EN DASH (use a comma or a simple hyphen):
$hits"
	fi

	# More than one consecutive blank line.
	hits=$(awk 'prev ~ /^[ \t]*\r?$/ && $0 ~ /^[ \t]*\r?$/ { print NR } { prev = $0 }' "$f" | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
CONSECUTIVE BLANK LINES (max one) at line(s): $(printf '%s' "$hits" | tr '\n' ' ')"
	fi

	# Trailing whitespace; awk interprets backslash escapes in regex where grep bracket expressions treat them as literals.
	hits=$(awk '/[ \t]+\r?$/ { print NR }' "$f" | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
TRAILING WHITESPACE at line(s): $(printf '%s' "$hits" | tr '\n' ' ')"
	fi

	if [ -n "$out" ]
	then
		if [ -n "$CHANGED" ]
		then
			printf 'BOFAD check on %s (limited to uncommitted lines):%s\n' "$f" "$out"
		else
			printf 'BOFAD check on %s (first 3 hits per rule, fix all occurrences):%s\n' "$f" "$out"
		fi
		return 1
	fi
	return 0
}

check_file()
{
	f="$1"
	[ -f "$f" ] || return 0
	case "$f" in
		*.java|*.cs|*.c|*.cpp|*.h|*.hpp) check_code "$f" ;;
		*.md) check_prose "$f" ;;
		*) return 0 ;;
	esac
}

if [ $# -gt 0 ]
then
	# Standalone mode.
	fail=0
	for arg in "$@"
	do
		check_file "$arg" || fail=1
	done
	exit $fail
fi

# Hook mode.
input=$(cat)
file=$(printf '%s' "$input" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1 | sed 's/\\\\/\\/g')
[ -n "$file" ] || exit 0

# Scope findings to uncommitted lines so a legacy file does not trigger mass-reformat instructions; empty set means untracked file or no repo, check the whole file.
CHANGED=$(git -C "$(dirname "$file")" diff -U0 HEAD -- "$file" 2>/dev/null | awk '/^@@/ { split($3, a, ","); start = substr(a[1], 2) + 0; count = 1; if (a[2] != "") count = a[2] + 0; for (i = 0; i < count; i++) print start + i }' | tr '\n' ' ')

report=$(check_file "$file")
if [ -n "$report" ]
then
	printf '%s\n' "$report" >&2
	exit 2
fi
exit 0
