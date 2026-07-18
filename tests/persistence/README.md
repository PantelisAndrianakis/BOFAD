# Persistence harness

The voice harness grades register at turn 1; this one grades the same register after simulated session depth. The Persistence section of SKILL.md claims the rules do not fade over long turns, tool sequences or summarized context. This harness is that claim's test: the delta between a probe's shallow score and its deep score is the measurement.

## Files

- `context.md` - the deep-session preamble: a synthetic summarized session carrying counter-pressure (foreign-style code, header-heavy replies, hedge-worded status lines). Deliberately dirty; excluded from the CI prose check on purpose.
- `deltas.md` - the measured shallow and deep scores per wave.

## Running a wave

1. Pick probes from `tests/voice/probes.md` or `tests/reasoning/probes.md`, favoring the rules most likely to fade: prose shape, status markers, house code style.
2. For each probe, produce two replies from the same host tier in the same batch: shallow (SKILL.md loaded, then the probe prompt) and deep (SKILL.md loaded, then the whole of `context.md` as session history, then the probe prompt).
3. Grade both replies against the probe's rubric with the `bofad-voice-check` agent. The rubric is identical for both; only the context differs.
4. Record both verdicts and the delta in `deltas.md`. A rubric line that passes shallow and fails deep is a fade; a fade that repeats across probes or waves earns a rule or hook per the SKILL.md admission rule, with the evidence row here.

Shallow and deep always run in the same wave with the same SKILL.md; never compare a deep score against a shallow verdict from an older wave, ruleset drift would pollute the delta.

## Limits

The preamble simulates depth, it is not real harness compaction: the model sees one long prompt, not a context window that was actually summarized mid-session. A fade this harness finds is real; a clean sheet here does not prove survival of true compaction. Extend `context.md` rather than replacing it, so waves stay comparable.
