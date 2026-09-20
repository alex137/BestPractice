---
slug:              todo-2026-09-11-contributor-access
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "a real person and repo for the rest of it, and Morgan adding the GitHub collaborator role and branch protection by hand (no tool in this repo's GitHub toolset creates a collaborator invite or a protection rule)."
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan"
noted:             2026-09-11
closed:            null
---
## What

- <a id="contributor-access"></a>**Run the contributor-access plan for real.**
    [spec/CONTRIBUTOR_ACCESS.md](../spec/CONTRIBUTOR_ACCESS.md)
    is drafted but not executed — it doubles as item 9's neighbor,
    [spec/PHASE6_BRIEF.md](../spec/PHASE6_BRIEF.md)'s still-open item 4 (the
    first end-to-end rehearsal of INSTALL.md §0). **Rewritten 2026-09-11**
    on Morgan's line — content is any contributor's, protected paths need an
    owner's review, practices are suggested by anyone and landed by an
    approver — replacing a Triage/Read model that denied the contributor
    every write, documents included.

    **Three of its platform assumptions are unverified and are the cheapest
    thing to settle first**, ahead of any real person: whether a code-owner
    review requirement leaves a documents-only pull request mergeable by its
    author, whether branch protection is available on the plan the repo sits
    under, and whether the person authenticates to GitHub as themselves. The
    first one decides whether the design works at all. **Blocked on:** a real
    person and repo for the rest of it, and Morgan adding the GitHub
    collaborator role and branch protection by hand (no tool in this repo's
    GitHub toolset creates a collaborator invite or a protection rule).

    **Reviewed 2026-09-14**, on Morgan's ask, and the plan now carries a
    "Review, 2026-09-14" section with seven ranked findings and the
    define/manage/limit/control framing (`strength: assented` — the session's
    findings, his instruction to write them up). The two that change the
    design rather than test it: `MAP.md` is owned while
    [orientation-map](../practices/orientation-map.md) makes every
    add-a-document pull request touch it (item
    `generated-views-are-owned-paths`),
    and `CODEOWNERS` gates the merge but not the run of an edited workflow
    (item [`workflow-run-is-not-gated`](#workflow-run-is-not-gated)). The
    rest are items 109–112 below. **Disposition:** wait — the three
    assumptions are still the first thing to settle, and Morgan opened a
    throwaway repository under his own account for exactly that on 2026-09-14; the
    measurement runs in
    [a session seeded there](https://claude.ai/code/session_01DqP5TjkampkhpW3DEvVi7Z)
    (this session cannot attach a repo under another owner, and
    docs.github.com is blocked by the proxy), and its `RESULTS.md` is what
    closes the three assumptions. **Built the same day, on "build what's
    needed"** (`strength: assented`): the boundary check, the owned-paths
    preview, the project mode of the CODEOWNERS generator, the `register`
    placeholder, and the reworded guides — items 108, 110, 111 (half) and
    112 below record each. Still open here: the assumptions, and the pilot.
    **Documented and audited, same day**: INSTALL.md §0 step 10,
    PER_MACHINE_SETUP.md's token row, SETUP.md's adding-a-person bullet,
    FOR_DEVELOPERS.md's "Who May Change What", and the very deep check's
    `CONTRIBUTOR BOUNDARY` section (pass 2, question 16), which reads the
    generated file against its registry and the protection setting against
    the plan on every run. **Plus, on Morgan's follow-up the same day**:
    [documentation/GITHUB_SETTINGS.md](../documentation/GITHUB_SETTINGS.md),
    the GitHub side in one place — roles, the owner-only settings, branch
    protection with the four values, what GitHub does with CODEOWNERS and
    how this system generates it, Actions permissions and secrets, the
    practice-set repositories — linked from every install path and guide.

## How It Closes

Not open until: a real person and repo for the rest of it, and Morgan adding the GitHub collaborator role and branch protection by hand (no tool in this repo's GitHub toolset creates a collaborator invite or a protection rule).

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
