---
slug:              todo-2026-09-13-vendor-very-deep-check-into-sets
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       ask
remind_on:         "2026-09-13"
blocked_on:        "four repositories under a different owner, each with its own merge rules. Established 2026-09-13 rather than assumed: `git push --dry-run` to `precedent-individual` returned *\"not in this session's authorized repository set… 403\"*, and `add_repo` with `access: \"push\"` returned *\"cross-tier adds are "
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-13
closed:            null
---
## What

- <a id="vendor-very-deep-check-into-sets"></a>**Vendor
    `very_deep_check.py` into the practice sets, so a set can audit its own
    always-loaded files instead of only gating new ones.** A set carries its
    own `AGENTS.md` — measured 2026-09-11 at 943, 956 and 963 tokens for the
    three team sets — and nothing in the set measures it.

    **The asymmetry, measured 2026-09-13** against
    `precedent-team-writing`'s [tools/ENGINE_MANIFEST.json](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_vendor_engine.py)-written
    manifest: 16 engine files vendored. [tools/precedent_check.py](../tools/precedent_check.py)
    is one of them; [tools/very_deep_check.py](../tools/very_deep_check.py) and
    [tools/verify_harness.py](../tools/verify_harness.py) are not. So the
    duplicate-text check landed the same day reaches a set through
    `precedent_check.py` — once that set's engine is refreshed — while the
    deep-read half, the DUPLICATED report and the costed split table, **can
    never run in a set at all**, however current its engine is. A set can be
    told "this change adds text that already exists"; it cannot be told "your
    always-loaded file is 4,000 tokens and here is what splitting it would
    save".

    **What has to be decided, not just done.** Vendoring `very_deep_check.py`
    changes what every practice set contains, and it pulls its dependencies
    with it — the deep check imports `precedent_check`, `build_views` and
    `precedent_resolve`, reaches the GitHub API for the repo-visibility pass,
    and its LIVE SESSIONS sweep asks the harness for a session list. Some of
    that is meaningless in a set. The real question is whether a set gets the
    whole tool or a named subset (SESSION LOAD and the gotcha passes, say),
    and that is a design call about what a set is for.

    **Blocked on / out of scope:** four repositories under a different owner,
    each with its own merge rules. Established 2026-09-13 rather than assumed:
    `git push --dry-run` to `precedent-individual` returned *"not in this
    session's authorized repository set… 403"*, and `add_repo` with
    `access: "push"` returned *"cross-tier adds are not supported in v1"*. A
    session rooted in each set does the landing; this one cannot.

    Raised by Morgan 2026-09-13 after asking whether the new duplicate check
    had reached the sets. The recommendation to queue rather than do it that
    night was the session's, and he took it, so this is `strength: assented`
    on the timing — the item's substance is his question, not the session's
    proposal.

    **What the reminder is for**, so a session months from now can raise it
    usefully rather than reading the title aloud: the undecided part is
    **whether a set gets the whole deep check or a named subset** (SESSION LOAD
    and the gotcha passes, say). Vendoring the whole tool drags dependencies
    that are meaningless in a set — the GitHub API call for the
    repository-visibility pass, the harness session list for LIVE SESSIONS.
    That is the question to put to him; the landing itself is four sessions'
    work in four repositories, and cheap once the shape is decided.

    **DECIDED 2026-09-14: the whole check, not a named subset.** Morgan, in
    his own words, asked which and answered *"the whole thing"*.
    **Strength:** decided (2026-09-14, Morgan). The `**Remind:**` line that
    carried this is removed because it has fired and been answered; what is
    left is landing work in four repositories this session cannot push to.
    **Disposition:** ask (2026-09-13, Morgan)

## How It Closes

Not open until: four repositories under a different owner, each with its own merge rules. Established 2026-09-13 rather than assumed: `git push --dry-run` to `precedent-individual` returned *"not in this session's authorized repository set… 403"*, and `add_repo` with `access: "push"` returned *"cross-tier adds are 

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
