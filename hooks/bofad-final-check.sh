#!/bin/sh
# BOFAD final-message check.
# Hook mode (no arguments): reads Claude Code Stop-hook JSON from stdin, pulls the last assistant message out of the transcript and scans it for the measured drift tells: hedge beside a done claim, em or en dash, summary heading, trailing promise. Findings go to stderr with exit 2 so the model continues once and fixes the message; a set stop_hook_active field exits 0 first, so the hook can never loop.
# Standalone mode (file arguments): treats a .jsonl file as a transcript and any other file as a plain final message, reports on stdout and exits 1 on findings; used by CI against the fixture transcripts.
# Extraction ceiling: the transcript is JSONL and this is grep and sed, not a JSON parser. The scan runs on the raw last assistant line, so JSON escapes stay escaped and a tool payload on that line can false-positive; any misparse fails open to exit 0 because a register nudge must never block a turn.

scan_text()
{
	text="$1"
	out=""

	# Em and en dashes, literal or as JSON escapes.
	if printf '%s' "$text" | grep -qE '—|–|\\u2014|\\u2013'
	then
		out="$out
EM/EN DASH (use a comma or a simple hyphen)."
	fi

	# Hedge word within reach of a done claim; the markers rule allows exactly four markers instead.
	if printf '%s' "$text" | grep -qiE '(should|likely|probably)[^.!?]{0,40}(work|works|fix|fixed|fine|correct|resolve)'
	then
		out="$out
HEDGED DONE CLAIM (use Verified / UNVERIFIED / EDITED-UNVERIFIED / NOTED, not should, likely or probably)."
	fi

	# Summary heading that restates what the reply already said.
	if printf '%s' "$text" | grep -qE '## Summary|In summary'
	then
		out="$out
SUMMARY SECTION (the reply already said it once)."
	fi

	# Trailing promise; the turn ends at done, not at a plan.
	tail_text=$(printf '%s' "$text" | tail -c 400)
	if printf '%s' "$tail_text" | grep -qE "I'll now|I will now|Next steps?:|Let me know if"
	then
		out="$out
TRAILING PROMISE (finish the turn instead of promising the work)."
	fi

	if [ -n "$out" ]
	then
		printf 'BOFAD final-message check:%s\n' "$out"
		return 1
	fi
	return 0
}

# Last transcript line that is an assistant message; empty when none exists.
last_assistant_line()
{
	grep '"type":"assistant"' "$1" | tail -n 1
}

if [ $# -gt 0 ]
then
	# Standalone mode.
	fail=0
	for arg in "$@"
	do
		[ -f "$arg" ] || continue
		case "$arg" in
			*.jsonl) line=$(last_assistant_line "$arg") ;;
			*) line=$(cat "$arg") ;;
		esac
		[ -n "$line" ] || continue
		scan_text "$line" || fail=1
	done
	exit $fail
fi

# Hook mode.
input=$(cat)
if printf '%s' "$input" | grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true'
then
	exit 0
fi

transcript=$(printf '%s' "$input" | sed -n 's/.*"transcript_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1 | sed 's/\\\\/\\/g')
[ -n "$transcript" ] || exit 0
[ -f "$transcript" ] || exit 0

line=$(last_assistant_line "$transcript")
[ -n "$line" ] || exit 0

report=$(scan_text "$line")
if [ -n "$report" ]
then
	printf '%s\n' "$report" >&2
	exit 2
fi
exit 0
