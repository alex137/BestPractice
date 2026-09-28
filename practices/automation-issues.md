---
slug:        automation-issues
title:       Unattended automation reports its own blockers as a tracked issue
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "an unattended job hits something blocking its normal work, or something optional it cannot reach"
gates:       []
index_clause: "a blocked job files or updates an issue; skip an optional input, never silently"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-28"
approved_by: "pending PR review -- moved 2026-09-28 from the shared set precedent-shared-repo-maintenance, Morgan F accepting the session's recommendation to move it (the move: strength assented); the rule itself: Morgan F, migrated from RepoPersonalPreferences by the private-set migration session"
---
## Rule
Any unattended job -- whatever a team's own automation adds -- that hits something blocking it from finishing its normal work (a missing or revoked credential, an unexpected failure) reports that blocker by opening or updating a tracked issue, not only a CI annotation or a job-summary line. Keep the annotation too -- it's free and some readers will still see it -- but treat it as a backup, not the primary channel.

**Where the blocker is an OPTIONAL input the job can proceed without -- a credential for a private source it would have consulted, a step that only applies to some repositories -- the job skips that work and reports, rather than failing the run.** A hard failure there blocks an otherwise successful run over something nobody has to act on today. **What makes the skip safe is the report**, and only the report: a silent skip and a run that is genuinely working are indistinguishable from the outside, so a job that skips without opening the issue has chosen the worst of both. Skip and report, never skip quietly, never fail loudly over an optional input.

## Detail
Idempotent by design: one open issue per blocker, not one per run -- a second occurrence of the same blocker comments on the existing open issue (with a "recurred: `<date>`" stamp) instead of opening a duplicate, so a blocker that fires every week for months reads as one ongoing problem with a comment thread, not fifty separate issues. Fails gracefully if the reporting mechanism itself can't reach the host or authenticate: prints a warning, exits cleanly, never turns a failure to report a blocker into a second, more confusing blocker.

## Why
A CI annotation lives inside one workflow run; nobody sees it unless they already know to go check that run. A tracked issue persists in the repo itself and rides the host's own notification system for free.

## Story
Migrated here from RepoPersonalPreferences by the phase-3 private-set
migration; the Story is backfilled from that pack's own text, which recorded
a reason rather than a single incident.

The reason is a property of where an Actions annotation lives: it exists
inside one workflow run, so nobody sees it unless they already know to go
open that run. A blocker reported only that way is reported to nobody. A
tracked issue persists in the repo, appears in the ordinary issues list, and
rides the host's own notification system for free -- no notification
infrastructure to build and no new secret to manage, which is what makes the
stronger channel cheap enough to be the default.

The idempotent-by-label design came from the failure mode the fix would
otherwise have created: a blocker that fires every week for months would
open a fresh issue every run and bury the issue list, so a repeat call
comments on the existing open issue with a recurrence stamp instead. Applied
first to the scheduled syncs' missing-credential paths, one of which had
previously been a deliberately silent skip -- the sync still skips, but the
fact that it is skipping stopped being silent.

**Those two syncs were retired on 2026-09-11** (`bestpractice-sync`, then
`pack-sync`, both on Morgan's judgment that an unattended self-merging run
is the wrong bet against a layer this size), and **this rule is now the only
place the skip-and-report half is written down.** It was carried here the
same day rather than left to be inferred: `pack-sync`'s Rule was the one
that said a missing private-source credential skips the update instead of
failing the workflow, and a rule in force must not be readable only through
a retired one -- the same reason `pack-sync`'s own Rule had been rewritten
hours earlier, for the same reason, one rule over.

**What generalised and what did not.** The skip-and-report pair did: it is
about optional inputs and unattended runs, not about syncing, and it applies
to any job with a step some repositories cannot reach. The rest of
`pack-sync` -- comparing a recorded commit against a head, merging through
recorded adaptations, self-merging once checks pass -- did not, and is not
here. It went with the rule, on purpose.

**Moved to the universal catalogue on 2026-09-28**, from the shared set for repository maintenance, on Morgan's accepting a session's recommendation that it, with four others, applies to any repository and not only to maintaining practice sets. His framing of the line, said about one of the four: *"Repo-maintenance is just for things to help maintain the practices etc."* Nothing in the rule itself changed; its Install was rewritten, since it had described the set it lived in rather than the check a repository with such a job could run.

## Install
No mechanical check: both halves are properties of an automation's run history, not of any repository's tree. A repository that runs such a job can check them directly -- does a recurrence comment on the existing open issue rather than opening a duplicate, and does a run missing an optional credential exit clean with an issue raised rather than red or silent -- but that check belongs to the automation, and reads its runs.
