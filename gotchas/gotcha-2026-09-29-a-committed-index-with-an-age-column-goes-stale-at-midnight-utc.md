---
slug:            gotcha-2026-09-29-a-committed-index-with-an-age-column-goes-stale-at-midnight-utc
status:          live
noted:           2026-09-29
severity:        minor
retired:         null
retires_when:    null
---
## Symptom

The deep check's isolated harness run fails with `enforced channel fires ...
an unplanted copy of this tree passes every check; generated-files-registered:
the same tree unplanted does not`, on a branch that never touched `todo/`.
Run in an empty environment, `precedent_check.py --only
generated-files-registered` says `todo/TODO.md: is out of date with a fresh
regeneration`, while the same check is green in the session.

## Story

On 2026-09-29, a little after 22:00 in Buenos Aires, a push check on an
unrelated engine change spent 16 minutes and then refused. The harness's
`--as-ci --isolated` run works in a clean clone under `TZ=UTC`, and in UTC it
was already the 30th. [tools/build_todo_index.py](../tools/build_todo_index.py)
writes an Age column (days since each item was noted) and a Due Reminders
section, both relative to today, so every Age cell came out one day greater
than the committed file and `--check` called it drift. The session's own run
resolved the person's zone and was still on the 29th, so nothing was wrong
there. The same file would have gone red for everyone at the next midnight
anyway: any committed file holding a value relative to today is out of date
once a day, whatever the zone.

## Fix

[todo/TODO.md](https://github.com/alex137/BestPractice/blob/staging/todo/TODO.md) now records `as_of:` in its frontmatter, the date its ages
were computed on, and `--check` rebuilds against that date. The check tests
that the file matches its items, not that somebody regenerated it since
midnight. A new generated file with a today-relative value needs the same
treatment. Test: `check_todo_index_check_survives_midnight` in
[tools/verify_harness.py](https://github.com/alex137/BestPractice/blob/staging/tools/verify_harness.py).
