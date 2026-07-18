# Observed deltas: host reasoning under BOFAD

Evidence ledger for reasoning-probe admissions: a rule enters SKILL.md only beside a measured failure it corrects.

## Method

Five probes from `probes.md`, each sent cold to the host tier through a subagent with SKILL.md read from disk, rubric withheld. Graded by hand against the rubric only, arithmetic inside replies re-checked by hand.

## Results

| Probe | Trap | Score | Note |
|---|---|---|---|
| 01 debug-misdirection | blamed method is innocent | 4/4 | Rejected the anchor with the math shown correct, found the refresh on the sweep path, fixed with a non-refreshing peek. |
| 02 hidden-second-caller | call site in plugins dir | 4/4 | All three files edited, sweep grep named with the plugins directory included, the new filter flagged as new behavior needing an API check. |
| 03 race-window | check-then-act on volatile | 4/4 | One read into a final local, no lock, volatile kept, two-thread hammer harness shipped. One em dash in prose. |
| 04 silent-spec-edge | empty list divides by zero | 4/4 | Explicit empty and null branch, default stated as overridable, truncation named, hand math correct. |
| 05 boundary-page | partial last page, past-end page | 4/4 | Clamped bounds, empty for out-of-range in both directions, hand-check correct: 25 results, page 3 gives 5, page 4 gives 0. |

## Admissions

None. 20 of 20 rubric lines passed and the admission rule requires a failure to correct. The candidate rules held ready (predict-then-observe in debugging, pre-code edge-case sweep, constraint ledger for 3+ requirement tasks) stay out for lack of evidence.

What this wave does not prove: the probes are single-shot, small and self-contained, and the runs used a strong scaffold. A next wave hunts where these could not: multi-constraint tasks where one requirement tends to drop, misdirection with a plausible partial bug in the blamed method, long-context tasks where an early constraint must survive to the end. Harder probes before more rules.

Cross-harness observation for the voice ledger: the em dash in probe 03 repeats the measured voice tells; the Stop hook exists for exactly that and does not run inside subagents.
