---
slug:              todo-2026-09-06-attach-private-sources
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-06
closed:            null
---
## What

- <a id="attach-private-sources"></a>**Run one session rooted at each private set — this unblocks four other
    items at once.** Established 2026-09-06 by trying it, rather than
    assumed: all three private repos (`themorgan/precedent-team-repo-maintenance`,
    `themorgan/precedent-team-tms`, `themorgan/precedent-individual`) are
    **reachable and pushable** by this account. The blocker is not access. It
    is that `add_repo` refuses a cross-owner add — a session already holding
    `alex137/*` cannot attach a `themorgan/*` repo ("cross-tier adds are not
    supported in v1"). So the unblock is simply **a session whose initial
    source is the private repo** — or, since 2026-09-10, a session with
    `PRECEDENT_GIT_TOKEN` on its environment, which clones every private
    source at session start with no `add_repo` call at all
    ([PER_MACHINE_SETUP.md](../documentation/PER_MACHINE_SETUP.md)). That route is verified working and is the
    cheaper one; this item's remaining work is the per-set commands below,
    which still need a session that can PUSH to each set. BestPractice itself is public, so that
    session can `git clone https://github.com/alex137/BestPractice` directly;
    no second `add_repo` is needed. In each such session:
    `python3 tools/precedent_vendor_engine.py refresh <bestpractice-clone>`,
    then `python3 tools/precedent_migrate_status.py --repo . --against ..`,
    then `python3 tools/build_codeowners.py`, committed.
    **What the refresh now carries, named rather than left to "it'll pick it
    up" (2026-09-06):** [tools/doc_lint.py](../tools/doc_lint.py)'s check 6 gained
    two fixes each source's own vendored copy is currently without — a
    `decisions/` directory is record-class, and a link to a dated decision
    record is an allowed reference in a deliverable. Any set that keeps
    decision records under dated names is failing its own light check on them
    until it refreshes. Nothing else is required of the sets: the change is in
    the vendored engine, not in anything they author.
    Unblocks `convert-team-set-retired-statuses`,
    `build-codeowners-check-flag`'s
    rollout, [`unreachable-practices`](todo-2026-09-06-unreachable-practices.md)'s
    measurement, and configuring the leak gate's vocabulary blocklist (which
    belongs in `precedent-individual`).

    **THE BLOCKER AS WRITTEN IS FALSE, 2026-09-07 — and it is the premise
    four other items are waiting on.** This item says a session holding
    `alex137/*` cannot attach a `themorgan/*` repo. The session running the
    very deep check that day held, simultaneously:
    `alex137/bestpractice`, `themorgan/precedent-individual`,
    `themorgan/precedent-team-repo-maintenance`, `themorgan/precedent-team-tms`,
    `the project's own prior notes repository` and one further private `themorgan/*`
    consumer repo — and
    `add_repo` accepted the last of those *during* that session, with all
    three private sets already attached and worked in. Mixed owners in one
    session is exactly what this item and
    [AGENTS.md](../AGENTS.md)'s gotcha say cannot happen.

    **What is NOT established**, stated so the correction does not overreach:
    whether a *fresh* session rooted at `alex137/BestPractice` can add a
    `themorgan/*` repo as its first cross-owner add. That specific call was
    not made. The constraint may have been lifted, or may only bind the first
    add — this session cannot tell which, because it did not start empty. So
    the four items above are **not** blocked on what this item says blocks
    them, and someone should re-test the fresh-session case rather than
    assume either answer.

    Its earlier evidence stays, dated: on 2026-09-06 the refusal was real and
    was reproduced, so this is a change in the environment rather than a
    mistake in the original finding.

    **The fresh-session case was tested 2026-09-09, and it refuses.** A
    session rooted at `alex137/bestpractice` called `add_repo` for
    `themorgan/precedent-individual` as its **first tool call of the
    session** and was told *"cross-tier adds are not supported in v1:
    requested ... but session already has repos from owner(s) [alex137]"*.
    So the initial source itself counts as "already has repos", and no
    ordering of calls inside such a session can work. That closes the
    question this item left open; it does not explain the 2026-09-07 session
    that held five owners' repositories at once, which stays unexplained.

    **Third data point, 2026-09-13, and it is the LATE-session case nobody
    had measured.** A session rooted at `alex137/BestPractice`, hours into
    its life with dozens of pushes behind it, called `add_repo` for
    `themorgan/precedent-individual` with `access: "push"` and got the same
    refusal, word for word. A plain `git push --dry-run` into that clone had
    already been refused by the proxy itself — *"themorgan/precedent-individual
    is not in this session's authorized repository set, so the proxy will not
    inject a credential for it"*, HTTP 403 — which is a second, independent
    mechanism saying the same thing. So the refusal is not a first-call
    artifact and not an `add_repo` quirk: it holds at both ends of a session's
    life. It was not measured on purpose; the session hit it doing something
    else and is recording it here rather than letting the next one re-derive
    it (`findings-return-through-repo`).

    **And the item's premise — that a session must be rooted at the private
    repo — is now only one of two routes.** `add_repo` is not the only way to
    hold a credential: an environment can carry one, and the SessionStart
    hook can then clone the sources *before the agent's first turn*, which is
    the ordering every part of this problem turns on. Set
    `PRECEDENT_GIT_TOKEN` and `PRECEDENT_SOURCE_BASE_URL`
    ([PER_MACHINE_SETUP.md](../documentation/PER_MACHINE_SETUP.md)),
    and [tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py)
    `--teams-from .` clones every declared team set as a sibling. **Nobody
    has run it with a valid token yet** — three of the four things it depends
    on were measured that day (the proxy passes authenticated GitHub reads,
    no ambient credential exists, the helper really does hand git the token),
    and the fourth needs a token this account has not issued. Until somebody
    does, this item stays open on that one step, not on the whole design.
    [tools/precedent_source_credentials.py](../tools/precedent_source_credentials.py)
    reports which state a session is in.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: noted date is a floor, not exact -- this item predates anchor tracking (every anchor was retrofitted 2026-09-06) and its true creation date is unknown. Migrated from TODO.md by tools/todo_migrate.py.
