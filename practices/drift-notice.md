---
slug:        drift-notice
title:       A session-start notice asks about drift immediately, not at the end
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Session start is a moment, not a file; the occasion index reaches it."
occasion:    "session start reports a source BEHIND or NOT VERIFIED"
gates:       []
index_clause: "raise it at once and file it; not verified is not current -- verify directly"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-05"
approved_by: "pending PR review -- drafted 2026-10-05 by Morgan F, moved from the shared set precedent-shared-repo-maintenance"
strength: decided
---
## Rule
Nothing updates a vendored source between sessions (upstream updates are taken by `Update Vendors`, attended); this rule makes sure a session that is here says so, since the person who could approve an update is right here from the first turn. At session start, compare each vendored source's recorded commit against its actual head (one cheap remote query, no model call), and if either has moved, say so as part of catching the person up, not saved for the end of the session. **A source the check could not verify is not a current one.** A fast, clean failure (missing credentials, a permission error) means "could not verify", never "confirmed fresh": say so, reach the source directly if the environment offers any way to, and if it offers none, say plainly that you could not verify it rather than reporting it current.

## Detail
A fired notice is also persisted, not just printed: file it as one `todo/todo-<date>-vendor-drift.md` item (`disposition: ask`) naming both commits, so it survives the turn and the open-items index keeps showing it. Taking either update stays deliberate, whenever it's raised -- never without being asked. If a merge lands in the same session while a notice is still open, re-ask right there rather than waiting for the end of the session. Fallback: if no notice fired at session start (an incomplete install, an offline start), repeat the same cheap comparison at the end of the session, right after the merge runbook's own steps.

The freshness check stays silent on a transient failure (offline, a timeout), because a notice that only means "the network hiccuped" is worse than none. A standing gap is different: an environment with no credentials for the source fails the same way every session, and read as silence it would mask real drift for as long as that environment exists. So the check prints a distinct "could not verify" line for a fast, clean failure, and the session treats it as above.

## Why
A purely printed notice competes for a session's attention against whatever concrete task the person actually opened the session to do, and can lose that fight silently -- read once, never acted on, and nothing forces it back into view.

## Story
Migrated here from RepoPersonalPreferences by the phase-3 private-set
migration; the Story is backfilled from that pack's own text. Two real
incidents shaped it.

The first, on 2026-08-27, is why a fired notice is persisted rather than
only printed. In a dependent repo a drift notice fired at session start, was
never raised to the user, and surfaced only when he asked directly a full
task later. Nothing had malfunctioned -- the notice was printed and is in the
transcript. It simply lost a priority fight against whatever concrete task
the session had been opened to do, and once the turn moved on nothing forced
it back into view. A notice that competes for attention and loses is
indistinguishable from one that never fired, so the notice now also writes
itself into the repo's own backlog document, where a per-commit check keeps
warning while the entry stays open.

The second is why the check verifies the install and not just the recorded
commit. A repo can carry a vendored tree without carrying the mechanisms
that keep it current -- through a fork, a template copy, or the case that
actually prompted it, a repo vendored from an already-dependent repo rather
than from canonical source. Comparing recorded commits there answers a
question nobody asked, because the wiring that would act on the answer is
missing. So a missing workflow, bootstrap snippet or woven-in section is
reported as an incomplete install rather than as drift, with an offer to
finish it from canonical source regardless of which repo the files on disk
arrived from.

Taking an update stays deliberate, which is the one deliberate difference
from the scheduled syncs that merge unattended: a human is already present
to answer, so there is no reason to skip the ask.

**2026-10-01: absorbed fresh-check-escalation** (Morgan, in the reduction
pass: *"Question 3 - all are great, approved"*, strength: decided). Both
rules are about what a session does with the session-start freshness report,
so they now share one index line, keyed to what that report says (BEHIND or
NOT VERIFIED) rather than to a set being vendored. fresh-check-escalation's
Rule and Detail are carried in full above; its file stays as the record,
`deduplicated` into this one, and its 2026-08-29 incident is in its own
Story.

## Install
No mechanical check: this is a rule about when a session raises drift (immediately at session start, not saved for later) -- a property of session conduct and turn ordering, not of any file this repo's own tree holds. There is no artifact left behind that distinguishes a notice raised early from one raised late.

