---
slug:            gotcha-2026-11-01-opened-above-its-repos-the-freshness-guard-moved-a-source-clone-off-main
status:          live
noted:           2026-11-01
severity:        notable
retired:         null
retires_when:    every practice set and consumer has refreshed its vendored freshness-guard.sh, precedent_run_repo_hooks.py and precedent_run_session_hooks.py past the commit that passes PRECEDENT_SESSION_ROOT
---
## Symptom

In a session opened above its repositories (`/home/user`), the first tool
call is refused:

> BLOCKED by freshness-guard (first tool call of this session): 'main' is
> missing 4 commit(s) from origin/staging

It names no checkout, and every clone in the folder is on `main`. Following
its remedy moves BestPractice onto a branch cut from `origin/staging`, and
from then on the push and Stop gates say the guarantee "each practice source
clone is current with its own origin" is NOT in effect: "1 commit(s) behind
origin/main ... checked out off main".

The remedy cannot be run as printed either. Its
`$(python3 tools/precedent_branch_name.py ...)` is relative and does not
resolve from the parent folder, and `cd <repo> && git switch ...` is refused
because only a command that starts with `git` counted as git. Only
`git -C <repo> switch ... <literal name>` got through.

## Story

2026-11-01, an Update Vendors run over three practice sets, opened above
BestPractice and the three set clones. The user-level hook switchboard,
[precedent_run_repo_hooks.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_run_repo_hooks.py)
(2026-10-19), runs the hooks of the repository an action is about with
`CLAUDE_PROJECT_DIR` set to that repository. A call about BestPractice ran
its freshness guard with BestPractice as the project, so the base was its
own landing branch, `staging`. But in that session BestPractice was not
being worked on. It was the universal source, read at `main`, where
[precedent_session_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_session_check.py)
holds it. Two parts each thought they owned where the clone sits, and they
disagreed. [precedent_update.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_update.py) then had to run main's code from a
temporary checkout.

This is an earlier fight coming back by a new path. The
[2026-09-26 trap](gotcha-2026-09-26-the-freshness-guard-held-attached-source-clones-to-pre-stagin.md)
was fixed by letting an attached repository's declared base win over the
landing branch. That fix covers repositories the guard checks as attached.
It never reached a source clone that the switchboard, built three weeks
later, hands to the guard as the project itself.

## Fix

The session check owns where a source clone sits: on the branch its
consumers read it at. Both switchboards now pass `PRECEDENT_SESSION_ROOT`,
the folder the session was really opened in. With it set, and different
from the checkout, [freshness-guard.sh](https://github.com/alex137/BestPractice/blob/staging/tools/freshness-guard.sh)
leaves a tier branch that is current with its own origin alone. It does not
block it or move it, and its note says where a write into that repository
belongs. A write on a tier never reaches origin anyway, because the push
gate refuses a push to one. Every block in that kind of session names its
checkout. Remedies are `git -C <path> ...` with a literal branch name from
the naming tool, and `cd <path> && git ...` counts as a git command.
Asserted in `check_freshness_guard_leaves_a_source_on_its_tier_when_opened_above`.
A session rooted in the repository is unchanged; that is the test's control.
