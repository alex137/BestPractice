---
slug:              todo-2026-07-19-two-published-commits-carry-the-wrong-timezone-offset-and-pr
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "a decision about which layer carries it, since the hook demonstrably cannot. The engine-refresh commit's missing `Session:` trailer is a separate, smaller thing and is **blocked on nothing** — the trailer belongs in [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py), which writ"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-07-19
closed:            null
---
## What

- **Two published commits carry the wrong timezone offset, and
  `precedent_refresh_sources.py --commit` writes a commit with no session
  trailer.** Both found 2026-09-07 by the
  [very deep check](../spec/VERY_DEEP_CHECK.md) after refreshing every source's
  vendored engine, and both are this-session-caused rather than latent.
  `themorgan/precedent-individual` commits `7e62667` and `3bbfead` carry
  `+0000` where that set's `identity.json` declares `-0300`. They are already
  on `main`, so
  [no-rewrite-for-warnings](../practices/no-rewrite-for-warnings.md) says fix
  forward rather than rewrite. The set's own mechanism for this is
  `check_buenos_aires_dates.py`'s grandfathering list, and its sibling
  `commit-author` practice is explicit that entries went in **on Morgan's
  explicit instruction** — so a session adding itself to that list would be
  deciding something the practice reserves to a person.
  The underlying cause is the same one filed above: the hook that exports
  `TZ` and sets the commit identity never runs in a repo that is not the
  session's primary, so both the identity and the timezone halves fail
  together and silently.
  Separately, the engine-refresh commit that
  [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)
  writes with `--commit` has no `Session:` trailer, which the maintainers'
  team set requires of every commit. Rewritten by hand this time; the tool
  will produce the same commit next time, so the trailer belongs in the tool.
  **The grandfathering is done** — approved by Morgan 2026-09-07, both SHAs
  exempted in `check_buenos_aires_dates.py` with the reason inline; that set
  is now 10 passed / 0 violated and 9 of 9 of its own tests. What remains is
  the cause, not the symptom, and it is the same one filed above: a hook
  cannot reach a repo that is not the session's primary, so the identity and
  timezone halves of that mechanism fail together and silently in any
  cross-repo session. **Blocked on:** a decision about which layer carries
  it, since the hook demonstrably cannot.
  The engine-refresh commit's missing `Session:` trailer is a separate,
  smaller thing and is **blocked on nothing** — the trailer belongs in
  [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py),
  which writes that commit.

## How It Closes

Not open until: a decision about which layer carries it, since the hook demonstrably cannot. The engine-refresh commit's missing `Session:` trailer is a separate, smaller thing and is **blocked on nothing** — the trailer belongs in [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py), which writ

## Notes

2026-09-16: noted date is a floor, not exact -- this item predates anchor tracking (every anchor was retrofitted 2026-09-06) and its true creation date is unknown. Migrated from TODO.md by tools/todo_migrate.py.
