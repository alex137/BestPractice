---
slug:              todo-2026-09-11-source-clone-keeps-no-credential
kind:              analysis
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-11
closed:            2026-09-11
---
## What

- <a id="source-clone-keeps-no-credential"></a>~~**A private source clone carries no credential helper, so every later
    fetch of it fails — and the freshness guard blocks on that.**~~
    **Done (2026-09-11).**
    [tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py)
    passes the credential as `git -c credential.helper=...` flags on the
    clone invocation, which is exactly right for keeping the token out of
    `.git/config`. But nothing configures the clone for later use, so a
    plain `git fetch origin main` inside it fails with *"could not read
    Username for 'https://github.com'"* even with `PRECEDENT_GIT_TOKEN`
    set.

    Measured 2026-09-11, in a container with all four private sources
    cloned and the token present: `PRECEDENT_FRESHNESS_ALSO` names those
    sources, the freshness guard's `pre-write` mode fetches each one, the
    fetch fails, and `_pre_write_one` blocks — **refusing every non-`git`
    tool call of the session**, repeatedly, since the sentinel is only
    written after the checks pass. The block message names the source's
    base branch (`could not fetch origin/main`) while the project dir is on
    `precedent-beta-v01`, which reads as a problem with the project's own
    checkout and is not.

    The workaround is one `git config credential.helper` per clone, with
    the same secret-free shell snippet
    [tools/precedent_source_credentials.py](../tools/precedent_source_credentials.py)
    already builds — set by hand in this container to get the session
    moving. The fix is for the bootstrap to write that helper into each
    clone's local config at clone time, so it survives the session that
    made it.

    **Fixed the same day, on Morgan's go-ahead.**
    `persist_credential_helper` in
    [tools/precedent_source_credentials.py](../tools/precedent_source_credentials.py)
    writes the same secret-free snippet into a clone's own local config,
    and [tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py)
    calls it after **every** successful sync — not only a fresh clone, so
    it is also the repair path for the clones already on disk. Proved
    against this container's real individual source rather than a fixture:
    the helper cleared by hand, `ensure_source` run, and a plain
    `git fetch origin main` with no `-c` flags then succeeded where it had
    failed an hour earlier. `verify_harness.py`'s
    `check_source_clone_keeps_its_credential` holds it, with two negative
    controls that were run rather than assumed.

## How It Closes

Already closed 2026-09-11 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
