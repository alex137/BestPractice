---
slug:              todo-2026-10-12-inner-workings-shown-to-non-owners
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "needs: decision -- Morgan, whether to run the audit now (about two hours)"
batch:             null
decision:          null
decision_strength: null
waiting_on:        Morgan
noted:             2026-10-12
closed:            null
---
## What

- [ ] **Bring every check and tool that speaks to a person in line with [inner-workings-for-code-owners](../practices/inner-workings-for-code-owners.md).** (needs: decision -- Morgan, whether to run the audit now)

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
