---
slug:            gotcha-2026-09-13-the-private-practice-sets-reach-a-session-through-the-enviro
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

The private practice sets reach a session through the environment credential, not through `add_repo`: set `PRECEDENT_GIT_TOKEN` and `PRECEDENT_SOURCE_BASE_URL` ([PER_MACHINE_SETUP.md](../documentation/PER_MACHINE_SETUP.md)) and the SessionStart hook clones them before the first turn, where no ordering rule can reach it.

## Story

**The private practice sets reach a session through the environment
credential, not through `add_repo`: set `PRECEDENT_GIT_TOKEN` and
`PRECEDENT_SOURCE_BASE_URL` ([PER_MACHINE_SETUP.md](../documentation/PER_MACHINE_SETUP.md)) and the SessionStart
hook clones them before the first turn, where no ordering rule can reach it.**
Verified end to end 2026-09-10 on a brand-new container and again 2026-09-11:
all four sources on disk before the first turn. **That "before the first
turn" guarantee did NOT hold on 2026-09-14, and it is the failure to plan
for.** In a resumed session the four clones landed *during the second turn*
-- reflog `clone: from .../precedent-team-writing` timestamped mid-session --
so the whole first turn ran with every team and individual practice silently
absent, on the universal set alone. Nothing announced it except the
unresolved-source notes, which read identically to the steady-state failure
this entry is about. **So treat the credential route as reliable but not
instantaneous**: on turn one, check the session-start source line rather than
assuming, and where something reports a source missing, look again before
concluding anything -- a race and a real absence print the same text
(practice: [diagnosis-is-measured](../practices/diagnosis-is-measured.md)).
The cost when that is skipped was paid the same day: a session read the
missing sources, relayed this entry's own two candidate causes -- refused
credential, retired repository -- as a diagnosis, and recommended deleting
three live source declarations. Both causes were wrong; the clone had simply
not run yet.
[tools/precedent_resolve.py](../tools/precedent_resolve.py) prints `MISSING` when
no credential is set and `SET` when one is set and a clone still failed; the
session check and the session-start source report print the same line.
**`add_repo` is the fallback, and what is measured about it does not add up.**
Three 2026-09-07 measurements had it refusing a cross-owner add in BOTH
directions — including as a session's very first tool call, so "call it before
anything else" is not a remedy — while two other sessions held repositories
from both owners at once and pushed to all of them. Nobody has an explanation
that fits both, so call it, read what it says, and proceed from that; never
from a remembered result. The full contradictory sequence is entry 34, and the
cost of skipping it is the entry above: a session with `individual` and `team`
unresolved applies the wrong rules all day and cannot tell. **If `env | grep
-c PRECEDENT` says 0, that is not proof the runner drops variables** — an
account can hold two environments with the SAME NAME and the selector cannot
tell them apart, which is what it was three times. The setting-up half of this
now lives where someone setting the variables reads it,
[PER_MACHINE_SETUP.md](../documentation/PER_MACHINE_SETUP.md)'s environment table; the three-day sequence is
[record/GOTCHAS_ARCHIVE.md](../record/GOTCHAS_ARCHIVE.md) entry 29.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
