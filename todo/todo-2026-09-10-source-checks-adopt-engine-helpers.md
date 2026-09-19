---
slug:              todo-2026-09-10-source-checks-adopt-engine-helpers
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
noted:             2026-09-10
closed:            2026-09-10
---
## What

- <a id="source-checks-adopt-engine-helpers"></a>**Move the two private
  practice sets' checks onto the engine helpers added 2026-09-10.** Three
  source-supplied checks were found broken by a real §0 install into a
  fresh private repository, and each one's cause was the same shape: a
  check re-deriving from private assumptions something the engine can
  answer correctly for every install model. The engine halves are done and
  covered here; the check halves live in repositories this repo cannot
  edit.

  - `check_no_stale_counts.py` (`precedent-team-writing`) excludes a
    vendored mirror via its own `_mirrored_prefixes()`, which reads
    `process/manifest.json` — §1's bookkeeping, and INSTALL.md §0 step 5
    says to skip it. In a §0 install the exclusion evaporates and the run
    reports Precedent's own historical prose as stale ("states 34
    practices, but practices currently holds 121"), none of it actionable.
    Replace that helper with
    [`precedent_resolve.mirrored_prefixes()`](../tools/precedent_resolve.py),
    which reads `precedent.json`'s declared source paths as well and is
    authoritative in exactly the repos the manifest is missing from. The
    downstream workaround — a `process/manifest.json` carrying only an
    `upstream` block, written purely to feed the old signal — comes out
    with it.
  - `check_commit_author.py` and `check_buenos_aires_dates.py`
    (`precedent-individual`) both compute from an `identity.json` at the
    CONSUMING repo's root and report a VIOLATION when it is absent — while
    `check_commit_author.py`'s own 2026-09-07 comment says a shared
    consuming repo must not have one. Both are therefore permanently red
    in any shared repo, with the fix forbidden by the same file that
    demands it. Replace the root read with
    [`precedent_resolve.declared_identity()`](../tools/precedent_resolve.py)
    and turn its `NoDeclaredIdentity` into `raise NotApplicable`: a
    violation should mean "a commit here has the wrong author", not "this
    repository is shared".

  **Also worth doing in the same pass:** audit the rest of both sets'
  `tools/checks/` for the same §1-only assumption. `no-stale-counts` was
  found because it fired, not because anything looked for it, and nothing
  in either set distinguishes "reads a §1 path" from "reads a path".

  **DONE 2026-09-10.** Three sessions, one rooted in each private set (the
  cross-tier refusal is per OWNER, so a session rooted in a `themorgan`
  repo reaches its siblings; one rooted here never will). Open pull
  requests carry the work, each awaiting an approver's yes per that set's
  own `approvers.json` — none was merged, correctly: `precedent-individual`
  #60, `precedent-team-writing` #4, `precedent-team-repo-maintenance` #36,
  `precedent-team-tms` #16, `precedent-team-working-style` #4.

  **The audit widened past what this item asked**, and was worth it. It
  was scoped to the two sets holding known-broken checks; it ran across
  all five, and found eight more instances in sets nobody had suspected —
  the item's own reasoning ("found because it fired, not because anything
  looked for it") applied to itself.

## How It Closes

Already closed 2026-09-10: three sessions, one rooted in each affected
private set, did the engine-helper adoption and opened a pull request in
each. Nothing further was ever asked of a session rooted here — merging
each PR is that repository's own approvers' call, not a condition on this
item.

## Notes

2026-09-19: this item was never carried into the 2026-09-16 `todo/`
migration (`9a08363b`) — it existed in [`TODO.md`](../TODO.md) as item 51
immediately before that commit, already marked `DONE 2026-09-10`, and the
migration's own step 2
([`spec/OPEN_ITEM_AND_GOTCHA_PLAN.md`](../spec/OPEN_ITEM_AND_GOTCHA_PLAN.md)
Part 4.1) says a done item "become[s] a `status: done` file", not that it
is dropped. It had no row in
[`spec/TODO_GOTCHA_MIGRATION_MAP.md`](../spec/TODO_GOTCHA_MIGRATION_MAP.md)
and no file under `todo/` or in [`todo/CLOSED.md`](CLOSED.md) either —
confirmed by searching both before writing this file. Recreated here from
the pre-migration text (`git show 9a08363b^:TODO.md`), unchanged except for
repointing its two in-repo links from relative
([`tools/precedent_resolve.py`](../tools/precedent_resolve.py)) to the
`../tools/...` shape this directory needs.

Found while tracing a stale link: `precedent-team-writing`'s own `TODO.md`
(its item 4, `todo-gotcha-stale-reference-exempted`) cites this item by its
old `TODO.md#source-checks-adopt-engine-helpers` anchor and says the anchor
"is gone from BestPractice's current `todo/` tree and its own
`spec/TODO_GOTCHA_MIGRATION_MAP.md`, and nothing found here confidently
says where it went" — this file and the migration-map row added alongside
it are that trace, so a session in `precedent-team-writing` can now repoint
its link and clear that exemption.

Not verified from this session: the current state of the five pull
requests listed above (`precedent-individual` #60, `precedent-team-writing`
#4, `precedent-team-repo-maintenance` #36, `precedent-team-tms` #16,
`precedent-team-working-style` #4). They were open and unmerged as of
2026-09-10; whether any has since merged, closed, or gone stale is a
question for a session rooted in each of those repos, not this one.
