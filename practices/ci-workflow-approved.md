---
slug:        ci-workflow-approved
title:       A workflow file runs only with the person's approval, pinned to its content
tier:        on-demand
severity:    default
applies_to:  [".github/workflows/**"]
occasion:    "a .github/workflows file is added, edited, or found in an update or migration"
gates:       ["push"]
index_clause: "no workflow added or edited without the person's words, hash-pinned"
index_required: true
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-25"
approved_by: "Morgan, 2026-09-25 (\"we need to absolutely put a hard stop to this ever happening again ... It's a priority\", strength: decided)"
---
## Rule
**A session never adds a GitHub Actions workflow, or changes when one runs,
on its own judgment.** Every `.github/workflows/*.yml` file in a repo that
vendors Precedent is either the engine's own untouched copy, or carries the
person's approval in `precedent.json`'s `github_ci_approved`, **pinned to
the file's exact content by sha256**, with their words quoted:

```json
"github_ci_approved": {
  ".github/workflows/light-check.yml": {
    "sha256": "<sha256 of the file>",
    "approved_by": "Morgan, 2026-09-25: \"Please stop it running every time\""
  }
}
```

**Any edit changes the hash and fails the check until the person approves
the new content.** That includes a new trigger, a new job, or a trigger put
back that someone removed. To get approval, show the person the file and say
when it will run: every run bills at least a minute in a private repository.
Then record what they said, in their words. **Never write an approval they
did not give.** If they do not want the file, delete it.

**This check runs on every push** (the push gate's basic tier, seconds), in
every full check, and at every Update Vendors and migration. A file
[`precedent_install.py`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_install.py) writes straight from a shipped template is approved
by the install, and names the template instead of quoting anyone.
Re-baselining an edited engine workflow with `record-ci` is an approval
too, and needs the same words.

## Why
Cost follows the trigger, and the trigger is one line. A session tuning a
workflow sees a good reason for that line in front of it. It does not see the
bill, or the session that removed the same line a week earlier for a reason
it never read. Advice did not stop it:
[workflow-file-outside-vendoring](workflow-file-outside-vendoring.md)
flagged exactly this file on every run, as advisory, and nobody acted.

## Story
**2026-09-25, a private consuming repo.** Morgan's usage export showed 11
billed minutes there on a day he expected close to none. All 11 were `push`
runs on `main` of the repo's own `light-check.yml`: one per merged pull request,
re-checking a tree that had already been checked. The pull-request runs were
already being skipped by the working-branch `[skip ci]`. But GitHub writes
the merge commit, and a merge commit carries no `[skip ci]`.

The file's history is the case for this rule:

- **2026-08-28:** installed with the personal pack, on pull request and on
  push to `main`.
- **2026-09-15:** a session removed the push trigger, because it doubled
  every merged pull request's cost.
- **2026-09-20:** another session deleted the file over its cost, and the
  deletion was reverted the same night: it was a live, required check.
- **2026-09-21:** a third session put the push trigger back while folding
  the doc lint into it. It copied BestPractice's own docs.yml shape.
  BestPractice is public, so GitHub bills it nothing. The same shape costs
  real money in a private repo.
- **2026-09-25:** one billed minute per merge, until the trigger came off
  again.

Every step was reasonable where it was made, and each session decided alone
about something that spends Morgan's money. His words when he saw it: "it
should NOT be doing that!!!! ... how do we stop future session from just
adding their own files like this and doing things like this that get out of
control? It's a priority."

## Install
Enforced by `_ci_workflow_approved` in
[tools/precedent_check.py](../tools/precedent_check.py), run by
[tools/precedent_push_check.py](../tools/precedent_push_check.py) as
`ci_workflows` in the basic tier, so it runs before every push a session
makes. It binds any repo that keeps a `.github/workflows/` directory
(`binds_when`), whether or not the practice text resolved there, and reports
"not applicable" in BestPractice itself, which has no engine manifest.

**What the push check cannot see, and what covers it** (2026-09-26):

- **A session writing a workflow straight onto GitHub** with a file-write
  tool never passes a push. `workflow-write-gate.sh` refuses that call
  before it runs and sends the session to a clone and a push
  ([templates/harness/claude-code/hooks/workflow-write-gate.sh](https://github.com/alex137/BestPractice/blob/staging/templates/harness/claude-code/hooks/workflow-write-gate.sh)).
  It guards Claude Code sessions only.
- **A workflow edited on GitHub's website, or written by anything the
  guard above does not cover,** is caught next time a session opens the
  repo: every session start runs the same check on the fresh clone and
  prints a loud warning
  ([templates/bootstrap.sh](https://github.com/alex137/BestPractice/blob/staging/templates/bootstrap.sh)),
  so it is named before the first piece of work.
- **A workflow on a side branch, one GitHub ran that is no longer on the
  default branch, a schedule, or a repo that is not a Precedent install**
  is visible only to GitHub.
  [tools/ci_fleet_audit.py](https://github.com/alex137/BestPractice/blob/staging/tools/ci_fleet_audit.py)
  asks GitHub about every branch of every repo it can reach, and the very
  deep check runs it (item 22). Its report stays in the session.
- **Whether a quote is genuine** is beyond any check. An invented one is
  written down where a reader will see it.
