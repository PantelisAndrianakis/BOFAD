#!/bin/sh
# BOFAD pre-commit check. Runs the mechanical style check over staged source files and blocks the commit on violations.
# Install: copy this file and bofad-check.sh into <repo>/.git/hooks/, rename this one to pre-commit, keep both executable.
# Checks the working tree version of each staged file, not the staged content; good enough when the editor commits right after editing.
# Findings are scoped to staged lines, matching the in-session hook, so a small fix in a legacy file is not blocked over untouched neighbors.

dir=$(dirname "$0")
files=$(git diff --cached --name-only --diff-filter=ACM)
[ -n "$files" ] || exit 0

fail=0
IFS='
'
for f in $files
do
	BOFAD_CHANGED=$(git diff --cached -U0 -- "$f" | awk '/^@@/ { split($3, a, ","); start = substr(a[1], 2) + 0; count = 1; if (a[2] != "") count = a[2] + 0; for (i = 0; i < count; i++) print start + i }' | tr '\n' ' ')
	export BOFAD_CHANGED
	sh "$dir/bofad-check.sh" "$f" || fail=1
done

if [ $fail -ne 0 ]
then
	echo 'Commit blocked by BOFAD style check. Fix the findings above or bypass once with --no-verify.'
	exit 1
fi
exit 0
