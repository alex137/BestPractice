---
slug:              todo-2026-10-31-attach-copied-in-sources-only-at-update-vendors
kind:              decision
domain:            mechanism
severity:          null
status:            done
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "B: a private copied-in source is checked only at Update Vendors, which attaches, clones and refreshes it and records the date; session start says 'checked at the last Update Vendors, <date>' for it; public copies are still checked at session start"
decision_strength: decided
waiting_on:        null
noted:             2026-10-31
closed:            2026-11-12
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

## How It Closes

When Morgan has picked A or B, and the pick is built: session start's
attach list, the freshness row for a copied-in source, and drift-notice's
wording all say the same thing.

## Resolution

**Decided 2026-11-12, Option B** (Morgan, strength: decided): *"Option B
definitely!!!!!"*, and on the general rule that no source is named in the
engine, only whether it is private: *"Perfect. Please open a new session
seeded in the right things and do this, including booked."*

Built the same day, all in BestPractice:

- `freshness_at_update_vendors` in
  [tools/precedent_resolve.py](../tools/precedent_resolve.py) is the one
  reader: a copied-in source is Update Vendors' to check when its copy's
  `precedent-source.json` does not say `"visibility": "public"`, unless its
  entry says `"freshness": "session-start"` or `"update-vendors"`.
- [tools/precedent_engine_freshness.py](../tools/precedent_engine_freshness.py)
  never asks a private copy's repository; its row reads "checked at the
  last Update Vendors, <date>" and is never counted NOT VERIFIED. The merge
  step ([tools/precedent_merge_vendors.py](../tools/precedent_merge_vendors.py))
  skips it the same way. Public copies are asked as before.
- [tools/precedent_update.py](../tools/precedent_update.py): `--attach-list`
  prints the `add_repo` call for each private copy with no clone here; the
  refresh clones a missing copy beside the repository itself, records
  `checked_at_update_vendors`, and leaves the copy for the person only when
  the clone fails.
- [practices/drift-notice.md](../practices/drift-notice.md) treats the
  "checked at the last Update Vendors" line as current, and
  [practices/vendor-update-runbook.md](../practices/vendor-update-runbook.md)
  says to attach first.

Session start's own attach lists already left copied-in sources out; what
sent a session to attach them was the NOT VERIFIED freshness row and
drift-notice's "reach the source directly". The relayed brief placed
drift-notice in the individual set; it is BestPractice's, so nothing
changed there. Test: `check_private_copies_are_checked_at_update_vendors`
in [tools/harness/vh_update_vendors.py](../tools/harness/vh_update_vendors.py).
