---
slug:              todo-2026-09-22-ported-identity-checks-have-no-planted-harness-cases
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-22
closed:            null
---
## What

- <a id="ported-identity-checks-have-no-planted-harness-cases"></a>**`tools/checks/check_commit_author.py` and
    `check_buenos_aires_dates.py`, ported to this repo from
    precedent-individual (commit `9d16b6a`) to back a new push-time
    identity gate, have no planted-violation case in
    `tools/verify_harness.py`'s own test suite.** `verify_harness.py --as-ci`
    reports it directly: "every registered check has a planted case here
    (untested: ['check_buenos_aires_dates', 'check_commit_author'])".

    Both scripts were verified BEHAVIORALLY instead, in throwaway clones,
    the same session they were added: a bot-authored/wrong-offset commit
    is flagged before it reaches a remote, silently drops out of scope
    once a remote-tracking ref reaches it, and
    `PRECEDENT_CHECK_FULL_HISTORY=1` still catches it either way; the
    push-gate denies a bad push and allows a clean one. That is real
    evidence the mechanism works, but it is not the same guarantee as a
    planted case living in the harness's own suite, checked on every
    future change the way every other registered check here already is.

    Deferred rather than closed the same session: the existing planted
    cases in this harness are a substantial, carefully-built body of work
    (throwaway git fixtures, negative controls, exact-message assertions)
    and matching that bar for two scripts was judged bigger than this
    session's remaining scope, with the git-identity fix Morgan asked for
    already the far larger piece of the turn.

## How It Closes

`verify_harness.py --as-ci`'s heavy shard reports zero untested registered
checks, with a real planted-violation case (and a planted clean case) for
each of `check_commit_author` and `check_buenos_aires_dates`.

## Notes

2026-09-22: filed the same session that ported the two scripts and their
push-gate, on the finding named above.
