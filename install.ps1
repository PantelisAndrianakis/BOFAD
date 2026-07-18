# BOFAD installer for Windows.
# Installs BOFAD for Codex CLI, Antigravity and OpenCode. Claude Code uses the plugin.
# Idempotent: re-running updates existing installs in place.

$ErrorActionPreference = 'Stop'

$skillSource = Join-Path $PSScriptRoot 'skills\bofad\SKILL.md'
if (-not (Test-Path $skillSource))
{
	Write-Host 'ERROR: skills\bofad\SKILL.md not found next to this script.'
	exit 1
}

$skillContent = Get-Content $skillSource -Raw
$beginMarker = '<!-- BOFAD:BEGIN -->'
$endMarker = '<!-- BOFAD:END -->'
$block = "$beginMarker`r`n$skillContent`r`n$endMarker"

function Install-Block($targetFile)
{
	$dir = Split-Path $targetFile -Parent
	if (-not (Test-Path $dir))
	{
		New-Item -ItemType Directory -Force $dir | Out-Null
	}

	if (Test-Path $targetFile)
	{
		$existing = Get-Content $targetFile -Raw
		if ($existing -match [regex]::Escape($beginMarker))
		{
			# Replace the existing BOFAD block.
			$pattern = [regex]::Escape($beginMarker) + '[\s\S]*?' + [regex]::Escape($endMarker)
			$updated = [regex]::Replace($existing, $pattern, $block)
			[System.IO.File]::WriteAllText($targetFile, $updated)
			Write-Host "Updated: $targetFile"
			return
		}

		# Append after existing content.
		[System.IO.File]::WriteAllText($targetFile, $existing.TrimEnd() + "`r`n`r`n" + $block + "`r`n")
		Write-Host "Appended: $targetFile"
		return
	}

	[System.IO.File]::WriteAllText($targetFile, $block + "`r`n")
	Write-Host "Created: $targetFile"
}

# Claude Code: installed as a plugin (always-on when enabled), not via this script.
Write-Host 'Claude Code: install as a plugin -> /plugin marketplace add PantelisAndrianakis/BOFAD  then  /plugin install BOFAD@AnotherDimension'

# Codex CLI: global instructions in ~\.codex\AGENTS.md.
Install-Block (Join-Path $env:USERPROFILE '.codex\AGENTS.md')

# Google Antigravity: cross-tool global rules in ~\.gemini\AGENTS.md.
Install-Block (Join-Path $env:USERPROFILE '.gemini\AGENTS.md')

# OpenCode: global rules in ~\.config\opencode\AGENTS.md.
Install-Block (Join-Path $env:USERPROFILE '.config\opencode\AGENTS.md')

Write-Host 'BOFAD installed. Restart your agent sessions to pick it up.'
