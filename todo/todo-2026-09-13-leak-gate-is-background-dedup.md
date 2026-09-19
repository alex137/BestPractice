---
slug:              todo-2026-09-13-leak-gate-is-background-dedup
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
noted:             2026-09-13
closed:            2026-09-13
---
## What

- <a id="leak-gate-is-background-dedup"></a>~~**Deduplicate
    `leak-gate-is-background` in the individual set, now that it is in force at
    universal.**~~ **Done 2026-09-13** — `themorgan/precedent-individual` pull
    request #94, merge commit `e3bb64e`. That set's copy now carries
    `status: deduplicated` and `in_force_at: leak-gate-is-background`, with the
    move written into its own `## Story`. It was step 2 of the 2026-09-13 move
    ([spec/MOVING_PRACTICES.md](../spec/MOVING_PRACTICES.md)); step 1 was
    [practices/leak-gate-is-background.md](../practices/leak-gate-is-background.md),
    landed here in pull request #269. The session that did it reported back
    rather than committing here, because it could not reach this repository at
    all — `add_repo` refuses the cross-owner add in both directions.

    **The two things this item told it to decide, and what it decided.**

    - **The check script stays in that set, with `checked_by:` still naming
      it.** Not on its own judgment: on this repository's own `## Install`
      section for the practice, which says a universal rule may not require the
      quiet directive of anyone, and names a per-set check keyed to that set's
      own blocklist as the right home for the mechanism half. What that script
      catches is a directive being tidied out of a long file, and nothing else
      in that tree would notice it going.
    - **The link to that set's `my-identity-is-not-private` stays in the
      surviving stub.** The universal text had to drop it
      ([practice-links-travel](../practices/practice-links-travel.md) — a relative
      link into a private set dies in every adopting repo), so the relation it
      carries is asserted nowhere here: that one is about what may go on a
      list, this one about who is allowed to bring the list up. In that set the
      target is an active sibling, so the link both resolves and travels.

    **The premise this item handed over was backwards, and following it is
    exactly what would have broken the check.** Kept rather than tidied away,
    the same way
    [TODO.md's `leak-gate-is-background-level` item](todo-2026-09-12-leak-gate-is-background-level.md)
    keeps the two readings it was decided against: a
    premise that was wrong in an instructive way is worth more kept than
    deleted. What it said was to check what a `deduplicated` status does to a
    practice's own `checked_by`, on the grounds that *"a check keyed to a
    practice no longer in force is the silent-skip shape
    [very-deep-check](../practices/very-deep-check.md)'s pass 2 asks about."* Two
    measurements answered it, taken against that set's vendored snapshot of
    [tools/precedent_check.py](../tools/precedent_check.py) and re-read here
    against this repository's own copy, which reads the same way:

    - **`deduplicated` does not disarm a check.** `run()` skips a
      practice-backed check only when `_practice_file(slug)` returns nothing,
      and `_practice_file()` tests that the file exists and nothing else. A
      deduplicated practice keeps its file, so the check goes on running and
      goes on failing the run. Confirmed by planting a violation in that set's
      blocklist with the practice file already at `status: deduplicated`:
      `VIOLATION leak-gate-is-background`, exit 1, the practice's own `## Rule`
      printed as the failure message.
    - **The silent skip is real, and comes from the opposite edit.**
      `register_materialized_checks()` takes a script's slug from whichever
      practice's `checked_by` names it, falling back to the filename stem. With
      `checked_by: null` the same planted violation registered under the slug
      `check_leak_gate_is_background`, found no practice file of that name, and
      was reported SKIPPED — a green run, exit 0, with the violation sitting
      untouched in the file.

    **No disposition line, because the item is no longer open.** What it leaves
    behind is a question this repository owns rather than that set, filed as
    [TODO.md's `check-gate-reads-status` item](todo-2026-09-13-check-gate-reads-status.md)
    below.

## How It Closes

Already closed 2026-09-13 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
