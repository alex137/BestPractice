---
slug:              todo-2026-10-12-inner-workings-shown-to-non-owners
kind:              manual
domain:            mechanism
severity:          null
status:            done
disposition:       null
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-12
closed:            2026-10-13
---
## What

- [x] **Bring every check and tool that speaks to a person in line with [inner-workings-for-code-owners](../practices/inner-workings-for-code-owners.md).**

Morgan, 2026-10-12 (strength: decided; BP is BestPractice (BP)): "Anything on the inner works of how
BP works including things like file management, dealing with temporary
files, dealing with temporary repos etc -- should only be for codeowners.
We must assume that non-codeowners are very low tech people."

The archive check was brought in line the same day
([tools/precedent_gate.py](../tools/precedent_gate.py), `_is_code_owner`).
The rest has not been read for it: the reply gate's other requirements
(The Boildown's branch and stage lines, "Files touched", the session-check
rows printed at the start of a turn), the stop hook's refusal texts that a
session relays, and Update Vendors' report as a session passes it on. Each
that explains a mechanism to the person asks `precedent_audience.is_code_owner`
first and, for anyone else, settles the matter itself or says the outcome in
one plain sentence.

## Closes when

Every requirement and report that reaches a person who is not a code owner
has been read for inner workings, and each one that carried them asks
`is_code_owner` first, with a harness case per change.

## Done

Morgan, 2026-10-13: "Now!!! Nothing technical should ever be said to a non
technical person." Every message on the list above now asks
`is_code_owner` first or says it is never relayed: the reply gate's
plain-words instruction, the Files touched rule, the session-setup warning,
the stop hook's refusal and Update Vendors' report, each with a harness case
in `check_archive_gate_keeps_inner_workings_from_non_owners`.
