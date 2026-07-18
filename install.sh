#!/bin/sh
# BOFAD installer for Linux/macOS.
# Installs BOFAD for Codex CLI, Antigravity and OpenCode. Claude Code uses the plugin.
# Idempotent: re-running updates existing installs in place.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_SOURCE="$SCRIPT_DIR/skills/bofad/SKILL.md"
BEGIN='<!-- BOFAD:BEGIN -->'
END='<!-- BOFAD:END -->'

if [ ! -f "$SKILL_SOURCE" ]; then
	echo "ERROR: skills/bofad/SKILL.md not found next to this script."
	exit 1
fi

install_block()
{
	target="$1"
	mkdir -p "$(dirname "$target")"

	if [ -f "$target" ] && grep -q "$BEGIN" "$target"; then
		# Replace the existing BOFAD block.
		awk -v begin="$BEGIN" -v end="$END" -v src="$SKILL_SOURCE" '
			$0 == begin { print begin; while ((getline line < src) > 0) print line; skip = 1; next }
			$0 == end { print end; skip = 0; next }
			!skip { print }
		' "$target" > "$target.tmp" && mv "$target.tmp" "$target"
		echo "Updated: $target"
	elif [ -f "$target" ]; then
		{ echo ""; echo "$BEGIN"; cat "$SKILL_SOURCE"; echo "$END"; } >> "$target"
		echo "Appended: $target"
	else
		{ echo "$BEGIN"; cat "$SKILL_SOURCE"; echo "$END"; } > "$target"
		echo "Created: $target"
	fi
}

# Claude Code: installed as a plugin (always-on when enabled), not via this script.
echo 'Claude Code: install as a plugin -> /plugin marketplace add PantelisAndrianakis/BOFAD  then  /plugin install BOFAD@AnotherDimension'

# Codex CLI: global instructions in ~/.codex/AGENTS.md.
install_block "$HOME/.codex/AGENTS.md"

# Google Antigravity: cross-tool global rules in ~/.gemini/AGENTS.md.
install_block "$HOME/.gemini/AGENTS.md"

# OpenCode: global rules in ~/.config/opencode/AGENTS.md.
install_block "$HOME/.config/opencode/AGENTS.md"

echo "BOFAD installed. Restart your agent sessions to pick it up."
