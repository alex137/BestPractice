---
slug:              todo-2026-10-31-document-project-template-sections-into-practices
kind:              decision
domain:            mechanism
severity:          null
status:            open
disposition:       null
remind_on:         null
blocked_on:        "out of scope of the 2026-10-31 loader-template move, and a judgment on wording written for non-developers"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-31
closed:            null
---
## What

On 2026-10-31 the loader template's "Merging a thread branch", Conventions,
Working in parallel and Administrator requests sections became practices
(merge-runbook, commits-credit-the-driver, working-in-parallel,
administrator-requests), and Update Vendors retires them from installed
repositories (`RETIRED_AGENTS_MD_SECTIONS` in
[tools/precedent_vendor_engine.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_vendor_engine.py)).
[templates/document-project/AGENTS.md](https://github.com/alex137/BestPractice/blob/staging/templates/document-project/AGENTS.md)
still carries its own copies of three of them, reworded for contributors who
are not developers (measured that day: its runbook lacks 6 of the loader
version's blocks and has 5 of its own; its Administrator requests lacks 10
and has 2). The retirement deliberately applies only to the loader family.

## Done when

Each of the three document-project sections is either retired the same way
(its reader's wording kept as a document-project add-on practice, `adds_to:`
the practice) or recorded as staying, with the reason, and the template and
`RETIRED_AGENTS_MD_SECTIONS` agree.
