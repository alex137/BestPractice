---
slug:              todo-2026-09-14-source-set-push-triggers
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "four repositories under a different owner. Established 2026-09-14 rather than assumed — `git push` returned *\"access denied by the git proxy: … is not in this session's authorized repository set\"*, and `add_repo` with `access: \"push\"` returned *\"cross-tier adds are not supported in v1: … session alr"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="source-set-push-triggers"></a>**The four practice sets still run
    their checks on `pull_request` only, so a direct push to one runs
    nothing.** Upstream's half landed 2026-09-14 in
    [PR #313](https://github.com/alex137/BestPractice/pull/313):
    [templates/github-actions/precedent-check.yml.template](../templates/github-actions/precedent-check.yml.template)
    and templates/github-actions/views-drift.yml.template (a job inside
    precedent-check.yml.template since 2026-09-19)
    now carry `push:` with no branch filter, so a set bootstrapped or
    refreshed from here on gets it. **The installed copies in the four
    existing sets do not**, and a refresh does not rewrite a workflow it did
    not just install.

    **What is wrong, measured 2026-09-14** by reading each set's own
    `.github/workflows/`: `precedent-check.yml` and `views-drift.yml` are
    wired to `pull_request:` alone in all four of `precedent-individual`,
    `precedent-team-repo-maintenance`, `precedent-team-writing` and
    `precedent-team-working-style`. Work lands in a private single-owner set
    by a session committing and pushing straight to a branch — there is
    usually no pull request at all — so both gates have existed and never
    fired once. **A green set and an unchecked set look identical**, which is
    the same failure shape `views-drift.yml`'s own header records for the
    generated views.

    `precedent-individual`'s `commit-identity.yml` is the sharp case and
    wants BOTH events rather than a swap. Its `pull_request` run is the
    moment its header argues for — after the commit exists, before it is
    permanent, while a bad identity can still be amended instead of
    grandfathered. A `push` run cannot gate, but it is the only thing that
    would ever see the path that produced every grandfathered entry in
    `identity.json`: a commit straight onto the branch, permanent the moment
    it lands.

    **Blocked on / out of scope:** four repositories under a different owner.
    Established 2026-09-14 rather than assumed — `git push` returned *"access
    denied by the git proxy: … is not in this session's authorized repository
    set"*, and `add_repo` with `access: "push"` returned *"cross-tier adds are
    not supported in v1: … session already has repos from owner(s)
    [alex137]"*. Waking or spawning a session that can reach them was refused
    too, by the permission classifier rather than by the repository wall, so
    the handoff went to Morgan as a paste block instead.

    Morgan authorized the work itself on 2026-09-14, where BestPractice (BP)
    is this repository: *"in addition to doing this on our BP branch, I think
    we should do this on all practice level files individual etc. Go
    merge."*
    `strength: decided` — he asked for it in his own words rather than
    accepting a proposal. Nothing here is waiting on a decision; it is
    waiting on a session that can push.

## How It Closes

Not open until: four repositories under a different owner. Established 2026-09-14 rather than assumed — `git push` returned *"access denied by the git proxy: … is not in this session's authorized repository set"*, and `add_repo` with `access: "push"` returned *"cross-tier adds are not supported in v1: … session alr

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
