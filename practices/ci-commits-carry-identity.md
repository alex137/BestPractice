---
slug:        ci-commits-carry-identity
title:       A workflow that commits resolves a person, or refuses
tier:        on-demand
severity:    default
applies_to:  [".github/workflows/**", "templates/github-actions/**"]
occasion:    "adding or editing a CI workflow that commits, pushes, or opens a pull request"
gates:       []
index_clause: "a committing workflow reads a declared identity, or refuses -- never the bot"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-10"
approved_by: "Morgan"
strength:    assented
source_practice_number: null
---
## Rule
**A workflow that commits resolves the author from a declaration, and
refuses the run when it cannot.** Read `name`, `email` and `timezone` from
the identity the repository already declares — an `identity.json`, or an
explicit `PRECEDENT_COMMIT_*` — and **exit non-zero if any of the three is
missing.**

**Hardcoding `github-actions[bot]`, or falling back to it, is the failure
this rule exists to prevent** — not a lesser version of following it. So is
committing on the runner's clock, which is UTC and cannot be told from a
real offset ([timestamps-carry-offset](timestamps-carry-offset.md)).

## Detail
**Why a workflow has to do this itself.** The commit-identity hook resolves
whoever is running a session and installs a `pre-commit` backstop refusing
the container's bot account. It runs at **session start, in an agent's
session**. A GitHub Actions runner never runs it, and nothing on the runner
does. So the one place a repository's identity discipline is guaranteed
absent is the one place that commits unattended, on a schedule, with nobody
reading the output.

**Refusing beats falling back, and that is the whole of it.** A workflow
that cannot find an identity has two options: stop, or author the commit as
something. The second produces a commit that looks fine until something
checks it — and by then there are dozens, on a weekly schedule, in a history
nobody wants to rewrite ([no-rewrite-for-warnings](no-rewrite-for-warnings.md)).
A refused run is one red check and a five-minute fix.

**Where the declaration lives depends on the repository, and copying the
wrong one refuses every run.** An `identity.json` at a repo's root *means*
"this repository is somebody's individual practice source" — so an
individual set reads its own, and a **shared team set must not have one to
read**. There the declaration is `PRECEDENT_COMMIT_NAME` / `_EMAIL` / `_TZ`,
set as repository variables and read the same way. Porting an individual
set's workflow verbatim into a team set produces a workflow that refuses on
every run with the only fix forbidden — the same trap `check_commit_author.py`
fell into, rebuilt inside a workflow. Found 2026-09-10, porting exactly that
fix between two real sets.

**A commit that is genuinely nobody's** — a throwaway fixture, a scratch
repository — is the documented exception the backstop already carries, and it
says so by name with `PRECEDENT_ALLOW_ANY_AUTHOR`. Anything a workflow pushes
to a real branch is somebody's.

**What the check reads, and what it cannot.** `ci-commits-carry-identity` in
[tools/precedent_check.py](../tools/precedent_check.py) looks at every
`.github/workflows/*.yml` that commits, and fires when one names a bot
account or configures a git identity without reading a declared one. It
cannot tell whether the identity a workflow *does* read is the right person,
and it does not look inside an action a workflow calls — a `uses:` step that
commits on your behalf is outside its reach, and outside this rule's only by
accident. Prefer a step you can read.

## Why
The failure is silent by construction. A scheduled workflow commits when
nobody is watching, and a bot-authored commit is indistinguishable from a
correct one until a check looks — so the wrongness accumulates at whatever
rate the schedule runs.

## Story
**A weekly workflow had mis-authored every commit it ever made, and the two
checks that would have caught it were switched off by an unrelated bug.**
Found 2026-09-10 in a real practice set, whose engine-refresh workflow
hardcoded `github-actions[bot]` and committed on the runner's UTC clock —
tripping both `commit-author` and the timezone rule at once, every run.

**Nobody had seen it because those two checks were reporting SKIPPED.** They
resolved identity through a module a practice set did not vendor, so inside
the set that owned the workflow they could not run at all. The day that was
fixed and the checks went live, the workflow's own commit was the first thing
they flagged.

**Two silent failures were holding each other up**, and that is the part
worth carrying past this incident: *a check that cannot run is not evidence
that what it checks is fine.* The repository had every rule it needed and
neither of the two mechanisms that would have shown the breach.

A second set was found running the same workflow, unfixed, in the same pass
— which is why this is a practice with a check rather than a note in the
repository where it was first found.

## Install
Nothing to configure — the check runs wherever the engine is vendored, and a
repository with no committing workflow reports NOT APPLICABLE rather than
passing vacuously.

For the workflow itself: resolve the three values in a step of its own,
before any `git commit`, and `exit 1` on a missing one. The limit this
enforces is written up for adopters in
[GITHUB_ACTIONS.md](../GITHUB_ACTIONS.md)'s "Limits".
