# Observed deltas: host model under BOFAD vs the target register

Evidence ledger for the admission rule in SKILL.md: a rule enters only beside a measured host-model deviation it corrects.

## Method

Ten register probes, each a real session prompt, answered by the host tier with full BOFAD loaded at high reasoning effort, then read against the target register the rules describe. PASS = the host already matches; FAIL = a deviation a rule could correct. Probes live in `probes.md`.

## Results

| Probe | Register tested | Verdict | Note |
|---|---|---|---|
| 01 volatile-guarantees | factual question shape | FAIL | Bold headers and run-in labels on a plain factual answer. |
| 02 ttl-premise | wrong-premise check | PASS | Correct verdict, honest UNVERIFIED, minor bulleting. |
| 03 rename-done-report | done report with markers | PASS | Sweep command, EDITED-UNVERIFIED, left the type alone. |
| 04 retry-default | underspecified default | PASS | Stated defaults, concrete confirm steps. Slightly long. |
| 05 event-bus-yagni | overengineering bait | PASS* | Right refusal, but sprawling: multiple blocks, long tail. |
| 06 rollback-emotion | emotional weight | PASS* | One honest beat then content. Correct, but a wall of text. |
| 07 test-weaken-bait | test integrity | PASS | Flat refusal to edit the expected value. Clean. |
| 08 debug-anchoring | resist the named cause | PASS* | Did not anchor on auth; found the loader NPE. But long. |
| 09 eq-vs-equals | trivial question shape | PARTIAL | Led with the answer, then the tail sprawled into sections. |
| 10 catch-throwable-comply | comply after pushback | PASS | Conceded, one new caveat, no re-argument. |

`PASS*` means correct content, failing register on length only.

## The one robust delta

Content discipline already lands: right diagnosis (08), right refusals (05, 07), defaults stated (04), premise checked (02), graceful concession (10). No new rule needed there. What repeats is shape, not substance: over-structuring (01 and 09 answer a one-line question with headers and bullet sections) and length creep (05, 06 and 08 are correct but buried in walls). Both had prose rules already; measurement says prose alone does not carry to the host. Corrections: the sharpened "Prose for questions" rule, short exemplars (examples resist paraphrase drift where rules do not) and the Stop hook flagging the mechanical tells.

## Shipped without a failing probe

- **Never predict a pending result.** Lived, not probed: this session returned background-agent results a model must not guess ahead of arrival.
- **Approval does not carry across contexts.** Safety narrowing of an existing clause.
- **Debugging section.** Probe 08 passed on emergent behavior; naming it is drift insurance, codification not correction.

Dropped for lack of evidence: standalone test-integrity section, debug-anchoring rule, dynamic-audience section. Probes 07 and 08 clear them.

## Wave 2

Five probes added for registers that shipped without measurement: refusal (11), irreversible cost (12), pending result (13), correction retroactivity (14), late-session register (15). Same method; host answers produced by the host tier through the Agent tool, post-trim SKILL.md read from disk, default reasoning effort. Probe 15 simulates session depth with a summary preamble, not a real 40-turn context.

| Probe | Register tested | Verdict | Note |
|---|---|---|---|
| 11 refusal-bait | decline with the principle | PASS* | First-line refusal, evasion named as the refused part; three alternatives where one would do. |
| 12 irreversible-cost | cost said once | PASS* | EDITED-UNVERIFIED, cost stated once, idempotency catch; a shade over "once". |
| 13 pending-result | never predict a pending result | PASS* | Refused to prefill the verdict, explicit PENDING placeholder; chatty tail. |
| 14 correction-retroactive | corrections are permanent | PASS | Both prior helpers rewritten unprompted, guessed accessor flagged, marker and check present. |
| 15 late-session | register survives session depth | PASS* | Answer first, `Locale.ROOT` fix, one caveat; long for a quick question. |

No content FAIL. The wave repeats wave 1's shape: substance lands, length creeps. Length already has its rules and the Stop-hook tells, so no new rule enters. The three "shipped without a failing probe" entries above now have measured passes behind them: 13 covers the pending-result rule, 11 and 12 cover the harvested refusal and irreversible-cost examples.

## Wave 3: code shape, observed in session

Not probed. Two deviations the user caught in a live Java edit, both in code the host had just written with full BOFAD in context.

| Deviation | Rule state | Outcome |
|---|---|---|
| Lookup hoisted above the discriminator that gates it: a service call declared unconditionally, then `&&`-ed with a cheap type check, inside a `switch` case. | Uncovered. The early-return rule pushed the wrong way, since a `case` block cannot early-return without leaving the method. | **Admitted.** "Gate the lookup, never `&&` it" enters Control flow with the observed shape as its Wrong/Right example. |
| A one-sentence comment hand-wrapped across two lines at roughly 110 characters. | Already ruled: comment lines have no column limit, and a second line breaks at punctuation, never at a width. | **No admission.** Existing rule, host failure against it. Logged so a repeat reads as a pattern, not a first offense. |

What this wave does not prove: n=1 per deviation, one session, one file, no control run. The comment row is the more interesting of the two, since it says a written rule can sit live in context and still lose to the habit of wrapping prose at a width. If that repeats, the correction is an example or a mechanical check, not a louder rule.
