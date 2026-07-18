# Voice harness

`hooks/bofad-check.sh` measures formatting; this harness measures register: answer first, prose for questions, honest markers, concession without re-arguing, stopping at done. References are frozen captures, never regenerated.

## Files

- `probes.md` - fifteen probes: a `### Prompt`, a numbered `### Rubric` of pass/fail checks, one `### Reference` answer that passes every line.
- `deltas.md` - the measured results behind every rubric and the admission-rule evidence.
- `voice-examples.golden` - byte pin of the SKILL.md Voice examples block; CI fails when the existing block changes other than by appending. Extend it after a harvest.

## Running a probe

1. Send a probe's Prompt to the target model with BOFAD loaded, at high reasoning effort. Capture the reply.
2. Grade it against the Rubric with the `bofad-voice-check` agent or by hand. Rubric lines are the only criteria; the reference is calibration, not a target.
3. A FAIL that repeats across models or probes earns a rule or example in SKILL.md and a row in `deltas.md`; a one-off does not.

## Adding a probe

Add a `## NN-slug` block with the three sections. References obey every SKILL.md rule; the checker and CI run on this file too. No rubric line without a real host answer that failed it - measure first.
