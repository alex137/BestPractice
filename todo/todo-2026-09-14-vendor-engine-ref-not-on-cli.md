---
slug:              todo-2026-09-14-vendor-engine-ref-not-on-cli
kind:              decision
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "\"but do we want to install that specific version we told it? Why not install the most recent version?\" -- Morgan settled that a rollout takes the tip, not a pinned ref."
decision_strength: decided
waiting_on:        null
noted:             2026-09-14
closed:            2026-09-14
---
## What

- <a id="vendor-engine-ref-not-on-cli"></a>**Expose
    [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)'s
    `ref` parameter on the command line.** `refresh` fetches
    `origin <SOURCE_BRANCH>` and then resolves `origin/<SOURCE_BRANCH>`, so it
    always vendors whatever the branch tip is at that moment. The function
    already accepts a `ref` naming an exact commit — `seed()` passes the
    calling checkout's own HEAD — but no CLI flag reaches it, so from the
    command line there is no way to vendor a commit that has been reviewed
    once the branch has moved past it.
    Found 2026-09-14 during the four-set engine refresh: that session was
    asked to pin `e7442211c826`, tried twice (checking the commit out, then
    forcing the local branch), and the tool's own fetch overwrote both
    attempts. It landed on the live tip and said so rather than falsifying a
    remote-tracking ref, which was the right call.
    **Blocked-on: not the code — `ref` exists and works.** What is undecided
    is whether vendoring a commit the branch has moved past should be offered
    at all, given that a set pinned to an ancestor is stale the moment it
    lands. Decide that before adding the flag.

    **Closed 2026-09-14 — the flag already exists, and this item's premise was
    wrong.** It is spelled `--from-ref`, it is on `refresh`, and it landed
    2026-09-08 in commit `00d124b` — six days BEFORE this item was written.
    The tool's own module docstring documents it in the usage block
    (`refresh <bestpractice-clone> [--force] [--from-ref REF]`), and `main()`
    resolves the ref inside the clone and fails loudly if it does not resolve,
    so a typo cannot silently fall back to the tip.
    Measured, not read: a copy of a real practice set was refreshed with
    `--from-ref 0a45c9f` against this checkout, and its
    `tools/ENGINE_MANIFEST.json` moved from `03f4e1e03350` to `0a45c9fa1cdf`
    — an ancestor the branch had already moved past, which is exactly the
    capability this item says is missing.
    **Root cause of the wrong item:** it was written from the function
    signature (`refresh(clone, force=False, ref=None)`) rather than from
    `main()` or the docstring directly above it, and so concluded no CLI path
    existed without looking for one. That is
    [search-by-purpose](../practices/search-by-purpose.md)'s exact case — search
    by mechanism before concluding nothing exists — and it cost the four-set
    rollout three extra passes, because the session that needed the flag tried
    to pin a commit by checking it out and by forcing the local branch instead.
    The undecided question the item ends on — whether vendoring a commit the
    branch has moved past should be offered at all — does have an answer, and
    it is not the one this closure first gave. Shipping `--from-ref` settled
    *can you*, not *should a rollout*. Morgan settled that half the same day,
    reading the runbook sentence this closure had just produced: *"but do we
    want to install that specific version we told it? Why not install the most
    recent version?"* **Strength:** decided (2026-09-14, Morgan).
    So: a rollout takes the tip every time, and where repos land a commit
    apart the laggard is rolled forward rather than the leaders held back —
    pinning all of them to the older commit would have made all four miss the
    reply-gate change and removed the difference that made anyone look.
    `--from-ref` stays for the two cases where the exact commit is the point:
    a commit whose diff was actually reviewed, and reproducing against an
    older engine. [vendor-update-runbook](../practices/vendor-update-runbook.md)
    step 3 carried the wrong version of this for one commit — `9e5088d`, in
    [#336](https://github.com/alex137/BestPractice/pull/336) — and was
    corrected the same day.

## How It Closes

Already closed 2026-09-14 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
