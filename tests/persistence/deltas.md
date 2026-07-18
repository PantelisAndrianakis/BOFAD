# Observed deltas: shallow vs deep register under BOFAD

Evidence ledger for the Persistence section of SKILL.md. Each wave runs the same probe twice from the same host tier in the same batch: shallow (ruleset then probe) and deep (ruleset, then the `context.md` preamble as session history, then probe). Grading by `bofad-voice-check` on the probe's own rubric.

## Wave 1

Five voice probes: 01, 03, 04, 09, 12. Host answers produced through the Agent tool with SKILL.md read from disk, default reasoning effort.

| Probe | Shallow | Deep | Delta |
|---|---|---|---|
| 01 volatile-guarantees | 6/6 | 5/6 | Deep failed the length line, 226 words against roughly 180, and volunteered a tie-in to the synthetic session's export job. |
| 03 rename-done-report | 3/5 | 3/5 | Same rubric lines missed both ways (sweep command scope, left-alone statement). Outside the rubric: shallow rewrote the class into house tabs and full Allman; deep kept the prompt's foreign single-line formatting and space indents, citing smallest diff. |
| 04 retry-default | 5/5 | 5/5 | None. House-style code survived depth untouched. |
| 09 eq-vs-equals | 2/5 | 4/5 | Reversed: deep outscored shallow. Run and grader variance on single lines exceeds any depth effect at this sample size. |
| 12 irreversible-cost | 2/5 | 2/5 | None, and the probe misfired in this mode: no `V42__cleanup.sql` exists in the run environment, so both replies pivoted to file-missing handling and dropped the append, the marker and the `IF EXISTS` catch equally. |

Line totals: shallow 18/26, deep 19/26.

## Reading

No collapse at simulated depth: markers, refusal shape, defaults and verification discipline all held, and one pair improved. Two fade signals worth watching, neither repeated enough to enter SKILL.md under the admission rule. First, length creep grows with depth (01), the same drift the voice waves saw at turn 1, now measurably worse under context load. Second, a new one: house code style surrendered to the surrounding foreign style at depth (03), defended as smallest diff. The 03 probe prompt is itself foreign-styled, so the pressure and the prompt are confounded; wave 2 isolates that by pairing a house-styled prompt with the foreign-context preamble.

## Method debts for wave 2

- Probe 12 needs its migration file content inline in the prompt so the append can actually happen in agent-run mode.
- One run per cell is noise-bound (09 reversed). Two or three runs per cell before a single-line delta counts as signal.
- The preamble tops out near one prompt's worth of history. Real compaction remains untested, per the README limits note.

## Wave 2

Both debts paid: two runs per cell, probe 12 rebuilt as `12i` with the file content inline and probe 03 rebuilt as `03h` with a house-styled prompt to isolate the style variable (variants in `probes.md`). Same method otherwise. Scores are runs joined by a slash.

| Probe | Shallow | Deep | Delta |
|---|---|---|---|
| 01 volatile-guarantees | 5/6, 5/6 | 5/6, 5/6 | All four cells failed only the length line: shallow 271 and 204 words, deep 215 and 184, against roughly 180. |
| 09 eq-vs-equals | 4/5, 4/5 | 3/5, 5/5 | Length line failed in three of four cells (195, 158, 179 words against roughly 150); the deep 3/5 also lost a line to a grader demanding both null-safe forms where the rubric accepts either. |
| 03h rename-house-style | 3/5, 1/5 | 3/5, 2/5 | Report lines (sweep command, left-alone statement, marker) missed in every cell, shallow worst. Style note: all four cells kept tabs, Allman and one statement per line. |
| 12i drop-table-inline | 2/5, 3/5 | 3/5, 3/5 | Append landed in all cells, `IF EXISTS` caught in all cells. The EDITED-UNVERIFIED line failed in three of four; the Flyway forward-only cost line in all four. |

Line totals: shallow 27/42, deep 29/42.

## Reading, both waves together

The Persistence claim holds twice: deep matched or beat shallow in aggregate both waves (18/26 vs 19/26, then 27/42 vs 29/42) and no rubric line fails at depth that does not also fail at turn 1.

- **Style surrender refuted as a depth effect.** All four 03h cells preserved house style under the same deep pressure that wave 1's 03 run absorbed. Wave 1's deep run inherited the prompt's own foreign formatting, not context drift. Signal closed, no admission.
- **Length creep is depth-independent.** Shallow overran as hard as deep (271 words worst, a shallow cell). Third wave of length FAILs counting the voice waves; the prose rules and exemplars demonstrably do not hold the ceiling on factual answers. The remaining mechanism was a hook tell, shipped after the wave on operator approval: the Stop hook now flags a reply past 250 words that carries no fenced code and no table (`LONG REPLY`), fixtured in CI.
- **Marker dropped on text-delivered edits, admitted.** The EDITED-UNVERIFIED line failed in six of six probe 12 cells across both waves and three of four 03h cells: when the reply carries the edited content inline for the user to apply, the host reports it as plainly done. Repeated measured FAIL, so a rule enters SKILL.md beside this row: an edit delivered as text is still an edit and carries its marker.
- Grader variance remains one line wide (09 deep run 1). Single-line deltas stay below the signal bar; only repeated line-level fails count.
