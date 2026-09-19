---
slug:              todo-2026-09-11-freshness-also-names-the-old-set-name
kind:              verify
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

- <a id="freshness-also-names-the-old-set-name"></a>**`PRECEDENT_FRESHNESS_ALSO` still names the set by its old name, and it
  lives in the environment rather than in any repository.** Measured
  2026-09-11 on this container:
  `~/precedent-individual=main;/home/user/precedent-team-maintainers=main;/home/user/precedent-team-working-style=main;/home/user/precedent-team-writing=main`.
  After the rename the second entry resolves to nothing — and
  [AGENTS.md](../AGENTS.md)'s own gotcha records that **a dead entry is skipped
  silently by design**, so the variable goes on reading as coverage while
  covering one repository less. Nothing else reports it except
  [tools/precedent_session_check.py](../tools/precedent_session_check.py)'s own
  row.

  Two corrections in one edit, and the second is the older bug: the path
  should also be written `~/precedent-team-repo-maintenance`, not spelled
  out, because `$HOME` is `/root` on some containers and `/home/user` on
  others — the same reason that entry was wrong for days in 2026-09. Three of
  the four entries still carry the absolute form.

  **Morgan says he fixed it, 2026-09-11, and this session cannot confirm
  that — which is not a doubt about him, it is a property of the
  mechanism.** An environment change never reaches a session already
  running, so `env` here still prints the old value and will until this
  container ends. That reading is not evidence either way.
  **Confirm on the next fresh container** with
  `python3 tools/precedent_session_check.py`, whose own row answers it in
  one line. Closed on his word, with the verification named rather than
  assumed.

  **CONFIRMED 2026-09-11, on a fresh container**, by that row: `OK
  PRECEDENT_FRESHNESS_ALSO names repositories that exist`. The reasoning
  matters as much as the row, because a passing row can also mean the check
  found nothing to check: that session had **resolved its private sources**,
  so all four sets were on disk under their current names — a variable still
  naming `/home/user/precedent-team-maintainers` would have failed, since
  nothing is at that path any more. So the row is evidence, not an absence.

  Two `??` rows in the same run, both benign and worth knowing so nobody
  reads them as failures: **branch drift** was a first run with no earlier
  baseline to compare against, and **session root** cannot be answered from a
  tool shell at all — `CLAUDE_PROJECT_DIR` is usually unset there, which
  proves nothing either way, and is exactly why the effect checks above it
  exist ([AGENTS.md](../AGENTS.md)'s "do not diagnose this from `env`").

  **The same run is the first evidence in this repository of a session
  starting fully wired** — `.precedent/SESSION_PRACTICES.md` written, private
  sources resolved, commits authored by a person, global backstop installed,
  gate packages present, every branch visible, not behind the base. Every
  session working on this repository earlier that day had some half of that
  off and had to repair it by hand.

  **One trap if anyone pastes that row's suggested value.** It is computed
  from what is on disk in the container it runs in, so on a container where
  a team set was never cloned it simply drops that set from the value it
  proposes — this session's own run proposed a value naming
  `precedent-individual` twice and omitting `precedent-team-writing` and
  `precedent-team-working-style` entirely, because neither was on disk here.
  Read it as "these entries resolve to nothing", never as "here is your
  variable".

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
