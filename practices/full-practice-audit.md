---
slug:        full-practice-audit
title:       A full practice audit — an on-demand, whole-catalogue sweep, on request only
tier:        on-demand
severity:    advisory
applies_to:  ["**"]
occasion:    "a person explicitly asks for a full practice audit (or \"practice check\") across the whole catalogue"
gates:       []
index_clause: "sweep every source's full catalogue, one practice at a time, on request only"
checked_by:  null
defines:     ["full practice audit"]
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "pending review"
---
## Rule
When a person explicitly asks for a full practice audit, run
[tools/full_practice_audit.py](tools/full_practice_audit.py): it enumerates
every active practice from every source in force for the checkout —
universal, team, repo-local, and individual, resolved the same way
[tools/precedent_resolve.py](tools/precedent_resolve.py) does for ordinary
loading — and prints the full Rule text of every practice that has no
mechanical check and no gate (the set that can only be judged). Judge each
one against the actual repo state with a closed question, one practice at
a time — *does this apply; if so, is it satisfied, yes or no, with the
specific file and line* — never the open "which of these might apply."
On-demand only, invoked explicitly by a person; never a routine or
automated gate.

## Detail
Practices already covered by a `checked_by` script or a `gates` entry are
listed but not re-judged here — confirm those, if wanted, by actually
running `tools/precedent_check.py` and `tools/precedent_gate.py --list`,
not by re-reading their Rule text, since the check is the faster and more
reliable way to know their status. The audit's real workload is the
judgment-only remainder.

## Why
**Read this before trusting the result.**
[spec/ATTENTION_CEILING.md](spec/ATTENTION_CEILING.md) pre-registered and
ran almost exactly this shape — a retrospective, judge-only pass over
practice candidates, "the review arm" — before this practice existed.
Predicted 80–86% recall; measured 54%, *worse* than a session doing the
work with no review pass at all (84%). The document's own verdict: "a big,
open-ended, whole-catalogue review... is the mechanism that already
failed." The validated fix was converting more practices to mechanical
`checked_by` checks, which cost nothing regardless of catalogue size —
that is the primary control, not this practice. This audit is a knowingly
unproven backstop for whatever enforcement has not yet reached — worth
having for what it can still catch (a formatting or naming convention with
no mechanical signature, missed by every other channel) — never a
substitute for enforcement. **A first evaluation ran 2026-09-04**
([spec/ATTENTION_CEILING.md](spec/ATTENTION_CEILING.md), "The
audit-judgment result") and scored 6 of 6 (100%) on six seeded/known cases,
validating the prediction that full-Rule, one-at-a-time, evidence-attached
judgment escapes the review arm's 54% ceiling — but N=6 on a single run by
a single judge is a first signal, not the review arm's own multi-run
discipline, so still not something to lean on routinely at higher stakes
without the fuller evaluation
[spec/UNBUILT_PLAN_ITEMS.md](spec/UNBUILT_PLAN_ITEMS.md) still names as
open.

## Story
Raised 2026-09-03 in a brainstorm about a missed headline-formatting issue
that had been caught and fixed once, with no guarantee of being caught the
next time it recurred. The first version of the idea proposed was a
routine, human-invoked full sweep with no caveat attached — checking the
plan's own attention-ceiling research before building it turned up the
review-arm result above, which the brainstorm had not accounted for.
Built anyway, on request, but disclosed honestly as an unvalidated
detective control rather than presented as a solved problem — building it
silently, without surfacing that history, would have repeated the exact
failure this repository's own research already found once.

## Install
[tools/full_practice_audit.py](tools/full_practice_audit.py) is the
enumeration; it reuses `tools/precedent_resolve.py`'s own source resolution
rather than re-walking `precedent.json`, so it always reports exactly the
sources a session's ordinary loading would also see. No mechanical
`checked_by` exists for this practice's own Rule, and probably can't: what
it asks for is a session's judgment applied to a catalogue enumerated by
the tool, not a property of the repo's tree the way `routing-audit`'s own
tool-existence-and-bookkeeping check is — the same class of resistant-to-
automation practice `checkable-gets-checked` and `mistakes-become-rules`
already name. See [routing-audit](routing-audit.md) for the cheaper,
narrower sibling mechanism this one deliberately does not replace, and
[spec/UNBUILT_PLAN_ITEMS.md](spec/UNBUILT_PLAN_ITEMS.md) for the
pre-registered evaluation this practice's own reliability still needs.
