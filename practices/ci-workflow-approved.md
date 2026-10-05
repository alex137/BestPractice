---
slug:        ci-workflow-approved
title:       A workflow file runs only with the person's approval, pinned to its content
tier:        on-demand
severity:    default
applies_to:  [".github/workflows/**"]
applies_to_why: "Its own applies_to. The moment it matters is a session about to add or edit a workflow file, which is exactly the glob; the push gate runs the check whatever the path channel did, so a miss here costs a refused push, not a billed run. Decided: 2026-09-25, when the practice landed."
occasion:    "a .github/workflows file is added, edited, or found in an update or migration"
gates:       ["push"]
gates_why:   "The push check refuses a workflow file without the person's recorded approval, and workflow-write-gate.sh refuses one written through the GitHub tools before it lands, so a session that never saw the rule is stopped before a billed run. index_required: false records that judgment: Morgan, 2026-10-01 (\"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)\", strength: assented -- one yes over a batch; corrected 2026-10-05)."
index_clause: "no new workflow or CI minutes without the person's words; a fix is maintenance"
index_required: false
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
visible_to:  code-owners
supersedes:  []
overrides:   null
added:       "2026-09-25"
approved_by: "Morgan, 2026-09-25 (\"we need to absolutely put a hard stop to this ever happening again ... It's a priority\", strength: decided); index line dropped: Morgan, 2026-10-01 (\"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)\", strength: assented -- one yes over a batch; corrected 2026-10-05)"
---
## Rule
**A session never adds a GitHub Actions workflow, or adds CI work to one,
on its own judgment**: no new workflow, job or trigger, nothing that makes
one run more often or longer. **That is what this rule guards: billed
minutes.** A change that adds no CI work -- a broken path, a dead fallback,
a stale message, in a workflow or in a template one is written from -- is
ordinary maintenance: make it, the way you would fix any other file.
**Where this rule seems to stand in the way of what is plainly right, ask
the person, with your recommendation; never leave a workflow broken because
of it** (Morgan, 2026-09-30: "We clearly shouldn't have broken workflows
because I once said to not edit a file! Ask!").

Every `.github/workflows/*.yml` file in a repo that
vendors Precedent is either the engine's own untouched copy, or carries the
person's approval in `precedent.json`'s `github_ci_approved`, **pinned to
the file's exact content by sha256**, with their words quoted:

```json
"github_ci_approved": {
  ".github/workflows/<name>.yml": {
    "sha256": "<sha256 of the file>",
    "approved_by": "<Name>, <YYYY-MM-DD>: \"<their words>\""
  }
}
```

**Any edit changes the hash and fails the check until the person approves
the new content.** That includes a new trigger, a new job, or a trigger put
back that someone removed. For a fix that adds no CI work to a file they
approved, make the fix, then show it and ask for the new approval, saying it
adds no minutes. A workflow the engine owns needs no approval to fix: fix
its template, and the next refresh carries the fix. To get approval, show the person the file and say
when it will run: every run bills at least a minute in a private repository.
Then record what they said, in their words. **Never write an approval they
did not give.** If they do not want the file, delete it.

**In a consuming repo or a practice set, Update Vendors settles a leftover
without asking** (a consumer since 2026-09-27, a practice set since
2026-10-01, which ships no workflow at all: practice
`source-sets-run-no-ci`). The engine owns the workflows upstream ships
(`leak-gate.yml`, `light-check.yml`): each refresh writes them from the
template over any hand edit, and removes every other workflow that has no
approval in the person's own words. **First it checks that nothing needed is
lost:** a file that runs something the local push check does not (a script, a
test runner, a third-party action) is left alone, and flagged loudly: a
banner in the update's output, a "Left for you" line naming what to move into
the local check, and an open item in the repo's `todo/`. A declaration under
`local_ci_workflows` no longer keeps a consumer's workflow; only the person's
approval does (Morgan, 2026-09-27: "I support if everything's already
covered, deleting it. If there is something that is not covered, leave it
alone, but flag it importantly"). So a consumer's finding here means the
refresh has not run since the file changed, or could not touch it (untracked,
or uncommitted edits). The answer is to run Update Vendors, not to ask the
person. **Asking about a leftover whose work runs locally is the failure
here.** Morgan, 2026-09-27 (strength: decided): *"Asking creates doubt and
confusion when there isn't any."* **Asking about one that would stop
something running is required** (2026-10-01: *"Ask if genuinely in
doubt"*): the session says in plain words what the file does and what would
stop, recommends, and asks keep or delete. A keep is recorded as their
approval, which is what keeps a workflow they actually want.

**This check runs on every push** (the push gate's basic tier, seconds), in
every full check, and at every Update Vendors and migration. **It also
judges growth everywhere, this repo's own templates included:** a change
that makes a workflow or a workflow template run more (a new event, branch,
type, path, schedule or job, or a narrowing filter dropped) is refused until
the person's words are pinned to its content in `github_ci_approved`; a fix
that adds no CI work passes. A workflow
written from a shipped template is tracked in `ENGINE_MANIFEST.json`, which
is what the check reads for it, so it needs no approval entry.
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

**2026-09-27, the same repository, on its next Update Vendors.** Its
hand-made `light-check.yml` still ran on every push to `main` and on every
pull request, re-running [doc_lint.py](../tools/doc_lint.py) and its own light check, both of which
its local push check already ran. The update left the file alone, because the
light check was written at install and never refreshed. This check then
blocked every push with "show the person the file and ask", and the session
had to ask. Morgan's answer was that there was nothing to ask: *"the point of
the yml changes is to stop these extra needless (often hand edited) yml files
from running, that's why we now run the checks locally etc so it shouldn't
ask."* The session fixed that one repository by hand. The engine now owns the
light check, and a consumer's refresh replaces a hand-made copy and removes
an unapproved workflow on its own.

**Off the occasion index from 2026-10-01** (`index_required: false`). The reduction pass for precedent-individual's session-start file ([the session-file open item](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-09-30-session-file-cut-to-4000.md)) counted this among the lines a mechanical check already refuses at push: the push check refuses an unapproved workflow, and `workflow-write-gate.sh` refuses a write through the GitHub tools. Its path and push gate still reach it. Morgan approved (strength: decided): *"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)"*

## Install
Enforced by `_ci_workflow_approved` in
[tools/precedent_check.py](../tools/precedent_check.py), run by
[tools/precedent_push_check.py](../tools/precedent_push_check.py) as
`ci_workflows` in the basic tier, so it runs before every push a session
makes. It binds any repo that keeps a `.github/workflows/` directory
(`binds_when`), whether or not the practice text resolved there, and reports
"not applicable" in BestPractice itself, which has no engine manifest.
In a consuming repo the refresh in
[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)
does the settling: `_refresh_ci_workflow_files` writes the shipped
workflows from their templates, and `_remove_unapproved_workflows` removes
the rest (`CI_CONVERGES_KINDS`).

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
