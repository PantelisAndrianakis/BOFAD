---
description: Review code against BOFAD - the mechanical checker plus the semantic code-check agent, findings only, no fixes applied.
argument-hint: [file paths, or blank to review uncommitted changes]
---

Review code against BOFAD in two layers and report findings without fixing anything.

Scope: the paths in `$ARGUMENTS`; with no arguments, the files changed since the last commit (`git diff HEAD --name-only`, untracked files included via `git status --porcelain`). No arguments and a clean tree → say there is nothing to review and stop.

1. Mechanical layer: run `bash "${CLAUDE_PLUGIN_ROOT}/hooks/bofad-check.sh"` with the scoped files as arguments and keep its `file:line` findings verbatim.
2. Semantic layer: run the `bofad-code-check` agent on the same scope, the diff when reviewing uncommitted changes, whole files when paths were given. No such agent in the harness → walk its checklist from `agents/bofad-code-check.md` yourself as an explicit step.
3. Report both layers in one reply: mechanical findings first, semantic findings second, each with `file:line`, most severe first inside each layer. No praise, no rewrites, no fix applied. A clean result in both layers is the word clean and nothing else.
4. End by offering to apply fixes; apply none until asked. Fixes, when asked for, ride the smallest diff and never reformat untouched neighbors.
