---
slug:            gotcha-2026-10-05-a-practice-routed-only-by-its-own-files-is-never-shown-to-anyone
status:          retired
noted:           2026-10-05
severity:        notable
retired:         2026-10-05
retires_when:    "layered-practice-packs no longer counts a route that fires only on a practice's own tool files, or a check that only confirms its tool exists, as reaching a session"
---
## Symptom

A practice reads as reachable to every check, and in practice no session is
ever told to do it. The tell is a state file or log the practice is meant to
keep that stops changing on the day it was seeded:
[tools/routing_audit_state.json](https://github.com/alex137/BestPractice/blob/staging/tools/routing_audit_state.json)
has exactly one commit, its seeding on 2026-09-04.

## Story

**2026-10-05, found while planning practice rechecks.** The routing audit's
`applies_to` names only its own tool and its own state file, so
`precedent_paths.py` shows its Rule to a session only when that session is
already editing the audit. Its registered check confirms the tool exists and
keeps its bookkeeping honest, and says plainly that it cannot see whether
the audit is run. Both counted as routes in `layered-practice-packs`, so the
practice passed as reachable while nothing could ever prompt anyone to run
it. A second session reviewing the plan named the cause: the audit was
reachable only from its own files.

The same shape caught the field-order check the same day, from a different
angle: a "temporary" warning whose end condition was a sentence nobody
owned. Both are a mechanism that looks wired from the inside and reaches
nobody from the outside.

## Fix

When you route a practice, ask what work a session would be doing when the
route fires. If the only answer is "maintaining this practice's own
tooling", it is not a route. Give it one that fires during the work the
practice is about: a glob over the files that work touches, a gate, or an
occasion-index line. A check counts as a route only if it can fail when the
practice goes unfollowed, not merely when its tool goes missing. `layered-practice-packs` applies this test since 2026-10-05, and the routing
audit's route now includes every practice file -- step 4 of
[spec/PRACTICE_STANDING_AND_RECHECK_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/PRACTICE_STANDING_AND_RECHECK_PLAN.md).
