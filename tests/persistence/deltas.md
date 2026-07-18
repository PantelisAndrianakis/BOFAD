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
