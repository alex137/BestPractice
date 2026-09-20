---
slug:              todo-2026-09-11-source-name-check-cannot-run-in-a-hosted-session
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "the harness's per-repository API gating, which this repository does not control, and a decision between those three shapes."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-11
closed:            null
---
## What

- <a id="source-name-check-cannot-run-in-a-hosted-session"></a>**The
    source-name check reports UNVERIFIED for every private source in a hosted
    session, which is where most vendor updates happen.**
    [tools/precedent_source_names.py](../tools/precedent_source_names.py) asks
    the GitHub API for each declared source repository's current `full_name`,
    because no git operation can answer it —
    [vendor-update-runbook](../practices/vendor-update-runbook.md)'s step 8.
    Measured on this container, 2026-09-11, with a valid
    `PRECEDENT_GIT_TOKEN` set and all four sources cloned and current:
    **four UNVERIFIED, zero checked.** `api.github.com` answers **403** with a
    body naming `add_repo` for every repository the session has not attached,
    and that answer comes from the harness's own egress policy, before
    GitHub sees the token. The credential is not the obstacle and setting a
    better one will not help.
    So the check is honest and, in this environment, inert. It runs where the
    API is reachable: a person's own machine with a personal access token, a
    CI job with one, or a hosted session for a repository it has attached —
    and the mechanism was proven end to end against
    `alex137/bestpractice`, the one repository this session could query.
    **What is not yet designed** is the route that makes step 8 answer
    something in a hosted session. Candidates, none measured: `add_repo` with
    `access: "push"` for each source at session start (which the cross-owner
    refusal recorded in [AGENTS.md](../AGENTS.md)'s gotchas may simply refuse);
    a scheduled workflow in each source repository that writes its own current
    name somewhere a consumer can read without the API; or accepting that this
    is a check for the machine and CI, and saying so in the runbook rather
    than leaving a reader to discover four UNVERIFIED rows.
    **Blocked on / out of scope:** the harness's per-repository API gating,
    which this repository does not control, and a decision between those three
    shapes. **Disposition:** wait (2026-09-11 — a session filed this; nobody
    has set it to `ask`)

## How It Closes

Not open until: the harness's per-repository API gating, which this repository does not control, and a decision between those three shapes.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
