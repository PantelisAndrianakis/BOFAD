# Voice harness

The style checker (`hooks/bofad-check.sh`) measures formatting. This harness measures the
part a grep cannot see: register. Does a reply lead with the answer, stay in prose for a
factual question, mark unverified claims honestly, concede without re-arguing, stop when the
information ends.

It exists because the voice is what drifts first and fastest on a weaker or older host model,
and because the retirement of the model this file emulates closes the window for generating
ground truth. The references here are captured while that window is open.

## Files

- `probes.md` - ten register probes. Each has a `### Prompt`, a numbered `### Rubric` of
  pass/fail checks and one `### Reference` answer that passes every line.
- `deltas.md` - the measured host-model results that justify each rubric. Read this first;
  it is also the evidence for the admission rule in SKILL.md (no rule without an observed
  failure it corrects).

## Running a probe

1. Send one probe's `### Prompt` to the target model with BOFAD loaded, at high reasoning
   effort. Capture its reply.
2. Grade the reply against that probe's `### Rubric` with the `bofad-voice-check` agent, or
   by hand. The rubric lines are the only criteria; the reference is calibration, not a
   target, so a different wording that passes every line still passes.
3. A FAIL is a candidate delta. If it repeats across models or probes, it earns a rule or an
   example in SKILL.md and a row in `deltas.md`. A one-off does not.

## Adding a probe

Add a `## NN-slug` block to `probes.md` with the three sections. Keep the reference honest to
every rule in SKILL.md, including its own prose rules, since the checker and CI run on this
file too. A probe with no rubric line that a real host answer has failed is speculation, not
a test - measure before you add it.
