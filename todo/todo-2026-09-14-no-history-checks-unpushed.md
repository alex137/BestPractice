---
slug:              todo-2026-09-14-no-history-checks-unpushed
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       parked
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="no-history-checks-unpushed"></a>**Two individual-set checks crashed
    on a repo with no commits. CLOSED 2026-09-14 — they skip it now, saying
    there is no history yet.** `tools/checks/check_commit_author.py` and
    `tools/checks/check_buenos_aires_dates.py` called `git log` with
    `check=True`. An unborn HEAD makes git log exit 128, the
    `CalledProcessError` escaped `find_violations()`, and
    [tools/precedent_check.py](../tools/precedent_check.py) printed the traceback
    as a VIOLATION of the practice itself. **A fresh install is exactly a repo
    with no commits**, so every [INSTALL.md](../INSTALL.md) §0 install hit both,
    and it is invisible from inside a practice set, which has years of
    history. Reported from the first real §0 install into a project with
    subject matter of its own, 2026-09-14.

    **What unblocked it** is the one thing it was waiting on: a session rooted
    in the individual set. The git proxy refuses to inject a credential across
    owners and `add_repo` refused the cross-owner add, so nothing rooted here
    could ever push the fix — it had to be pushed from there, and on
    2026-09-14 it was, as that set's pull request #130, *"A repository with no
    commits skips these two checks instead of crashing"*, merged at `519d20f`
    over `68da995`. The set is private, so there is no link to give.

    **What landed.** Both files read the log through a `_git_log_lines()`
    helper that drops `check=True` and, on a non-zero git exit, raises the
    file's own `NotApplicable` — SKIPPED, exit 2: *"this repository has no
    commits yet"* when `git rev-parse --verify --quiet HEAD` fails, *"not a
    git repository"* when `rev-parse --git-dir` fails, and otherwise git's own
    stderr. **`--git-dir` is probed first**, because a directory that is not a
    repository fails the HEAD probe too and would otherwise be told the wrong
    cause. The helper is **duplicated verbatim in both files**, for the reason
    those files already give at length: `precedent_materialize.py` copies only
    the `check_*.py` scripts a practice's `checked_by:` claims, so a shared
    helper module sitting beside them would never travel into a consuming
    repo.

    **Both suites got the two-direction case**, against a repository built
    from nothing (`git init`) rather than a clone — a clone of that set
    carries years of history and can never reach the condition. The empty repo
    must exit 2 **and** the message must say "no commits yet" (exit 2 alone
    would pass against a skip for the wrong reason — a repo declaring no
    identity skips too); then the same fixture, once it carries one commit by
    the declared person (name, email and zone read from the fixture's own
    `identity.json` rather than written out a second time), must run **clean**
    rather than stay skipped forever. Reproduced before and after rather than
    reasoned about: an empty `git init` repo printed the `CalledProcessError`
    traceback before the change and prints `SKIPPED: this repository has no
    commits yet ...` after it. Both suites are green, that set's
    `tools/checks/tests/run_all.sh` exits 0, and its `precedent_check.py`
    reports 17 passed, 0 violated, 0 errored.

    So this item's own closing condition — a fresh repo (`git init`, nothing
    committed) runs both checks and gets SKIPPED rather than a traceback — is
    met. **The sibling item is not:**
    [`close-detect-declaration-unpushed`](todo-2026-09-14-close-detect-declaration-unpushed.md)
    hit the same cross-owner wall, is a different fix, and stays open.

    **Disposition:** parked (2026-09-14, closed as done)

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
