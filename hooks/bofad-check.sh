#!/bin/sh
# BOFAD mechanical style check.
# Hook mode (no arguments): reads Claude Code PostToolUse JSON from stdin, scopes findings to lines changed since the last commit, reports on stderr and exits 2 so the model self-corrects.
# Standalone mode (file arguments): checks each whole file, reports on stdout and exits 1 on findings; used by the pre-commit wrapper, CI or manually.
# Code checks run on brace languages where every rule below is safe, Python takes the subset that survives the translation; prose checks run on markdown. Warn-only in hook mode, the edit itself is never blocked.

# Line numbers to report on, space-separated; empty means the whole file. Set in hook mode from git diff; standalone callers preset it via BOFAD_CHANGED (the pre-commit wrapper does).
CHANGED="${BOFAD_CHANGED:-}"

# Python interpreter for the companion scripts; modern Linux ships python3 only, Windows ships python. Empty means every Python check silently skips, which keeps the bare copy-install working.
PYBIN=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)

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

	# Missing space after comment marker; URL schemes are masked first so an address on the line no longer exempts the whole line.
	hits=$(grep -n '.' "$f" | sed 's|[A-Za-z][A-Za-z0-9+.-]*://|__SCHEME__|g' | grep -E '//[^ /!-]' | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
COMMENT SPACING (space required after //):
$hits"
	fi

	# Comment wrapped at a column instead of at punctuation; a line comment continued by another line comment ends at ; - , . or : so the break lands on a clause boundary.
	# Commented-out code is exempt, it ends on whatever the code ended on.
	hits=$(awk '
		{ lines[NR] = $0 }
		END {
			for (i = 1; i < NR; i++)
			{
				cur = lines[i]
				nxt = lines[i + 1]
				if (cur !~ /^[ \t]*\/\/ / || nxt !~ /^[ \t]*\/\/ /) { continue }
				if (cur ~ /[;,.:_-][ \t]*$/ || cur ~ /[{}()][ \t]*$/) { continue }
				if (cur ~ /@formatter:(on|off)/ || nxt ~ /@formatter:(on|off)/) { continue }
				print i ":" cur
			}
		}' "$f" | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
COMMENT WRAP (break at punctuation, the continuation is a plain // line):
$hits"
	fi

	# Local type inference forbidden, var and C++ auto alike; line comments and doc continuation lines are stripped first so prose mentioning the keywords stays legal, string literals still flag - accepted ceiling.
	hits=$(grep -n '.' "$f" | sed 's|//.*||' | grep -vE '^[0-9]+:[[:space:]]*(\*|/\*)' | grep -E '(^|[^A-Za-z0-9_.])(var|auto)[[:space:]]+[A-Za-z_]' | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
TYPE INFERENCE (explicit type required, no var or auto):
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

	# Blank-line layout drift against the bundled bofad-format.py; runs the formatter to a temp file and reports diff hunks. Standalone mode only, a whole-file diff has no meaning inside hook mode's changed-line scope. Config.java is excluded to match the formatter's own exclusion.
	fmt="$(dirname "$0")/bofad-format.py"
	case "$f" in
		*Config.java) fmt="" ;;
	esac
	if [ -z "$CHANGED" ] && [ -n "$fmt" ] && [ -f "$fmt" ] && [ -n "$PYBIN" ]
	then
		tmp=$(mktemp)
		if "$PYBIN" -c "import sys, importlib.util; spec = importlib.util.spec_from_file_location('fmt', sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.process_java_file(sys.argv[2], sys.argv[3])" "$fmt" "$f" "$tmp" 2>/dev/null
		then
			hits=$(diff "$f" "$tmp" | grep -E '^[0-9]' | head -n 3)
			if [ -n "$hits" ]
			then
				out="$out
FORMATTER DRIFT (blank-line layout, run hooks/bofad-format.py on this file):
$hits"
			fi
		fi
		rm -f "$tmp"
	fi

	# Java autoboxing patterns via the bundled bofad-boxing.py; output is path:line: RULE: msg, the leading path is stripped so filter_hits can line-scope it in hook mode. Java only, the wrapper rules mean nothing to the other brace languages. Missing script or python degrades to a silent skip, which keeps the bare pre-commit copy-install working.
	box="$(dirname "$0")/bofad-boxing.py"
	case "$f" in
		*.java) ;;
		*) box="" ;;
	esac
	if [ -n "$box" ] && [ -f "$box" ] && [ -n "$PYBIN" ]
	then
		hits=$("$PYBIN" "$box" "$f" 2>/dev/null | awk -v n="${#f}" '{ print substr($0, n + 2) }' | filter_hits | head -n 12)
		if [ -n "$hits" ]
		then
			out="$out
BOXING (unnecessary box/unbox, see bofad-boxing.py rules):
$hits"
		fi
	fi

	lint_checks "$f"
	common_checks "$f"
}

check_python()
{
	f="$1"
	out=""

	# Spaces used for indentation, tabs required; house style outranks PEP 8 here.
	hits=$(grep -nE '^ +[^ ]' "$f" | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
SPACE INDENT (tabs required):
$hits"
	fi

	# Missing space after the comment marker. The shebang and repeated-hash dividers are exempt, URL schemes are masked first, and a hash inside a string literal still flags - accepted ceiling.
	hits=$(sed 's|[A-Za-z][A-Za-z0-9+.-]*://|__SCHEME__|g' "$f" | grep -nE '(^|[[:space:]])#[^ #!]' | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
COMMENT SPACING (space required after #):
$hits"
	fi

	# Comment wrapped at a column instead of at punctuation; a line comment continued by another line comment ends at ; - , . or : so the break lands on a clause boundary.
	hits=$(awk '
		{ lines[NR] = $0 }
		END {
			for (i = 1; i < NR; i++)
			{
				cur = lines[i]
				nxt = lines[i + 1]
				if (cur !~ /^[ \t]*# / || nxt !~ /^[ \t]*# /) { continue }
				if (cur ~ /[;,.:_-][ \t]*$/ || cur ~ /[{}()][ \t]*$/) { continue }
				print i ":" cur
			}
		}' "$f" | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
COMMENT WRAP (break at punctuation, the continuation is a plain # line):
$hits"
	fi

	# Functional collection chains forbidden; a plain loop or one flat comprehension does the job.
	hits=$(grep -nE '(^|[^A-Za-z0-9_])(map|filter|reduce)\(|\.apply\(' "$f" | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
FUNCTIONAL CHAIN (traditional loops required):
$hits"
	fi

	# One variable per line; chained assignment and tuple targets both bind more than one name.
	hits=$(grep -nE '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*(,[[:space:]]*[A-Za-z_][A-Za-z0-9_]*)+[[:space:]]*=[^=]|^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*=[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*=[^=]' "$f" | filter_hits | head -n 3)
	if [ -n "$hits" ]
	then
		out="$out
MULTI-DECLARATION (one variable per line):
$hits"
	fi

	lint_checks "$f"
	common_checks "$f"
}

# Structural rules via the bundled bofad-lint.py: switch shape, missing braces, repeated getters, single-use locals, string concatenation in loops, naming, Oxford comma. Same output contract as the boxing script, so the same strip and filter applies; missing script or python degrades to a silent skip.
lint_checks()
{
	f="$1"
	lint="$(dirname "$0")/bofad-lint.py"
	if [ -f "$lint" ] && [ -n "$PYBIN" ]
	then
		hits=$("$PYBIN" "$lint" "$f" 2>/dev/null | awk -v n="${#f}" '{ print substr($0, n + 2) }' | filter_hits | head -n 24)
		if [ -n "$hits" ]
		then
			out="$out
LINT (see bofad-lint.py rules):
$hits"
		fi
	fi
}

check_prose()
{
	f="$1"
	out=""

	# Oxford comma and mixed line endings come from bofad-lint.py; its Python pattern is tight enough where a clause-comma grep was block-happy.
	lint_checks "$f"
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
	# A whitespace-only line is the project's blank-line indentation, and a block-comment continuation
	# line carries its trailing space by convention. Neither is a finding, so both are skipped here.
	hits=$(awk '/[^ \t].*[ \t]+\r?$/ && !/^[ \t]*\*/ { print NR }' "$f" | filter_hits | head -n 3)
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
		*.java|*.cs|*.c|*.cpp|*.h|*.hpp|*.ixx) check_code "$f" ;;
		*.py) check_python "$f" ;;
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
