---
description: Review code against BOFAD - the mechanical checker plus the semantic code-check agent, findings only, no fixes applied.
argument-hint: [file paths, or blank to review uncommitted changes]
---

Review code against BOFAD in two layers and report findings without fixing anything.

Scope: never a subset of the change. With no arguments, every file changed since the last commit in each repository the work touched: `git diff HEAD --name-only` plus untracked files from `git status --porcelain`, or `svn status` in an svn working copy. With paths in `$ARGUMENTS`, those paths, and before reporting, the same status listing of their repositories: any changed source file missing from the paths joins the scope, script, sed and regex edits included. Files byte-identical across projects are reviewed once per content hash, and the report names each hash group. No arguments and a clean tree → say there is nothing to review and stop.

1. Mechanical layer: run `bash "${CLAUDE_PLUGIN_ROOT}/hooks/bofad-check.sh"` with the scoped files as arguments and keep its `file:line` findings verbatim.
2. Semantic layer: run the `bofad-code-check` agent on the same scope, the diff when reviewing uncommitted changes, whole files when paths were given. No such agent in the harness → walk its checklist from `agents/bofad-code-check.md` yourself as an explicit step.
3. Report both layers in one reply. It opens with the count of files reviewed against files changed, then mechanical findings, then semantic findings, each with `file:line`, most severe first inside each layer. No praise, no rewrites, no fix applied. A clean result in both layers over the full changed set is the count line and the word clean, nothing else; a changed file left out is never clean.
4. End by offering to apply fixes; apply none until asked. Fixes, when asked for, ride the smallest diff and never reformat untouched neighbors.
