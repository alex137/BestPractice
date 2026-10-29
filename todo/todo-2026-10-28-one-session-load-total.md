---
slug:              todo-2026-10-28-one-session-load-total
kind:              decision
domain:            mechanism
severity:          medium
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "go, one number everywhere"
decision_strength: decided
waiting_on:        null
noted:             2026-10-28
closed:            null
---
## What

Token-budget blocks came back on 2026-10-27 and 2026-10-28 because tokens
moved between budgets (rules moved into the ladder set, sets copied into
repositories, a fix to how a share is counted), not because sessions got
heavier. Every budget is a separate tight number only Morgan can raise, so
any change to which budget pays for a rule asks him again.

The analysis and the proposal are in
[spec/SESSION_LOAD_ONE_TOTAL_PLAN.md](../spec/SESSION_LOAD_ONE_TOTAL_PLAN.md):
one refusing number per session, the total it loads from its generated
files, declared once by the person and copied into each repository so CI
reads it too; no per-part number is stored or approved. Revised the same
day after an independent review.

## Decided

Morgan, 2026-10-28 (strength: decided): "Go, one number everywhere" --
the revised plan, with one person-wide total rather than one per kind of
repository.

The number: Morgan, 2026-10-28 (strength: decided): "okay, yes, let's do
it, 10k approved" -- 10,000 tokens, against about 8,100 measured in
BestPractice, the largest of the four repositories measured that day.

## Built

2026-10-28, on branch 2026-10-28-themorgan-one-session-load-total-ayyyj-mtcmv:
the total is the one refusing budget wherever a registry declares
`session_load_tokens`; Update Vendors copies the person's total and their
words from the individual set (`record_person_total` in
[tools/precedent_update.py](../tools/precedent_update.py)); the gates print
which part a branch grew; tests in
[tools/verify_harness.py](../tools/verify_harness.py)
(`check_session_load_total_is_the_one_budget`).

Left on purpose (needs: every repository to carry the total first -- an
Update Vendors run on each): deleting `brought_sets_tokens` and
`individual_set_tokens` from the individual set, and the copy-in approval
code in Update Vendors. Under a total they are already ignored; deleted
before a repository has its total, they would charge the brought sets to
that repository's ceiling and refuse there.

## Closes when

Every repository Morgan uses carries `session_load_tokens` (by Update
Vendors, from his individual set), and the deletions left on purpose above
are done.
