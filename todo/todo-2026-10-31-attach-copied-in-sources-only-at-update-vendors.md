---
slug:              todo-2026-10-31-attach-copied-in-sources-only-at-update-vendors
kind:              decision
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "Morgan's answer: a policy change to session start and drift-notice"
batch:             null
decision:          null
decision_strength: null
waiting_on:        Morgan
noted:             2026-10-31
closed:            null
---
## What

Should a session attach a copied-in source (a `vendored: true` entry in
`precedent.json`, such as a voice pack) at every session start, or only
when it runs Update Vendors?

Today a consuming repository's session start tells the session to attach
every declared source, copied-in ones included. A copied-in source is
already in the repository as files, so nothing loads from its clone; the
attach exists only so the freshness check can ask the private repository
whether it has moved. Each attach is a prompt the person approves, and one
consuming repository copies in two private sources, so every ordinary
session there asks for two repositories it never reads.

## Options

- **A. Keep attaching them every session.** The freshness line stays live:
  a voice pack that moved upstream is reported in the first reply of the
  next session. Costs two prompts per session in that repository.
- **B. Attach them only for Update Vendors** (my pick). Session start skips
  them, and the freshness line for a copied-in private source reads
  "checked at the last Update Vendors, <date>" instead of NOT VERIFIED.
  Update Vendors attaches them, refreshes the copies and records the date.
  Costs: a voice pack that moved is heard about at the next Update Vendors
  instead of the next session. Update Vendors runs most days, and the copy
  only changes there anyway, so a session learning of it sooner can do
  nothing with it but say so.

## Notes

Raised by the 2026-10-31 repository-name-capitalization fix (BestPractice
branch `2026-10-31-themorgan-repo-name-case-k74nv-mjmpw`), which a
consuming repository's Update Vendors session asked for after the person
approved one source twice. Building B means changing session start's
attach list, the freshness check's row for a copied-in source, and the
drift-notice practice's wording.
